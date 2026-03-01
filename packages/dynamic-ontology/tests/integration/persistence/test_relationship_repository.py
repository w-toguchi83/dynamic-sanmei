"""Integration tests for PostgresRelationshipRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager
from dynamic_ontology.adapters.persistence.postgresql.entity_repository import (
    PostgresEntityRepository,
)
from dynamic_ontology.adapters.persistence.postgresql.entity_type_repository import (
    PostgresEntityTypeRepository,
)
from dynamic_ontology.adapters.persistence.postgresql.relationship_repository import (
    PostgresRelationshipRepository,
)
from dynamic_ontology.adapters.persistence.postgresql.relationship_type_repository import (
    PostgresRelationshipTypeRepository,
)
from dynamic_ontology.domain.exceptions import VersionConflictError
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.relationship import Relationship, RelationshipType


@pytest.fixture
def sample_entity_type() -> EntityType:
    """Create a sample entity type for testing."""
    return EntityType(
        id=uuid4(),
        name=f"RelRepoTestType_{uuid4().hex[:8]}",
        description="A test entity type for relationship repository tests",
        properties={
            "name": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=True,
                max_length=255,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_relationship_type() -> RelationshipType:
    """Create a sample relationship type for testing."""
    return RelationshipType(
        id=uuid4(),
        name=f"RelRepoTestRelType_{uuid4().hex[:8]}",
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
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
async def persisted_entity_type(
    db_manager: DatabaseSessionManager,
    sample_entity_type: EntityType,
    test_namespace_id: str,
) -> EntityType:
    """Create and persist a sample entity type."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        return await repo.create(sample_entity_type)


@pytest.fixture
async def persisted_relationship_type(
    db_manager: DatabaseSessionManager,
    sample_relationship_type: RelationshipType,
    test_namespace_id: str,
) -> RelationshipType:
    """Create and persist a sample relationship type."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        return await repo.create(sample_relationship_type)


@pytest.fixture
async def persisted_entities(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    test_namespace_id: str,
) -> tuple[Entity, Entity]:
    """Create and persist two entities for relationship testing."""
    entity1 = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"name": "Entity A"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    entity2 = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"name": "Entity B"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        created1 = await repo.create(entity1)
        created2 = await repo.create(entity2)
        return (created1, created2)


@pytest.fixture
async def cleanup_test_data(db_manager: DatabaseSessionManager):
    """Cleanup relationships, entities, entity types, and relationship types after test."""
    data: dict[str, list[str]] = {
        "relationships": [],
        "entities": [],
        "entity_types": [],
        "relationship_types": [],
    }
    yield data
    # Cleanup after test
    async with db_manager.session() as session:
        # Delete relationships first
        for rel_id in data["relationships"]:
            # First delete history records
            await session.execute(
                text("DELETE FROM do_relationship_history WHERE relationship_id = :id"),
                {"id": rel_id},
            )
            # Then delete the relationship
            await session.execute(
                text("DELETE FROM do_relationships WHERE id = :id"),
                {"id": rel_id},
            )
        # Delete entities
        for entity_id in data["entities"]:
            # First delete history records
            await session.execute(
                text("DELETE FROM do_entity_history WHERE entity_id = :id"),
                {"id": entity_id},
            )
            # Then delete the entity
            await session.execute(
                text("DELETE FROM do_entities WHERE id = :id"),
                {"id": entity_id},
            )
        # Delete entity types
        for entity_type_id in data["entity_types"]:
            await session.execute(
                text("DELETE FROM do_entity_types WHERE id = :id"),
                {"id": entity_type_id},
            )
        # Delete relationship types
        for rel_type_id in data["relationship_types"]:
            await session.execute(
                text("DELETE FROM do_relationship_types WHERE id = :id"),
                {"id": rel_type_id},
            )


@pytest.mark.asyncio
async def test_create_relationship(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test creating a relationship in the database."""
    entity1, entity2 = persisted_entities

    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.75},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        result = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(result.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

        assert result.id == relationship.id
        assert result.type_id == persisted_relationship_type.id
        assert result.from_entity_id == entity1.id
        assert result.to_entity_id == entity2.id
        assert result.version == 1
        assert result.properties == {"weight": 0.75}


@pytest.mark.asyncio
async def test_get_relationship_by_id(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test retrieving a relationship by ID."""
    entity1, entity2 = persisted_entities

    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.5},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(created.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # Retrieve in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        result = await repo.get_by_id(str(relationship.id))

        assert result is not None
        assert result.id == relationship.id
        assert result.type_id == persisted_relationship_type.id
        assert result.from_entity_id == entity1.id
        assert result.to_entity_id == entity2.id
        assert result.properties["weight"] == 0.5


@pytest.mark.asyncio
async def test_get_relationship_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test retrieving a non-existent relationship returns None."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        result = await repo.get_by_id(str(uuid4()))
        assert result is None


@pytest.mark.asyncio
async def test_list_relationships_by_entity_outgoing(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test listing relationships by entity (outgoing direction)."""
    entity1, entity2 = persisted_entities

    # Create a relationship from entity1 to entity2
    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.3},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(created.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # List outgoing relationships from entity1
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        result, total = await repo.list_by_entity(str(entity1.id), direction="outgoing")

        assert len(result) == 1
        assert result[0].id == relationship.id
        assert result[0].from_entity_id == entity1.id

        # Entity2 should have no outgoing relationships
        result2, total2 = await repo.list_by_entity(str(entity2.id), direction="outgoing")
        assert len(result2) == 0


@pytest.mark.asyncio
async def test_list_relationships_by_entity_incoming(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test listing relationships by entity (incoming direction)."""
    entity1, entity2 = persisted_entities

    # Create a relationship from entity1 to entity2
    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.4},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(created.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # List incoming relationships to entity2
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        result, total = await repo.list_by_entity(str(entity2.id), direction="incoming")

        assert len(result) == 1
        assert result[0].id == relationship.id
        assert result[0].to_entity_id == entity2.id

        # Entity1 should have no incoming relationships
        result2, total2 = await repo.list_by_entity(str(entity1.id), direction="incoming")
        assert len(result2) == 0


@pytest.mark.asyncio
async def test_list_relationships_by_entity_both(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test listing relationships by entity (both directions)."""
    entity1, entity2 = persisted_entities

    # Create a third entity
    entity3 = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"name": "Entity C"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        entity_repo = PostgresEntityRepository(session, test_namespace_id)
        created_entity3 = await entity_repo.create(entity3)
        cleanup_test_data["entities"].append(str(created_entity3.id))

    # Create relationship from entity1 to entity2
    relationship1 = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.5},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # Create relationship from entity3 to entity1
    relationship2 = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity3.id,
        to_entity_id=entity1.id,
        version=1,
        properties={"weight": 0.6},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created1 = await repo.create(relationship1)
        created2 = await repo.create(relationship2)

        cleanup_test_data["relationships"].extend([str(created1.id), str(created2.id)])
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # List both directions for entity1 (should return both relationships)
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        result, total = await repo.list_by_entity(str(entity1.id), direction="both")

        assert len(result) == 2
        result_ids = {r.id for r in result}
        assert relationship1.id in result_ids
        assert relationship2.id in result_ids


@pytest.mark.asyncio
async def test_list_relationships_by_entity_with_type_filter(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test listing relationships by entity with relationship_type filter."""
    entity1, entity2 = persisted_entities

    # Create another relationship type
    other_rel_type = RelationshipType(
        id=uuid4(),
        name=f"OtherRelType_{uuid4().hex[:8]}",
        description="Another relationship type",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        rel_type_repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        created_other_type = await rel_type_repo.create(other_rel_type)
        cleanup_test_data["relationship_types"].append(str(created_other_type.id))

    # Create relationships with different types
    relationship1 = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.5},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    relationship2 = Relationship(
        id=uuid4(),
        type_id=other_rel_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created1 = await repo.create(relationship1)
        created2 = await repo.create(relationship2)

        cleanup_test_data["relationships"].extend([str(created1.id), str(created2.id)])
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # Filter by specific relationship type
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        result, total = await repo.list_by_entity(
            str(entity1.id),
            relationship_type=str(persisted_relationship_type.id),
            direction="both",
        )

        assert len(result) == 1
        assert result[0].id == relationship1.id
        assert result[0].type_id == persisted_relationship_type.id


@pytest.mark.asyncio
async def test_update_relationship_with_version(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test updating a relationship increments version."""
    entity1, entity2 = persisted_entities

    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.1},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(created.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # Update in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)

        updated_relationship = Relationship(
            id=relationship.id,
            type_id=relationship.type_id,
            from_entity_id=relationship.from_entity_id,
            to_entity_id=relationship.to_entity_id,
            version=1,
            properties={"weight": 0.9},
            created_at=relationship.created_at,
            updated_at=datetime.now(UTC),
        )

        result = await repo.update(updated_relationship, current_version=1)

        assert result.id == relationship.id
        assert result.version == 2
        assert result.properties["weight"] == 0.9


@pytest.mark.asyncio
async def test_update_relationship_version_conflict(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test that updating with wrong version raises VersionConflictError."""
    entity1, entity2 = persisted_entities

    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.2},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(created.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # Try to update with wrong version
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)

        updated_relationship = Relationship(
            id=relationship.id,
            type_id=relationship.type_id,
            from_entity_id=relationship.from_entity_id,
            to_entity_id=relationship.to_entity_id,
            version=99,  # Wrong version
            properties={"weight": 0.8},
            created_at=relationship.created_at,
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(VersionConflictError) as exc_info:
            await repo.update(updated_relationship, current_version=99)

        assert exc_info.value.entity_id == str(relationship.id)
        assert exc_info.value.current_version == 1
        assert exc_info.value.provided_version == 99


@pytest.mark.asyncio
async def test_delete_relationship(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test deleting a relationship."""
    entity1, entity2 = persisted_entities

    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.6},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        await repo.create(relationship)

        # Add for cleanup in case deletion fails
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # Delete in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        deleted = await repo.delete(str(relationship.id))
        assert deleted is True

    # Verify deletion
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        found = await repo.get_by_id(str(relationship.id))
        assert found is None


@pytest.mark.asyncio
async def test_delete_relationship_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test deleting a non-existent relationship returns False."""
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        result = await repo.delete(str(uuid4()))
        assert result is False


@pytest.mark.asyncio
async def test_relationship_history_on_create(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test that creating a relationship records history."""
    entity1, entity2 = persisted_entities

    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.7},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(created.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # Check history in a new session
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        history = await repo.get_history(str(relationship.id))

        assert len(history) == 1
        assert history[0]["relationship_id"] == str(relationship.id)
        assert history[0]["version"] == 1
        assert history[0]["operation"] == "CREATE"
        assert history[0]["properties"]["weight"] == 0.7
        assert history[0]["valid_to"] is None


@pytest.mark.asyncio
async def test_relationship_history_on_update(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test that updating a relationship records history."""
    entity1, entity2 = persisted_entities

    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.1},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(created.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # Update the relationship
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)

        updated_relationship = Relationship(
            id=relationship.id,
            type_id=relationship.type_id,
            from_entity_id=relationship.from_entity_id,
            to_entity_id=relationship.to_entity_id,
            version=1,
            properties={"weight": 0.99},
            created_at=relationship.created_at,
            updated_at=datetime.now(UTC),
        )
        await repo.update(updated_relationship, current_version=1)

    # Check history
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        history = await repo.get_history(str(relationship.id))

        assert len(history) == 2

        # Sort by version to ensure order
        history_sorted = sorted(history, key=lambda h: h["version"])

        # First record (CREATE) should have valid_to set
        assert history_sorted[0]["version"] == 1
        assert history_sorted[0]["operation"] == "CREATE"
        assert history_sorted[0]["valid_to"] is not None

        # Second record (UPDATE) should have no valid_to
        assert history_sorted[1]["version"] == 2
        assert history_sorted[1]["operation"] == "UPDATE"
        assert history_sorted[1]["valid_to"] is None
        assert history_sorted[1]["properties"]["weight"] == 0.99


@pytest.mark.asyncio
async def test_get_relationship_at_time(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    persisted_relationship_type: RelationshipType,
    persisted_entities: tuple[Entity, Entity],
    cleanup_test_data: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test time-travel query to get relationship at a specific point in time."""
    import asyncio

    entity1, entity2 = persisted_entities

    relationship = Relationship(
        id=uuid4(),
        type_id=persisted_relationship_type.id,
        from_entity_id=entity1.id,
        to_entity_id=entity2.id,
        version=1,
        properties={"weight": 0.25},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        created = await repo.create(relationship)

        cleanup_test_data["relationships"].append(str(created.id))
        cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
        cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
        cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

    # Record time after create
    time_after_create = datetime.now(UTC)

    # Small delay to ensure time difference
    await asyncio.sleep(0.1)

    # Update the relationship
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)

        updated_relationship = Relationship(
            id=relationship.id,
            type_id=relationship.type_id,
            from_entity_id=relationship.from_entity_id,
            to_entity_id=relationship.to_entity_id,
            version=1,
            properties={"weight": 0.85},
            created_at=relationship.created_at,
            updated_at=datetime.now(UTC),
        )
        await repo.update(updated_relationship, current_version=1)

    # Query at time before update - should get original
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)

        # Get relationship at time after create (should return v1)
        result = await repo.get_by_id(str(relationship.id), at_time=time_after_create.isoformat())

        assert result is not None
        assert result.version == 1
        assert result.properties["weight"] == 0.25

    # Get current relationship (no time specified) - should get updated version
    async with db_manager.session() as session:
        repo = PostgresRelationshipRepository(session, test_namespace_id)
        current = await repo.get_by_id(str(relationship.id))

        assert current is not None
        assert current.version == 2
        assert current.properties["weight"] == 0.85


class TestChangedByTracking:
    """Tests for changed_by field tracking through repository operations."""

    @pytest.mark.asyncio
    async def test_create_stores_changed_by(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        persisted_relationship_type: RelationshipType,
        persisted_entities: tuple[Entity, Entity],
        cleanup_test_data: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Test that create persists changed_by and records it in history."""
        entity1, entity2 = persisted_entities

        relationship = Relationship(
            id=uuid4(),
            type_id=persisted_relationship_type.id,
            from_entity_id=entity1.id,
            to_entity_id=entity2.id,
            version=1,
            properties={"weight": 0.5},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            changed_by="test-user-create",
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            created = await repo.create(relationship)

            cleanup_test_data["relationships"].append(str(created.id))
            cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
            cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
            cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

            assert created.changed_by == "test-user-create"

        # Verify changed_by appears in history
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            history = await repo.get_history(str(relationship.id))

            assert len(history) == 1
            assert history[0]["changed_by"] == "test-user-create"
            assert history[0]["operation"] == "CREATE"

    @pytest.mark.asyncio
    async def test_update_stores_changed_by(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        persisted_relationship_type: RelationshipType,
        persisted_entities: tuple[Entity, Entity],
        cleanup_test_data: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Test that update persists changed_by and records it in history."""
        entity1, entity2 = persisted_entities

        relationship = Relationship(
            id=uuid4(),
            type_id=persisted_relationship_type.id,
            from_entity_id=entity1.id,
            to_entity_id=entity2.id,
            version=1,
            properties={"weight": 0.3},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            changed_by="creator-user",
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            created = await repo.create(relationship)

            cleanup_test_data["relationships"].append(str(created.id))
            cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
            cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
            cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

        # Update with a different changed_by
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)

            updated_relationship = Relationship(
                id=relationship.id,
                type_id=relationship.type_id,
                from_entity_id=relationship.from_entity_id,
                to_entity_id=relationship.to_entity_id,
                version=1,
                properties={"weight": 0.8},
                created_at=relationship.created_at,
                updated_at=datetime.now(UTC),
                changed_by="updater-user",
            )

            result = await repo.update(updated_relationship, current_version=1)
            assert result.changed_by == "updater-user"

        # Verify history records have correct changed_by values
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            history = await repo.get_history(str(relationship.id))

            assert len(history) == 2
            history_sorted = sorted(history, key=lambda h: h["version"])

            assert history_sorted[0]["changed_by"] == "creator-user"
            assert history_sorted[0]["operation"] == "CREATE"
            assert history_sorted[1]["changed_by"] == "updater-user"
            assert history_sorted[1]["operation"] == "UPDATE"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_changed_by(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        persisted_relationship_type: RelationshipType,
        persisted_entities: tuple[Entity, Entity],
        cleanup_test_data: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Test that get_by_id returns changed_by field."""
        entity1, entity2 = persisted_entities

        relationship = Relationship(
            id=uuid4(),
            type_id=persisted_relationship_type.id,
            from_entity_id=entity1.id,
            to_entity_id=entity2.id,
            version=1,
            properties={"weight": 0.6},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            changed_by="fetch-test-user",
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            created = await repo.create(relationship)

            cleanup_test_data["relationships"].append(str(created.id))
            cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
            cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
            cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

        # Fetch in a new session
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            fetched = await repo.get_by_id(str(relationship.id))

            assert fetched is not None
            assert fetched.changed_by == "fetch-test-user"


class TestExistsByPair:
    """Tests for exists_by_pair method."""

    @pytest.mark.asyncio
    async def test_exists_by_pair_returns_true_when_exists(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        persisted_relationship_type: RelationshipType,
        persisted_entities: tuple[Entity, Entity],
        cleanup_test_data: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Test that exists_by_pair returns True when a matching relationship exists."""
        entity1, entity2 = persisted_entities

        relationship = Relationship(
            id=uuid4(),
            type_id=persisted_relationship_type.id,
            from_entity_id=entity1.id,
            to_entity_id=entity2.id,
            version=1,
            properties={"weight": 0.5},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            created = await repo.create(relationship)

            cleanup_test_data["relationships"].append(str(created.id))
            cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
            cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
            cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.exists_by_pair(
                type_id=str(persisted_relationship_type.id),
                from_entity_id=str(entity1.id),
                to_entity_id=str(entity2.id),
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_exists_by_pair_returns_false_when_not_exists(
        self,
        db_manager: DatabaseSessionManager,
        test_namespace_id: str,
    ) -> None:
        """Test that exists_by_pair returns False when no matching relationship exists."""
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.exists_by_pair(
                type_id=str(uuid4()),
                from_entity_id=str(uuid4()),
                to_entity_id=str(uuid4()),
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_exists_by_pair_different_type_returns_false(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        persisted_relationship_type: RelationshipType,
        persisted_entities: tuple[Entity, Entity],
        cleanup_test_data: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Test that exists_by_pair returns False when same from/to but different type_id."""
        entity1, entity2 = persisted_entities

        relationship = Relationship(
            id=uuid4(),
            type_id=persisted_relationship_type.id,
            from_entity_id=entity1.id,
            to_entity_id=entity2.id,
            version=1,
            properties={"weight": 0.5},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            created = await repo.create(relationship)

            cleanup_test_data["relationships"].append(str(created.id))
            cleanup_test_data["entities"].extend([str(entity1.id), str(entity2.id)])
            cleanup_test_data["entity_types"].append(str(persisted_entity_type.id))
            cleanup_test_data["relationship_types"].append(str(persisted_relationship_type.id))

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.exists_by_pair(
                type_id=str(uuid4()),  # 異なるタイプID
                from_entity_id=str(entity1.id),
                to_entity_id=str(entity2.id),
            )

            assert result is False
