"""Integration tests for PostgresEntityTypeRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager
from dynamic_ontology.adapters.persistence.postgresql.entity_type_repository import (
    PostgresEntityTypeRepository,
)
from dynamic_ontology.domain.exceptions import ValidationError
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType


@pytest.fixture
def sample_entity_type() -> EntityType:
    """Create a sample entity type for testing."""
    return EntityType(
        id=uuid4(),
        name=f"TestEntityType_{uuid4().hex[:8]}",
        description="A test entity type",
        properties={
            "title": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=True,
                max_length=255,
            ),
            "count": PropertyDefinition(
                type=PropertyType.INTEGER,
                required=False,
                indexed=False,
                min_value=0,
                max_value=1000,
            ),
        },
        custom_validators=["validate_title_format"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
async def cleanup_entity_types(db_manager: DatabaseSessionManager):
    """Cleanup entity types after test."""
    created_ids: list[str] = []
    yield created_ids
    # Cleanup after test
    async with db_manager.session() as session:
        for entity_type_id in created_ids:
            await session.execute(
                text("DELETE FROM do_entity_types WHERE id = :id"),
                {"id": entity_type_id},
            )


@pytest.mark.asyncio
async def test_create_entity_type(
    db_manager: DatabaseSessionManager,
    sample_entity_type: EntityType,
    cleanup_entity_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test creating an entity type in the database."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        result = await repo.create(sample_entity_type)
        cleanup_entity_types.append(str(result.id))

        assert result.id == sample_entity_type.id
        assert result.name == sample_entity_type.name
        assert result.description == sample_entity_type.description
        assert len(result.properties) == 2
        assert "title" in result.properties
        assert result.properties["title"].type == PropertyType.STRING
        assert result.properties["title"].required is True
        assert result.custom_validators == ["validate_title_format"]


@pytest.mark.asyncio
async def test_get_entity_type_by_id(
    db_manager: DatabaseSessionManager,
    sample_entity_type: EntityType,
    cleanup_entity_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test retrieving an entity type by ID."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        # Create first
        created = await repo.create(sample_entity_type)
        cleanup_entity_types.append(str(created.id))

    # Retrieve in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        result = await repo.get_by_id(str(sample_entity_type.id))

        assert result is not None
        assert result.id == sample_entity_type.id
        assert result.name == sample_entity_type.name
        assert result.description == sample_entity_type.description
        assert len(result.properties) == 2


@pytest.mark.asyncio
async def test_get_entity_type_by_name(
    db_manager: DatabaseSessionManager,
    sample_entity_type: EntityType,
    cleanup_entity_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test retrieving an entity type by name."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        # Create first
        created = await repo.create(sample_entity_type)
        cleanup_entity_types.append(str(created.id))

    # Retrieve in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        result = await repo.get_by_name(sample_entity_type.name)

        assert result is not None
        assert result.id == sample_entity_type.id
        assert result.name == sample_entity_type.name


@pytest.mark.asyncio
async def test_get_entity_type_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test retrieving a non-existent entity type returns None."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        # Try to get non-existent entity type by ID
        result_by_id = await repo.get_by_id(str(uuid4()))
        assert result_by_id is None

        # Try to get non-existent entity type by name
        result_by_name = await repo.get_by_name("NonExistentType")
        assert result_by_name is None


@pytest.mark.asyncio
async def test_list_all_entity_types(
    db_manager: DatabaseSessionManager,
    cleanup_entity_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test listing all entity types."""
    # Create multiple entity types
    entity_types = [
        EntityType(
            id=uuid4(),
            name=f"ListTestType_{i}_{uuid4().hex[:8]}",
            description=f"Test entity type {i}",
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
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        for et in entity_types:
            created = await repo.create(et)
            cleanup_entity_types.append(str(created.id))

    # List all in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        result = await repo.list_all()

        # Should contain at least the 3 we created
        created_ids = {str(et.id) for et in entity_types}
        result_ids = {str(et.id) for et in result}

        assert created_ids.issubset(result_ids)


@pytest.mark.asyncio
async def test_update_entity_type(
    db_manager: DatabaseSessionManager,
    sample_entity_type: EntityType,
    cleanup_entity_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test updating an entity type."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        # Create first
        created = await repo.create(sample_entity_type)
        cleanup_entity_types.append(str(created.id))

    # Update in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        # Modify the entity type
        updated_entity_type = EntityType(
            id=sample_entity_type.id,
            name=sample_entity_type.name,
            description="Updated description",
            properties={
                "title": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                    indexed=True,
                    max_length=500,  # Changed from 255
                ),
                "count": PropertyDefinition(
                    type=PropertyType.INTEGER,
                    required=False,
                    indexed=False,
                    min_value=0,
                    max_value=2000,  # Changed from 1000
                ),
                "active": PropertyDefinition(  # New property
                    type=PropertyType.BOOLEAN,
                    required=False,
                    indexed=False,
                    default=True,
                ),
            },
            custom_validators=["validate_title_format", "validate_count_range"],
            created_at=sample_entity_type.created_at,
            updated_at=datetime.now(UTC),
        )

        result = await repo.update(updated_entity_type)

        assert result.id == sample_entity_type.id
        assert result.description == "Updated description"
        assert len(result.properties) == 3
        assert "active" in result.properties
        assert result.properties["title"].max_length == 500
        assert len(result.custom_validators) == 2


@pytest.mark.asyncio
async def test_delete_entity_type(
    db_manager: DatabaseSessionManager,
    sample_entity_type: EntityType,
    test_namespace_id: str,
) -> None:
    """Test deleting an entity type."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        # Create first
        await repo.create(sample_entity_type)

    # Delete in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        result = await repo.delete(str(sample_entity_type.id))

        assert result is True

    # Verify deletion in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        result = await repo.get_by_id(str(sample_entity_type.id))

        assert result is None


@pytest.mark.asyncio
async def test_delete_entity_type_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test deleting a non-existent entity type returns False."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        result = await repo.delete(str(uuid4()))

        assert result is False


@pytest.mark.asyncio
async def test_create_entity_type_duplicate_name_raises_validation_error(
    db_manager: DatabaseSessionManager,
    sample_entity_type: EntityType,
    cleanup_entity_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test that creating an EntityType with a duplicate name raises ValidationError."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        # Create the first entity type
        created = await repo.create(sample_entity_type)
        cleanup_entity_types.append(str(created.id))

    # Try to create another entity type with the same name in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        duplicate_entity_type = EntityType(
            id=uuid4(),
            name=sample_entity_type.name,  # Same name as the first one
            description="A duplicate entity type",
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
            await repo.create(duplicate_entity_type)

        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "name"
        assert "already exists" in exc_info.value.errors[0]["message"]


@pytest.mark.asyncio
async def test_update_entity_type_duplicate_name_raises_validation_error(
    db_manager: DatabaseSessionManager,
    cleanup_entity_types: list[str],
    test_namespace_id: str,
) -> None:
    """Test that updating an EntityType to a duplicate name raises ValidationError."""
    # Create two entity types with different names
    first_entity_type = EntityType(
        id=uuid4(),
        name=f"FirstEntityType_{uuid4().hex[:8]}",
        description="First entity type",
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

    second_entity_type = EntityType(
        id=uuid4(),
        name=f"SecondEntityType_{uuid4().hex[:8]}",
        description="Second entity type",
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
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        # Create both entity types
        created_first = await repo.create(first_entity_type)
        cleanup_entity_types.append(str(created_first.id))

        created_second = await repo.create(second_entity_type)
        cleanup_entity_types.append(str(created_second.id))

    # Try to update the second one to have the first one's name
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)

        updated_entity_type = EntityType(
            id=second_entity_type.id,
            name=first_entity_type.name,  # Duplicate name
            description="Updated description",
            properties={
                "field": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                    indexed=False,
                ),
            },
            custom_validators=[],
            created_at=second_entity_type.created_at,
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(ValidationError) as exc_info:
            await repo.update(updated_entity_type)

        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "name"
        assert "already exists" in exc_info.value.errors[0]["message"]
