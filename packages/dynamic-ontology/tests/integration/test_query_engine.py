"""Integration tests for QueryEngine."""

import os
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
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.query import (
    AggregateConfig,
    FilterCondition,
    FilterOperator,
    Query,
    SortDirection,
    SortField,
    TraverseConfig,
    TraverseDirection,
)
from dynamic_ontology.domain.models.relationship import Relationship, RelationshipType
from dynamic_ontology.domain.services.query_engine import QueryEngine, QueryResult


@pytest.fixture
def database_url() -> str:
    """Get database URL from settings."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/dynamic_ontology_test",
    )


@pytest.fixture
async def db_manager(database_url: str):
    """Create and initialize database manager."""
    manager = DatabaseSessionManager()
    manager.init(database_url)
    yield manager
    await manager.close()


@pytest.fixture
def sample_entity_type() -> EntityType:
    """Create a sample entity type for testing."""
    return EntityType(
        id=uuid4(),
        name=f"QueryEngineTestType_{uuid4().hex[:8]}",
        description="A test entity type for query engine tests",
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
            "status": PropertyDefinition(
                type=PropertyType.STRING,
                required=False,
                indexed=True,
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
async def cleanup_resources(db_manager: DatabaseSessionManager):
    """Cleanup entities and entity types after test."""
    entity_ids: list[str] = []
    entity_type_ids: list[str] = []
    yield {"entities": entity_ids, "entity_types": entity_type_ids}

    # Cleanup after test - delete entities first (foreign key constraint)
    async with db_manager.session() as session:
        for entity_id in entity_ids:
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
        for entity_type_id in entity_type_ids:
            await session.execute(
                text("DELETE FROM do_entity_types WHERE id = :id"),
                {"id": entity_type_id},
            )


@pytest.mark.asyncio
async def test_simple_query(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test simple query without filters returns all entities of type."""
    # Create test entities
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": f"Test Entity {i}", "count": i * 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(3)
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))
        cleanup_resources["entity_types"].append(str(persisted_entity_type.id))

    # Execute simple query
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(entity_type=persisted_entity_type.name)
        result = await engine.execute(query)

        assert isinstance(result, QueryResult)
        assert result.total == 3
        assert len(result.items) == 3
        assert result.limit == 100
        assert result.offset == 0

        # Verify all items are Entity objects
        for item in result.items:
            assert isinstance(item, Entity)
            assert item.type_id == persisted_entity_type.id


@pytest.mark.asyncio
async def test_query_with_simple_filter(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test query with a simple equality filter."""
    # Create test entities with different statuses
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Active Item", "status": "active"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Inactive Item", "status": "inactive"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Another Active", "status": "active"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))
        cleanup_resources["entity_types"].append(str(persisted_entity_type.id))

    # Execute query with filter
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_entity_type.name,
            filter=FilterCondition(
                field="status",
                operator=FilterOperator.EQ,
                value="active",
            ),
        )
        result = await engine.execute(query)

        assert result.total == 2
        assert len(result.items) == 2

        # All results should have status="active"
        for item in result.items:
            assert item.properties.get("status") == "active"


@pytest.mark.asyncio
async def test_query_with_and_filter(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test query with AND filter conditions."""
    # Create test entities with combinations
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "High Active", "status": "active", "count": 100},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Low Active", "status": "active", "count": 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "High Inactive", "status": "inactive", "count": 100},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))
        cleanup_resources["entity_types"].append(str(persisted_entity_type.id))

    # Execute query with AND filter
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_entity_type.name,
            filter=FilterCondition(
                field="status",
                operator=FilterOperator.EQ,
                value="active",
                and_conditions=[
                    FilterCondition(
                        field="count",
                        operator=FilterOperator.GTE,
                        value=50,
                    ),
                ],
            ),
        )
        result = await engine.execute(query)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].properties["title"] == "High Active"
        assert result.items[0].properties["status"] == "active"
        assert result.items[0].properties["count"] == 100


@pytest.mark.asyncio
async def test_query_with_sort(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test query with sort ordering."""
    # Create test entities with different titles for sorting
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Charlie", "count": 30},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Alpha", "count": 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Bravo", "count": 20},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))
        cleanup_resources["entity_types"].append(str(persisted_entity_type.id))

    # Execute query with ascending sort by title
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_entity_type.name,
            sort=[SortField(field="title", direction=SortDirection.ASC)],
        )
        result = await engine.execute(query)

        assert result.total == 3
        assert len(result.items) == 3
        assert result.items[0].properties["title"] == "Alpha"
        assert result.items[1].properties["title"] == "Bravo"
        assert result.items[2].properties["title"] == "Charlie"

    # Execute query with descending sort by title
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_entity_type.name,
            sort=[SortField(field="title", direction=SortDirection.DESC)],
        )
        result = await engine.execute(query)

        assert result.total == 3
        assert len(result.items) == 3
        assert result.items[0].properties["title"] == "Charlie"
        assert result.items[1].properties["title"] == "Bravo"
        assert result.items[2].properties["title"] == "Alpha"


@pytest.mark.asyncio
async def test_query_with_pagination(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test query with pagination (limit and offset)."""
    # Create test entities
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": f"Item {i:03d}", "count": i},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(10)
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))
        cleanup_resources["entity_types"].append(str(persisted_entity_type.id))

    # Execute query with pagination - first page
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_entity_type.name,
            sort=[SortField(field="title", direction=SortDirection.ASC)],
            limit=3,
            offset=0,
        )
        result = await engine.execute(query)

        assert result.total == 10  # Total count ignores pagination
        assert len(result.items) == 3
        assert result.limit == 3
        assert result.offset == 0
        assert result.items[0].properties["title"] == "Item 000"
        assert result.items[2].properties["title"] == "Item 002"

    # Execute query with pagination - second page
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_entity_type.name,
            sort=[SortField(field="title", direction=SortDirection.ASC)],
            limit=3,
            offset=3,
        )
        result = await engine.execute(query)

        assert result.total == 10
        assert len(result.items) == 3
        assert result.limit == 3
        assert result.offset == 3
        assert result.items[0].properties["title"] == "Item 003"
        assert result.items[2].properties["title"] == "Item 005"

    # Execute query with pagination - partial last page
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_entity_type.name,
            sort=[SortField(field="title", direction=SortDirection.ASC)],
            limit=3,
            offset=9,
        )
        result = await engine.execute(query)

        assert result.total == 10
        assert len(result.items) == 1  # Only 1 item left
        assert result.limit == 3
        assert result.offset == 9
        assert result.items[0].properties["title"] == "Item 009"


@pytest.mark.asyncio
async def test_query_entity_type_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test query raises error for non-existent entity type."""
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(entity_type="NonExistentType")

        with pytest.raises(ValueError) as exc_info:
            await engine.execute(query)

        assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_query_with_contains_filter(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test query with CONTAINS filter for substring matching."""
    # Create test entities with different titles
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Important Document"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Regular File"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Another Important Item"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))
        cleanup_resources["entity_types"].append(str(persisted_entity_type.id))

    # Execute query with CONTAINS filter
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_entity_type.name,
            filter=FilterCondition(
                field="title",
                operator=FilterOperator.CONTAINS,
                value="Important",
            ),
        )
        result = await engine.execute(query)

        assert result.total == 2
        assert len(result.items) == 2

        # All results should contain "Important" in title
        for item in result.items:
            assert "Important" in item.properties["title"]


@pytest.mark.asyncio
async def test_query_empty_result(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test query returns empty result when no entities match."""
    cleanup_resources["entity_types"].append(str(persisted_entity_type.id))

    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(entity_type=persisted_entity_type.name)
        result = await engine.execute(query)

        assert result.total == 0
        assert len(result.items) == 0
        assert result.limit == 100
        assert result.offset == 0


# =============================================================================
# Graph Traversal Tests
# =============================================================================


@pytest.fixture
async def traversal_cleanup_resources(db_manager: DatabaseSessionManager):
    """Cleanup resources for traversal tests including relationships."""
    entity_ids: list[str] = []
    entity_type_ids: list[str] = []
    relationship_ids: list[str] = []
    relationship_type_ids: list[str] = []

    yield {
        "entities": entity_ids,
        "entity_types": entity_type_ids,
        "relationships": relationship_ids,
        "relationship_types": relationship_type_ids,
    }

    # Cleanup in correct order (relationships first due to foreign keys)
    async with db_manager.session() as session:
        for rel_id in relationship_ids:
            await session.execute(
                text("DELETE FROM do_relationship_history WHERE relationship_id = :id"),
                {"id": rel_id},
            )
            await session.execute(
                text("DELETE FROM do_relationships WHERE id = :id"),
                {"id": rel_id},
            )
        for entity_id in entity_ids:
            await session.execute(
                text("DELETE FROM do_entity_history WHERE entity_id = :id"),
                {"id": entity_id},
            )
            await session.execute(
                text("DELETE FROM do_entities WHERE id = :id"),
                {"id": entity_id},
            )
        for entity_type_id in entity_type_ids:
            await session.execute(
                text("DELETE FROM do_entity_types WHERE id = :id"),
                {"id": entity_type_id},
            )
        for rel_type_id in relationship_type_ids:
            await session.execute(
                text("DELETE FROM do_relationship_types WHERE id = :id"),
                {"id": rel_type_id},
            )


@pytest.fixture
def person_entity_type() -> EntityType:
    """Create Person entity type for traversal tests."""
    return EntityType(
        id=uuid4(),
        name=f"Person_{uuid4().hex[:8]}",
        description="A person entity type",
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
def task_entity_type() -> EntityType:
    """Create Task entity type for traversal tests."""
    return EntityType(
        id=uuid4(),
        name=f"Task_{uuid4().hex[:8]}",
        description="A task entity type",
        properties={
            "title": PropertyDefinition(
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
def assigned_to_relationship_type() -> RelationshipType:
    """Create assigned_to relationship type."""
    return RelationshipType(
        id=uuid4(),
        name=f"assigned_to_{uuid4().hex[:8]}",
        description="Task is assigned to a person",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_traverse_outgoing_relationships(
    db_manager: DatabaseSessionManager,
    person_entity_type: EntityType,
    task_entity_type: EntityType,
    assigned_to_relationship_type: RelationshipType,
    traversal_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test outgoing traversal from Task to Person via assigned_to."""
    # Create entity types
    async with db_manager.session() as session:
        entity_type_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_person_type = await entity_type_repo.create(person_entity_type)
        persisted_task_type = await entity_type_repo.create(task_entity_type)
        traversal_cleanup_resources["entity_types"].append(str(persisted_person_type.id))
        traversal_cleanup_resources["entity_types"].append(str(persisted_task_type.id))

    # Create relationship type
    async with db_manager.session() as session:
        rel_type_repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        persisted_rel_type = await rel_type_repo.create(assigned_to_relationship_type)
        traversal_cleanup_resources["relationship_types"].append(str(persisted_rel_type.id))

    # Create entities
    alice = Entity(
        id=uuid4(),
        type_id=persisted_person_type.id,
        version=1,
        properties={"name": "Alice"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    bob = Entity(
        id=uuid4(),
        type_id=persisted_person_type.id,
        version=1,
        properties={"name": "Bob"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    task1 = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Task 1"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    task2 = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Task 2"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        entity_repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in [alice, bob, task1, task2]:
            created = await entity_repo.create(entity)
            traversal_cleanup_resources["entities"].append(str(created.id))

    # Create relationships: Task1 -> Alice, Task2 -> Bob
    rel1 = Relationship(
        id=uuid4(),
        type_id=persisted_rel_type.id,
        from_entity_id=task1.id,
        to_entity_id=alice.id,
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    rel2 = Relationship(
        id=uuid4(),
        type_id=persisted_rel_type.id,
        from_entity_id=task2.id,
        to_entity_id=bob.id,
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        rel_repo = PostgresRelationshipRepository(session, test_namespace_id)
        for rel in [rel1, rel2]:
            created = await rel_repo.create(rel)
            traversal_cleanup_resources["relationships"].append(str(created.id))

    # Execute query with outgoing traversal from Task
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_task_type.name,
            traverse=TraverseConfig(
                relationship_type=persisted_rel_type.name,
                direction=TraverseDirection.OUTGOING,
                depth=1,
            ),
        )
        result = await engine.execute(query)

        assert result.total == 2
        assert len(result.items) == 2
        assert len(result.related_entities) == 2

        # Check that each task has one related person
        task1_related = result.related_entities.get(str(task1.id), [])
        task2_related = result.related_entities.get(str(task2.id), [])

        assert len(task1_related) == 1
        assert task1_related[0].properties["name"] == "Alice"

        assert len(task2_related) == 1
        assert task2_related[0].properties["name"] == "Bob"


@pytest.mark.asyncio
async def test_traverse_incoming_relationships(
    db_manager: DatabaseSessionManager,
    person_entity_type: EntityType,
    task_entity_type: EntityType,
    assigned_to_relationship_type: RelationshipType,
    traversal_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test incoming traversal from Person to Task via assigned_to."""
    # Create entity types
    async with db_manager.session() as session:
        entity_type_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_person_type = await entity_type_repo.create(person_entity_type)
        persisted_task_type = await entity_type_repo.create(task_entity_type)
        traversal_cleanup_resources["entity_types"].append(str(persisted_person_type.id))
        traversal_cleanup_resources["entity_types"].append(str(persisted_task_type.id))

    # Create relationship type
    async with db_manager.session() as session:
        rel_type_repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        persisted_rel_type = await rel_type_repo.create(assigned_to_relationship_type)
        traversal_cleanup_resources["relationship_types"].append(str(persisted_rel_type.id))

    # Create entities
    alice = Entity(
        id=uuid4(),
        type_id=persisted_person_type.id,
        version=1,
        properties={"name": "Alice"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    task1 = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Task 1"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    task2 = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Task 2"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        entity_repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in [alice, task1, task2]:
            created = await entity_repo.create(entity)
            traversal_cleanup_resources["entities"].append(str(created.id))

    # Create relationships: Task1 -> Alice, Task2 -> Alice
    rel1 = Relationship(
        id=uuid4(),
        type_id=persisted_rel_type.id,
        from_entity_id=task1.id,
        to_entity_id=alice.id,
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    rel2 = Relationship(
        id=uuid4(),
        type_id=persisted_rel_type.id,
        from_entity_id=task2.id,
        to_entity_id=alice.id,
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        rel_repo = PostgresRelationshipRepository(session, test_namespace_id)
        for rel in [rel1, rel2]:
            created = await rel_repo.create(rel)
            traversal_cleanup_resources["relationships"].append(str(created.id))

    # Execute query with incoming traversal from Person
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_person_type.name,
            traverse=TraverseConfig(
                relationship_type=persisted_rel_type.name,
                direction=TraverseDirection.INCOMING,
                depth=1,
            ),
        )
        result = await engine.execute(query)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].properties["name"] == "Alice"

        # Alice should have 2 related tasks (incoming)
        alice_related = result.related_entities.get(str(alice.id), [])
        assert len(alice_related) == 2

        related_titles = {e.properties["title"] for e in alice_related}
        assert related_titles == {"Task 1", "Task 2"}


@pytest.mark.asyncio
async def test_traverse_both_directions(
    db_manager: DatabaseSessionManager,
    person_entity_type: EntityType,
    task_entity_type: EntityType,
    assigned_to_relationship_type: RelationshipType,
    traversal_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test bidirectional traversal."""
    # Create entity types
    async with db_manager.session() as session:
        entity_type_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_person_type = await entity_type_repo.create(person_entity_type)
        persisted_task_type = await entity_type_repo.create(task_entity_type)
        traversal_cleanup_resources["entity_types"].append(str(persisted_person_type.id))
        traversal_cleanup_resources["entity_types"].append(str(persisted_task_type.id))

    # Create a generic "relates_to" relationship type
    relates_to_type = RelationshipType(
        id=uuid4(),
        name=f"relates_to_{uuid4().hex[:8]}",
        description="Generic relationship",
        directional=False,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        rel_type_repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        persisted_rel_type = await rel_type_repo.create(relates_to_type)
        traversal_cleanup_resources["relationship_types"].append(str(persisted_rel_type.id))

    # Create entities: TaskA <-> TaskB <-> TaskC
    task_a = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Task A"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    task_b = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Task B"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    task_c = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Task C"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        entity_repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in [task_a, task_b, task_c]:
            created = await entity_repo.create(entity)
            traversal_cleanup_resources["entities"].append(str(created.id))

    # Create relationships: A -> B, C -> B (B is connected to both A and C)
    rel1 = Relationship(
        id=uuid4(),
        type_id=persisted_rel_type.id,
        from_entity_id=task_a.id,
        to_entity_id=task_b.id,
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    rel2 = Relationship(
        id=uuid4(),
        type_id=persisted_rel_type.id,
        from_entity_id=task_c.id,
        to_entity_id=task_b.id,
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        rel_repo = PostgresRelationshipRepository(session, test_namespace_id)
        for rel in [rel1, rel2]:
            created = await rel_repo.create(rel)
            traversal_cleanup_resources["relationships"].append(str(created.id))

    # Execute query with BOTH direction traversal from B
    # Filter to get only Task B, then traverse both directions
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_task_type.name,
            filter=FilterCondition(
                field="title",
                operator=FilterOperator.EQ,
                value="Task B",
            ),
            traverse=TraverseConfig(
                relationship_type=persisted_rel_type.name,
                direction=TraverseDirection.BOTH,
                depth=1,
            ),
        )
        result = await engine.execute(query)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].properties["title"] == "Task B"

        # B should be connected to both A (incoming) and C (incoming)
        b_related = result.related_entities.get(str(task_b.id), [])
        assert len(b_related) == 2

        related_titles = {e.properties["title"] for e in b_related}
        assert related_titles == {"Task A", "Task C"}


@pytest.mark.asyncio
async def test_traverse_depth_limiting(
    db_manager: DatabaseSessionManager,
    task_entity_type: EntityType,
    traversal_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test that depth limiting works correctly in traversal."""
    # Create entity type
    async with db_manager.session() as session:
        entity_type_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_task_type = await entity_type_repo.create(task_entity_type)
        traversal_cleanup_resources["entity_types"].append(str(persisted_task_type.id))

    # Create relationship type
    depends_on_type = RelationshipType(
        id=uuid4(),
        name=f"depends_on_{uuid4().hex[:8]}",
        description="Task dependency",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        rel_type_repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        persisted_rel_type = await rel_type_repo.create(depends_on_type)
        traversal_cleanup_resources["relationship_types"].append(str(persisted_rel_type.id))

    # Create a chain: Task1 -> Task2 -> Task3 -> Task4
    tasks = [
        Entity(
            id=uuid4(),
            type_id=persisted_task_type.id,
            version=1,
            properties={"title": f"Task {i}"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(1, 5)
    ]

    async with db_manager.session() as session:
        entity_repo = PostgresEntityRepository(session, test_namespace_id)
        for task in tasks:
            created = await entity_repo.create(task)
            traversal_cleanup_resources["entities"].append(str(created.id))

    # Create chain relationships
    relationships = []
    for i in range(len(tasks) - 1):
        rel = Relationship(
            id=uuid4(),
            type_id=persisted_rel_type.id,
            from_entity_id=tasks[i].id,
            to_entity_id=tasks[i + 1].id,
            version=1,
            properties={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        relationships.append(rel)

    async with db_manager.session() as session:
        rel_repo = PostgresRelationshipRepository(session, test_namespace_id)
        for rel in relationships:
            created = await rel_repo.create(rel)
            traversal_cleanup_resources["relationships"].append(str(created.id))

    # Test depth=1: Task1 should only reach Task2
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_task_type.name,
            filter=FilterCondition(
                field="title",
                operator=FilterOperator.EQ,
                value="Task 1",
            ),
            traverse=TraverseConfig(
                relationship_type=persisted_rel_type.name,
                direction=TraverseDirection.OUTGOING,
                depth=1,
            ),
        )
        result = await engine.execute(query)

        assert result.total == 1
        task1_related = result.related_entities.get(str(tasks[0].id), [])
        assert len(task1_related) == 1
        assert task1_related[0].properties["title"] == "Task 2"

    # Test depth=2: Task1 should reach Task2 and Task3
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_task_type.name,
            filter=FilterCondition(
                field="title",
                operator=FilterOperator.EQ,
                value="Task 1",
            ),
            traverse=TraverseConfig(
                relationship_type=persisted_rel_type.name,
                direction=TraverseDirection.OUTGOING,
                depth=2,
            ),
        )
        result = await engine.execute(query)

        task1_related = result.related_entities.get(str(tasks[0].id), [])
        assert len(task1_related) == 2
        related_titles = {e.properties["title"] for e in task1_related}
        assert related_titles == {"Task 2", "Task 3"}

    # Test depth=3: Task1 should reach Task2, Task3, and Task4
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_task_type.name,
            filter=FilterCondition(
                field="title",
                operator=FilterOperator.EQ,
                value="Task 1",
            ),
            traverse=TraverseConfig(
                relationship_type=persisted_rel_type.name,
                direction=TraverseDirection.OUTGOING,
                depth=3,
            ),
        )
        result = await engine.execute(query)

        task1_related = result.related_entities.get(str(tasks[0].id), [])
        assert len(task1_related) == 3
        related_titles = {e.properties["title"] for e in task1_related}
        assert related_titles == {"Task 2", "Task 3", "Task 4"}


@pytest.mark.asyncio
async def test_traverse_cycle_detection(
    db_manager: DatabaseSessionManager,
    task_entity_type: EntityType,
    traversal_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test that cycle detection prevents infinite loops."""
    # Create entity type
    async with db_manager.session() as session:
        entity_type_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_task_type = await entity_type_repo.create(task_entity_type)
        traversal_cleanup_resources["entity_types"].append(str(persisted_task_type.id))

    # Create relationship type
    links_to_type = RelationshipType(
        id=uuid4(),
        name=f"links_to_{uuid4().hex[:8]}",
        description="Task link",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        rel_type_repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        persisted_rel_type = await rel_type_repo.create(links_to_type)
        traversal_cleanup_resources["relationship_types"].append(str(persisted_rel_type.id))

    # Create a cycle: Task1 -> Task2 -> Task3 -> Task1
    tasks = [
        Entity(
            id=uuid4(),
            type_id=persisted_task_type.id,
            version=1,
            properties={"title": f"Task {i}"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(1, 4)
    ]

    async with db_manager.session() as session:
        entity_repo = PostgresEntityRepository(session, test_namespace_id)
        for task in tasks:
            created = await entity_repo.create(task)
            traversal_cleanup_resources["entities"].append(str(created.id))

    # Create cycle relationships: 1->2, 2->3, 3->1
    relationships = [
        Relationship(
            id=uuid4(),
            type_id=persisted_rel_type.id,
            from_entity_id=tasks[0].id,
            to_entity_id=tasks[1].id,
            version=1,
            properties={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Relationship(
            id=uuid4(),
            type_id=persisted_rel_type.id,
            from_entity_id=tasks[1].id,
            to_entity_id=tasks[2].id,
            version=1,
            properties={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Relationship(
            id=uuid4(),
            type_id=persisted_rel_type.id,
            from_entity_id=tasks[2].id,
            to_entity_id=tasks[0].id,
            version=1,
            properties={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    async with db_manager.session() as session:
        rel_repo = PostgresRelationshipRepository(session, test_namespace_id)
        for rel in relationships:
            created = await rel_repo.create(rel)
            traversal_cleanup_resources["relationships"].append(str(created.id))

    # Traverse with depth=5 (more than cycle length)
    # Should not hang and should visit each node only once
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_task_type.name,
            filter=FilterCondition(
                field="title",
                operator=FilterOperator.EQ,
                value="Task 1",
            ),
            traverse=TraverseConfig(
                relationship_type=persisted_rel_type.name,
                direction=TraverseDirection.OUTGOING,
                depth=5,
            ),
        )
        result = await engine.execute(query)

        # Task1 is the starting point, should find Task2 and Task3
        # Should NOT re-visit Task1 (cycle detection)
        task1_related = result.related_entities.get(str(tasks[0].id), [])
        assert len(task1_related) == 2
        related_titles = {e.properties["title"] for e in task1_related}
        assert related_titles == {"Task 2", "Task 3"}


@pytest.mark.asyncio
async def test_traverse_no_relationships(
    db_manager: DatabaseSessionManager,
    task_entity_type: EntityType,
    traversal_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test traversal when entities have no relationships."""
    # Create entity type
    async with db_manager.session() as session:
        entity_type_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_task_type = await entity_type_repo.create(task_entity_type)
        traversal_cleanup_resources["entity_types"].append(str(persisted_task_type.id))

    # Create relationship type
    depends_on_type = RelationshipType(
        id=uuid4(),
        name=f"depends_on_{uuid4().hex[:8]}",
        description="Task dependency",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        rel_type_repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        persisted_rel_type = await rel_type_repo.create(depends_on_type)
        traversal_cleanup_resources["relationship_types"].append(str(persisted_rel_type.id))

    # Create a single entity with no relationships
    task = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Lonely Task"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        entity_repo = PostgresEntityRepository(session, test_namespace_id)
        created = await entity_repo.create(task)
        traversal_cleanup_resources["entities"].append(str(created.id))

    # Traverse should return empty related entities
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_task_type.name,
            traverse=TraverseConfig(
                relationship_type=persisted_rel_type.name,
                direction=TraverseDirection.OUTGOING,
                depth=1,
            ),
        )
        result = await engine.execute(query)

        assert result.total == 1
        assert len(result.items) == 1
        task_related = result.related_entities.get(str(task.id), [])
        assert len(task_related) == 0


@pytest.mark.asyncio
async def test_traverse_relationship_type_not_found(
    db_manager: DatabaseSessionManager,
    task_entity_type: EntityType,
    traversal_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test traversal raises error when relationship type not found."""
    # Create entity type
    async with db_manager.session() as session:
        entity_type_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_task_type = await entity_type_repo.create(task_entity_type)
        traversal_cleanup_resources["entity_types"].append(str(persisted_task_type.id))

    # Create an entity
    task = Entity(
        id=uuid4(),
        type_id=persisted_task_type.id,
        version=1,
        properties={"title": "Test Task"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        entity_repo = PostgresEntityRepository(session, test_namespace_id)
        created = await entity_repo.create(task)
        traversal_cleanup_resources["entities"].append(str(created.id))

    # Try to traverse with non-existent relationship type
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_task_type.name,
            traverse=TraverseConfig(
                relationship_type="nonexistent_relationship",
                direction=TraverseDirection.OUTGOING,
                depth=1,
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            await engine.execute(query)

        assert "nonexistent_relationship" in str(exc_info.value)
        assert "not found" in str(exc_info.value)


# =============================================================================
# Aggregation Tests
# =============================================================================


@pytest.fixture
def aggregation_entity_type() -> EntityType:
    """Create entity type for aggregation tests with numeric properties."""
    return EntityType(
        id=uuid4(),
        name=f"AggTestType_{uuid4().hex[:8]}",
        description="Entity type for aggregation tests",
        properties={
            "title": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=True,
                max_length=255,
            ),
            "status": PropertyDefinition(
                type=PropertyType.STRING,
                required=False,
                indexed=True,
            ),
            "priority": PropertyDefinition(
                type=PropertyType.INTEGER,
                required=False,
                indexed=True,
            ),
            "score": PropertyDefinition(
                type=PropertyType.INTEGER,
                required=False,
                indexed=False,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
async def aggregation_cleanup_resources(db_manager: DatabaseSessionManager):
    """Cleanup resources for aggregation tests."""
    entity_ids: list[str] = []
    entity_type_ids: list[str] = []

    yield {"entities": entity_ids, "entity_types": entity_type_ids}

    # Cleanup after test
    async with db_manager.session() as session:
        for entity_id in entity_ids:
            await session.execute(
                text("DELETE FROM do_entity_history WHERE entity_id = :id"),
                {"id": entity_id},
            )
            await session.execute(
                text("DELETE FROM do_entities WHERE id = :id"),
                {"id": entity_id},
            )
        for entity_type_id in entity_type_ids:
            await session.execute(
                text("DELETE FROM do_entity_types WHERE id = :id"),
                {"id": entity_type_id},
            )


@pytest.mark.asyncio
async def test_aggregate_count(
    db_manager: DatabaseSessionManager,
    aggregation_entity_type: EntityType,
    aggregation_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test simple count aggregation."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(aggregation_entity_type)
        aggregation_cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": f"Item {i}", "status": "active", "score": i * 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(1, 5)  # 4 entities with scores 10, 20, 30, 40
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            aggregation_cleanup_resources["entities"].append(str(created.id))

    # Execute aggregation query
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            aggregate=AggregateConfig(count=True),
        )
        result = await engine.execute(query)

        assert result.items == []
        assert result.aggregations is not None
        assert result.aggregations["count"] == 4


@pytest.mark.asyncio
async def test_aggregate_count_with_filter(
    db_manager: DatabaseSessionManager,
    aggregation_entity_type: EntityType,
    aggregation_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test count aggregation with filter applied."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(aggregation_entity_type)
        aggregation_cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities with different statuses
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Active 1", "status": "active", "score": 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Active 2", "status": "active", "score": 20},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Closed 1", "status": "closed", "score": 30},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Closed 2", "status": "closed", "score": 40},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            aggregation_cleanup_resources["entities"].append(str(created.id))

    # Count only active entities
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            filter=FilterCondition(
                field="status",
                operator=FilterOperator.EQ,
                value="active",
            ),
            aggregate=AggregateConfig(count=True),
        )
        result = await engine.execute(query)

        assert result.items == []
        assert result.aggregations is not None
        assert result.aggregations["count"] == 2


@pytest.mark.asyncio
async def test_aggregate_sum(
    db_manager: DatabaseSessionManager,
    aggregation_entity_type: EntityType,
    aggregation_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test sum aggregation on numeric field."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(aggregation_entity_type)
        aggregation_cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities with scores: 1, 2, 3, 4 (sum = 10)
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": f"Item {i}", "status": "active", "score": i},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(1, 5)
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            aggregation_cleanup_resources["entities"].append(str(created.id))

    # Execute sum aggregation
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            aggregate=AggregateConfig(sum_field="score"),
        )
        result = await engine.execute(query)

        assert result.items == []
        assert result.aggregations is not None
        assert result.aggregations["sum"] == 10.0  # 1 + 2 + 3 + 4


@pytest.mark.asyncio
async def test_aggregate_avg(
    db_manager: DatabaseSessionManager,
    aggregation_entity_type: EntityType,
    aggregation_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test avg aggregation on numeric field."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(aggregation_entity_type)
        aggregation_cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities with scores: 10, 20, 30, 40 (avg = 25)
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": f"Item {i}", "status": "active", "score": i * 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(1, 5)
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            aggregation_cleanup_resources["entities"].append(str(created.id))

    # Execute avg aggregation
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            aggregate=AggregateConfig(avg_field="score"),
        )
        result = await engine.execute(query)

        assert result.items == []
        assert result.aggregations is not None
        assert result.aggregations["avg"] == 25.0  # (10 + 20 + 30 + 40) / 4


@pytest.mark.asyncio
async def test_aggregate_group_by(
    db_manager: DatabaseSessionManager,
    aggregation_entity_type: EntityType,
    aggregation_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test aggregation with GROUP BY clause."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(aggregation_entity_type)
        aggregation_cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities with different statuses
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Open 1", "status": "open", "score": 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Open 2", "status": "open", "score": 20},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Closed 1", "status": "closed", "score": 30},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Closed 2", "status": "closed", "score": 40},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            aggregation_cleanup_resources["entities"].append(str(created.id))

    # Execute group by aggregation
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            aggregate=AggregateConfig(
                count=True,
                group_by=["status"],
            ),
        )
        result = await engine.execute(query)

        assert result.items == []
        assert result.aggregations is not None
        assert "groups" in result.aggregations

        groups = result.aggregations["groups"]
        assert len(groups) == 2

        # Find groups by status (order by status field: closed, open)
        status_counts = {g["status"]: g["count"] for g in groups}
        assert status_counts["open"] == 2
        assert status_counts["closed"] == 2


@pytest.mark.asyncio
async def test_aggregate_group_by_with_sum(
    db_manager: DatabaseSessionManager,
    aggregation_entity_type: EntityType,
    aggregation_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test GROUP BY with sum aggregation."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(aggregation_entity_type)
        aggregation_cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities: open (10+20=30), closed (30+40=70)
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Open 1", "status": "open", "score": 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Open 2", "status": "open", "score": 20},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Closed 1", "status": "closed", "score": 30},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Closed 2", "status": "closed", "score": 40},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            aggregation_cleanup_resources["entities"].append(str(created.id))

    # Execute group by with sum aggregation
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            aggregate=AggregateConfig(
                sum_field="score",
                group_by=["status"],
            ),
        )
        result = await engine.execute(query)

        assert result.items == []
        assert result.aggregations is not None
        assert "groups" in result.aggregations

        groups = result.aggregations["groups"]
        assert len(groups) == 2

        # Verify sums by status
        status_sums = {g["status"]: g["sum"] for g in groups}
        assert status_sums["open"] == 30.0  # 10 + 20
        assert status_sums["closed"] == 70.0  # 30 + 40


@pytest.mark.asyncio
async def test_aggregate_min_max(
    db_manager: DatabaseSessionManager,
    aggregation_entity_type: EntityType,
    aggregation_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test min and max aggregation."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(aggregation_entity_type)
        aggregation_cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities with scores: 5, 15, 25, 35
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": f"Item {i}", "status": "active", "score": i * 10 + 5},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(4)  # scores: 5, 15, 25, 35
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            aggregation_cleanup_resources["entities"].append(str(created.id))

    # Execute min/max aggregation
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            aggregate=AggregateConfig(
                min_field="score",
                max_field="score",
            ),
        )
        result = await engine.execute(query)

        assert result.items == []
        assert result.aggregations is not None
        # min/max on text returns string representation
        assert result.aggregations["min"] == "15"  # alphabetically "15" < "25" < "35" < "5"
        assert result.aggregations["max"] == "5"  # alphabetically "5" is highest


@pytest.mark.asyncio
async def test_aggregate_multiple_operations(
    db_manager: DatabaseSessionManager,
    aggregation_entity_type: EntityType,
    aggregation_cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test multiple aggregation operations in a single query."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(aggregation_entity_type)
        aggregation_cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities with scores: 10, 20, 30, 40
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": f"Item {i}", "status": "active", "score": i * 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(1, 5)
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            aggregation_cleanup_resources["entities"].append(str(created.id))

    # Execute multiple aggregations
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            aggregate=AggregateConfig(
                count=True,
                sum_field="score",
                avg_field="score",
            ),
        )
        result = await engine.execute(query)

        assert result.items == []
        assert result.aggregations is not None
        assert result.aggregations["count"] == 4
        assert result.aggregations["sum"] == 100.0  # 10 + 20 + 30 + 40
        assert result.aggregations["avg"] == 25.0  # 100 / 4


# =============================================================================
# Time Travel Tests
# =============================================================================


@pytest.fixture
async def time_travel_cleanup_resources(db_manager: DatabaseSessionManager):
    """Cleanup resources for time travel tests."""
    entity_ids: list[str] = []
    entity_type_ids: list[str] = []

    yield {"entities": entity_ids, "entity_types": entity_type_ids}

    # Cleanup after test
    async with db_manager.session() as session:
        for entity_id in entity_ids:
            await session.execute(
                text("DELETE FROM do_entity_history WHERE entity_id = :id"),
                {"id": entity_id},
            )
            await session.execute(
                text("DELETE FROM do_entities WHERE id = :id"),
                {"id": entity_id},
            )
        for entity_type_id in entity_type_ids:
            await session.execute(
                text("DELETE FROM do_entity_types WHERE id = :id"),
                {"id": entity_type_id},
            )


class TestQueryEngineTimeTravel:
    """Test cases for QueryEngine at_time (time travel) functionality."""

    @pytest.mark.asyncio
    async def test_query_with_at_time(
        self,
        db_manager: DatabaseSessionManager,
        sample_entity_type: EntityType,
        time_travel_cleanup_resources: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Test query with at_time returns entity state at that point in time.

        Scenario:
        1. Create entity with initial properties
        2. Record timestamp
        3. Update entity with new properties
        4. Query with at_time using recorded timestamp
        5. Verify the returned entity has the original properties
        """
        import time

        # Create entity type
        async with db_manager.session() as session:
            repo = PostgresEntityTypeRepository(session, test_namespace_id)
            persisted_type = await repo.create(sample_entity_type)
            time_travel_cleanup_resources["entity_types"].append(str(persisted_type.id))

        # Create entity with initial properties
        entity = Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Original Title", "count": 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            created = await repo.create(entity)
            time_travel_cleanup_resources["entities"].append(str(created.id))

        # Small delay to ensure distinct timestamps
        time.sleep(0.1)

        # Record timestamp AFTER creation, BEFORE update
        snapshot_time = datetime.now(UTC)

        # Small delay before update
        time.sleep(0.1)

        # Update entity with new properties
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            updated_entity = Entity(
                id=created.id,
                type_id=persisted_type.id,
                version=2,
                properties={"title": "Updated Title", "count": 20},
                created_at=created.created_at,
                updated_at=datetime.now(UTC),
            )
            await repo.update(updated_entity, current_version=1)

        # Query with at_time to get the state at snapshot_time
        async with db_manager.session() as session:
            engine = QueryEngine(session, test_namespace_id)
            query = Query(
                entity_type=persisted_type.name,
                at_time=snapshot_time,
            )
            result = await engine.execute(query)

            # Should return the entity in its original state
            assert result.total == 1
            assert len(result.items) == 1

            returned_entity = result.items[0]
            assert returned_entity.id == created.id
            assert returned_entity.properties["title"] == "Original Title"
            assert returned_entity.properties["count"] == 10
            assert returned_entity.version == 1

    @pytest.mark.asyncio
    async def test_query_at_time_before_entity_created(
        self,
        db_manager: DatabaseSessionManager,
        sample_entity_type: EntityType,
        time_travel_cleanup_resources: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Test query with at_time before entity creation returns empty result.

        Scenario:
        1. Record timestamp
        2. Create entity after that timestamp
        3. Query with at_time using the recorded timestamp
        4. Verify empty result is returned
        """
        import time

        # Create entity type
        async with db_manager.session() as session:
            repo = PostgresEntityTypeRepository(session, test_namespace_id)
            persisted_type = await repo.create(sample_entity_type)
            time_travel_cleanup_resources["entity_types"].append(str(persisted_type.id))

        # Record timestamp BEFORE entity creation
        before_creation_time = datetime.now(UTC)

        # Small delay to ensure entity is created after the timestamp
        time.sleep(0.1)

        # Create entity after the timestamp
        entity = Entity(
            id=uuid4(),
            type_id=persisted_type.id,
            version=1,
            properties={"title": "Test Entity", "count": 100},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            created = await repo.create(entity)
            time_travel_cleanup_resources["entities"].append(str(created.id))

        # Query with at_time before entity was created
        async with db_manager.session() as session:
            engine = QueryEngine(session, test_namespace_id)
            query = Query(
                entity_type=persisted_type.name,
                at_time=before_creation_time,
            )
            result = await engine.execute(query)

            # Should return empty result since entity didn't exist at that time
            assert result.total == 0
            assert len(result.items) == 0


# =============================================================================
# REGEX Filter Tests
# =============================================================================


@pytest.fixture
def email_entity_type() -> EntityType:
    """Create entity type for REGEX filter tests with email property."""
    return EntityType(
        id=uuid4(),
        name=f"EmailTestType_{uuid4().hex[:8]}",
        description="Entity type for REGEX filter tests",
        properties={
            "email": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=True,
                max_length=255,
            ),
            "name": PropertyDefinition(
                type=PropertyType.STRING,
                required=False,
                indexed=False,
                max_length=255,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_query_with_regex_filter(
    db_manager: DatabaseSessionManager,
    email_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Query with REGEX filter should match patterns."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(email_entity_type)
        cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities with different email formats
    entities_data = [
        {"email": "user@example.com", "name": "User 1"},
        {"email": "admin@example.org", "name": "User 2"},
        {"email": "test@example.com", "name": "User 3"},
        {"email": "invalid-email", "name": "User 4"},
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for data in entities_data:
            entity = Entity(
                id=uuid4(),
                type_id=persisted_type.id,
                version=1,
                properties=data,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))

    # Query with REGEX pattern for .com emails
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            filter=FilterCondition(
                field="email",
                operator=FilterOperator.REGEX,
                value=r".*@example\.com$",
            ),
        )
        result = await engine.execute(query)

        assert len(result.items) == 2
        emails = {e.properties["email"] for e in result.items}
        assert emails == {"user@example.com", "test@example.com"}


# ============================================================================
# FULL_TEXT Filter Tests
# ============================================================================


@pytest.fixture
def fulltext_entity_type() -> EntityType:
    """Create entity type for FULL_TEXT filter tests with title property."""
    return EntityType(
        id=uuid4(),
        name=f"FullTextTestType_{uuid4().hex[:8]}",
        description="Entity type for FULL_TEXT filter tests",
        properties={
            "title": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=True,
                max_length=255,
            ),
            "description": PropertyDefinition(
                type=PropertyType.STRING,
                required=False,
                indexed=False,
                max_length=500,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_query_with_full_text_filter(
    db_manager: DatabaseSessionManager,
    fulltext_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Query with FULL_TEXT filter should match words."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(fulltext_entity_type)
        cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities with different titles
    entities_data = [
        {"title": "Python Programming Guide", "description": "Learn Python basics"},
        {"title": "JavaScript Tutorial", "description": "Web development with JS"},
        {"title": "Python Web Framework", "description": "Build web apps with Python"},
        {"title": "Database Design", "description": "SQL and PostgreSQL basics"},
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for data in entities_data:
            entity = Entity(
                id=uuid4(),
                type_id=persisted_type.id,
                version=1,
                properties=data,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))

    # Query with FULL_TEXT search for "python"
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            filter=FilterCondition(
                field="title",
                operator=FilterOperator.FULL_TEXT,
                value="python",
            ),
        )
        result = await engine.execute(query)

        assert len(result.items) == 2
        titles = {e.properties["title"] for e in result.items}
        assert titles == {"Python Programming Guide", "Python Web Framework"}


@pytest.mark.asyncio
async def test_query_with_full_text_multiple_words(
    db_manager: DatabaseSessionManager,
    fulltext_entity_type: EntityType,
    cleanup_resources: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Query with FULL_TEXT filter with multiple words should match all words (AND)."""
    # Create entity type
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        persisted_type = await repo.create(fulltext_entity_type)
        cleanup_resources["entity_types"].append(str(persisted_type.id))

    # Create test entities
    entities_data = [
        {"title": "Python Programming Guide"},
        {"title": "Python Web Framework"},
        {"title": "Web Development Basics"},
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for data in entities_data:
            entity = Entity(
                id=uuid4(),
                type_id=persisted_type.id,
                version=1,
                properties=data,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            created = await repo.create(entity)
            cleanup_resources["entities"].append(str(created.id))

    # Query with multiple words (should match both "python" AND "web")
    async with db_manager.session() as session:
        engine = QueryEngine(session, test_namespace_id)
        query = Query(
            entity_type=persisted_type.name,
            filter=FilterCondition(
                field="title",
                operator=FilterOperator.FULL_TEXT,
                value="python web",
            ),
        )
        result = await engine.execute(query)

        # Only "Python Web Framework" matches both words
        assert len(result.items) == 1
        assert result.items[0].properties["title"] == "Python Web Framework"
