"""Integration tests for PostgresRelationshipTypeRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager
from dynamic_ontology.adapters.persistence.postgresql.relationship_type_repository import (
    PostgresRelationshipTypeRepository,
)
from dynamic_ontology.domain.exceptions import EntityNotFoundError, ValidationError
from dynamic_ontology.domain.models.entity_type import PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.relationship import RelationshipType


@pytest.fixture
def sample_relationship_type() -> RelationshipType:
    """Create a sample directional relationship type for testing."""
    return RelationshipType(
        id=uuid4(),
        name=f"TestRelType_{uuid4().hex[:8]}",
        description="A test relationship type",
        directional=True,
        properties={
            "weight": PropertyDefinition(
                type=PropertyType.FLOAT,
                required=False,
                indexed=True,
                min_value=0.0,
                max_value=1.0,
            ),
            "label": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=False,
                max_length=100,
            ),
        },
        custom_validators=["validate_weight_range"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_bidirectional_relationship_type() -> RelationshipType:
    """Create a sample bidirectional relationship type for testing."""
    return RelationshipType(
        id=uuid4(),
        name=f"TestBidirectionalRelType_{uuid4().hex[:8]}",
        description="A bidirectional relationship type",
        directional=False,
        properties={
            "strength": PropertyDefinition(
                type=PropertyType.INTEGER,
                required=True,
                indexed=True,
                min_value=1,
                max_value=10,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
async def cleanup_relationship_types(db_manager: DatabaseSessionManager):
    """Cleanup relationship types after test."""
    created_ids: list[str] = []
    yield created_ids
    # Cleanup after test
    async with db_manager.session() as session:
        for relationship_type_id in created_ids:
            await session.execute(
                text("DELETE FROM do_relationship_types WHERE id = :id"),
                {"id": relationship_type_id},
            )


@pytest.mark.asyncio
async def test_create_relationship_type(
    db_manager: DatabaseSessionManager,
    sample_relationship_type: RelationshipType,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test creating a relationship type in the database."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        result = await repo.create(sample_relationship_type)
        cleanup_relationship_types.append(str(result.id))

        assert result.id == sample_relationship_type.id
        assert result.name == sample_relationship_type.name
        assert result.description == sample_relationship_type.description
        assert result.directional is True
        assert len(result.properties) == 2
        assert "weight" in result.properties
        assert result.properties["weight"].type == PropertyType.FLOAT
        assert result.properties["label"].required is True
        assert result.custom_validators == ["validate_weight_range"]


@pytest.mark.asyncio
async def test_get_relationship_type_by_id(
    db_manager: DatabaseSessionManager,
    sample_relationship_type: RelationshipType,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test retrieving a relationship type by ID."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Create first
        created = await repo.create(sample_relationship_type)
        cleanup_relationship_types.append(str(created.id))

    # Retrieve in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        result = await repo.get_by_id(str(sample_relationship_type.id))

        assert result is not None
        assert result.id == sample_relationship_type.id
        assert result.name == sample_relationship_type.name
        assert result.description == sample_relationship_type.description
        assert result.directional is True
        assert len(result.properties) == 2


@pytest.mark.asyncio
async def test_get_relationship_type_by_name(
    db_manager: DatabaseSessionManager,
    sample_relationship_type: RelationshipType,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test retrieving a relationship type by name."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Create first
        created = await repo.create(sample_relationship_type)
        cleanup_relationship_types.append(str(created.id))

    # Retrieve in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        result = await repo.get_by_name(sample_relationship_type.name)

        assert result is not None
        assert result.id == sample_relationship_type.id
        assert result.name == sample_relationship_type.name


@pytest.mark.asyncio
async def test_get_relationship_type_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test retrieving a non-existent relationship type returns None."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Try to get non-existent relationship type by ID
        result_by_id = await repo.get_by_id(str(uuid4()))
        assert result_by_id is None

        # Try to get non-existent relationship type by name
        result_by_name = await repo.get_by_name("NonExistentRelType")
        assert result_by_name is None


@pytest.mark.asyncio
async def test_list_all_relationship_types(
    db_manager: DatabaseSessionManager,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test listing all relationship types."""
    # Create multiple relationship types
    relationship_types = [
        RelationshipType(
            id=uuid4(),
            name=f"ListTestRelType_{i}_{uuid4().hex[:8]}",
            description=f"Test relationship type {i}",
            directional=True,
            properties={
                "field": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                    indexed=False,
                ),
            },
            custom_validators=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(3)
    ]

    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        for rt in relationship_types:
            created = await repo.create(rt)
            cleanup_relationship_types.append(str(created.id))

    # List all in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        result = await repo.list_all()

        # Should contain at least the 3 we created
        created_ids = {str(rt.id) for rt in relationship_types}
        result_ids = {str(rt.id) for rt in result}

        assert created_ids.issubset(result_ids)


@pytest.mark.asyncio
async def test_update_relationship_type(
    db_manager: DatabaseSessionManager,
    sample_relationship_type: RelationshipType,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test updating a relationship type."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Create first
        created = await repo.create(sample_relationship_type)
        cleanup_relationship_types.append(str(created.id))

    # Update in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Modify the relationship type
        updated_relationship_type = RelationshipType(
            id=sample_relationship_type.id,
            name=sample_relationship_type.name,
            description="Updated description",
            directional=sample_relationship_type.directional,
            properties={
                "weight": PropertyDefinition(
                    type=PropertyType.FLOAT,
                    required=True,  # Changed from False
                    indexed=True,
                    min_value=0.0,
                    max_value=2.0,  # Changed from 1.0
                ),
                "label": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                    indexed=False,
                    max_length=200,  # Changed from 100
                ),
                "priority": PropertyDefinition(  # New property
                    type=PropertyType.INTEGER,
                    required=False,
                    indexed=True,
                    default=1,
                ),
            },
            custom_validators=["validate_weight_range", "validate_priority"],
            created_at=sample_relationship_type.created_at,
            updated_at=datetime.now(UTC),
        )

        result = await repo.update(updated_relationship_type)

        assert result.id == sample_relationship_type.id
        assert result.description == "Updated description"
        assert len(result.properties) == 3
        assert "priority" in result.properties
        assert result.properties["weight"].max_value == 2.0
        assert result.properties["weight"].required is True
        assert len(result.custom_validators) == 2


@pytest.mark.asyncio
async def test_delete_relationship_type(
    db_manager: DatabaseSessionManager,
    sample_relationship_type: RelationshipType,
    test_namespace_id: str,
) -> None:
    """Test deleting a relationship type."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Create first
        await repo.create(sample_relationship_type)

    # Delete in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        result = await repo.delete(str(sample_relationship_type.id))

        assert result is True

    # Verify deletion in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        result = await repo.get_by_id(str(sample_relationship_type.id))

        assert result is None


@pytest.mark.asyncio
async def test_delete_relationship_type_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test deleting a non-existent relationship type returns False."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        result = await repo.delete(str(uuid4()))

        assert result is False


@pytest.mark.asyncio
async def test_relationship_type_bidirectional(
    db_manager: DatabaseSessionManager,
    sample_bidirectional_relationship_type: RelationshipType,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test creating and retrieving a bidirectional relationship type (directional=False)."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Create the bidirectional relationship type
        result = await repo.create(sample_bidirectional_relationship_type)
        cleanup_relationship_types.append(str(result.id))

        assert result.id == sample_bidirectional_relationship_type.id
        assert result.name == sample_bidirectional_relationship_type.name
        assert result.directional is False
        assert "strength" in result.properties

    # Verify in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        retrieved = await repo.get_by_id(str(sample_bidirectional_relationship_type.id))

        assert retrieved is not None
        assert retrieved.directional is False


@pytest.mark.asyncio
async def test_create_duplicate_name_raises_validation_error(
    db_manager: DatabaseSessionManager,
    sample_relationship_type: RelationshipType,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test that creating a RelationshipType with a duplicate name raises ValidationError."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Create the first relationship type
        created = await repo.create(sample_relationship_type)
        cleanup_relationship_types.append(str(created.id))

    # Try to create another relationship type with the same name in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        duplicate_relationship_type = RelationshipType(
            id=uuid4(),
            name=sample_relationship_type.name,  # Same name as the first one
            description="A duplicate relationship type",
            directional=True,
            properties={
                "field": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                    indexed=False,
                ),
            },
            custom_validators=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValidationError) as exc_info:
            await repo.create(duplicate_relationship_type)

        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "name"
        assert "already exists" in exc_info.value.errors[0]["message"]


@pytest.mark.asyncio
async def test_update_relationship_type_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test updating a non-existent relationship type raises EntityNotFoundError."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        non_existent_relationship_type = RelationshipType(
            id=uuid4(),
            name=f"NonExistent_{uuid4().hex[:8]}",
            description="Non-existent relationship type",
            directional=True,
            properties={
                "field": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                    indexed=False,
                ),
            },
            custom_validators=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(EntityNotFoundError) as exc_info:
            await repo.update(non_existent_relationship_type)

        assert str(non_existent_relationship_type.id) in str(exc_info.value)
        assert "RelationshipType" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_relationship_type_duplicate_name_raises_validation_error(
    db_manager: DatabaseSessionManager,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test that updating a RelationshipType to a duplicate name raises ValidationError."""
    # Create two relationship types with different names
    first_relationship_type = RelationshipType(
        id=uuid4(),
        name=f"FirstRelType_{uuid4().hex[:8]}",
        description="First relationship type",
        directional=True,
        properties={
            "field": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=False,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    second_relationship_type = RelationshipType(
        id=uuid4(),
        name=f"SecondRelType_{uuid4().hex[:8]}",
        description="Second relationship type",
        directional=True,
        properties={
            "field": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=False,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        # Create both relationship types
        created_first = await repo.create(first_relationship_type)
        cleanup_relationship_types.append(str(created_first.id))

        created_second = await repo.create(second_relationship_type)
        cleanup_relationship_types.append(str(created_second.id))

    # Try to update the second one to have the first one's name
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)

        updated_relationship_type = RelationshipType(
            id=second_relationship_type.id,
            name=first_relationship_type.name,  # Duplicate name
            description="Updated description",
            directional=True,
            properties={
                "field": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                    indexed=False,
                ),
            },
            custom_validators=[],
            created_at=second_relationship_type.created_at,
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValidationError) as exc_info:
            await repo.update(updated_relationship_type)

        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "name"
        assert "already exists" in exc_info.value.errors[0]["message"]


@pytest.mark.asyncio
async def test_create_relationship_type_with_allow_duplicates_false(
    db_manager: DatabaseSessionManager,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """allow_duplicates=False で作成し永続化される。"""
    rt = RelationshipType(
        id=uuid4(),
        name=f"no_dup_{uuid4().hex[:8]}",
        description="",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        allow_duplicates=False,
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        created = await repo.create(rt)
        cleanup_relationship_types.append(str(created.id))

        assert created.allow_duplicates is False

    # 新しいセッションで取得して永続化を確認
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        fetched = await repo.get_by_id(str(rt.id))

        assert fetched is not None
        assert fetched.allow_duplicates is False


@pytest.mark.asyncio
async def test_update_relationship_type_allow_duplicates(
    db_manager: DatabaseSessionManager,
    cleanup_relationship_types: list[str],
    test_namespace_id: str,
) -> None:
    """allow_duplicates を True → False に更新できる。"""
    from dataclasses import replace

    rt = RelationshipType(
        id=uuid4(),
        name=f"upd_dup_{uuid4().hex[:8]}",
        description="",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        allow_duplicates=True,
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        created = await repo.create(rt)
        cleanup_relationship_types.append(str(created.id))

        assert created.allow_duplicates is True

    # 新しいセッションで更新
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        updated = replace(created, allow_duplicates=False, updated_at=datetime.now(UTC))
        result = await repo.update(updated)

        assert result.allow_duplicates is False

    # 新しいセッションで永続化を確認
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        fetched = await repo.get_by_id(str(rt.id))

        assert fetched is not None
        assert fetched.allow_duplicates is False
