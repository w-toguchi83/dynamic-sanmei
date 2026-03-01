"""Integration tests for RelationshipRepository batch operations."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest

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
from dynamic_ontology.domain.models.relationship import Relationship, RelationshipType


@pytest.fixture
async def db_manager(database_url: str) -> AsyncGenerator[DatabaseSessionManager]:
    """Create and initialize database manager."""
    manager = DatabaseSessionManager()
    manager.init(database_url)
    yield manager
    await manager.close()


@pytest.fixture
async def entity_type(db_manager: DatabaseSessionManager, test_namespace_id: str) -> EntityType:
    """Create an entity type for relationship batch tests."""
    et = EntityType(
        id=uuid4(),
        name=f"RelBatchNode_{uuid4().hex[:8]}",
        description="Entity type for relationship batch tests",
        properties={
            "name": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=True,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        created = await repo.create(et)
        await session.commit()
        return created


@pytest.fixture
async def entities(db_manager: DatabaseSessionManager, entity_type: EntityType, test_namespace_id: str) -> list[Entity]:
    """Create 3 entities to use as relationship endpoints."""
    now = datetime.now(UTC)
    entity_list = [
        Entity(
            id=uuid4(),
            type_id=entity_type.id,
            version=1,
            properties={"name": f"Node_{i}"},
            created_at=now,
            updated_at=now,
        )
        for i in range(3)
    ]
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result = await repo.create_many(entity_list)
        await session.commit()
        assert result.success is True
        return entity_list


@pytest.fixture
async def relationship_type(db_manager: DatabaseSessionManager, test_namespace_id: str) -> RelationshipType:
    """Create a relationship type for batch tests."""
    rt = RelationshipType(
        id=uuid4(),
        name=f"RelBatchEdge_{uuid4().hex[:8]}",
        description="Relationship type for batch tests",
        directional=True,
        properties={
            "weight": PropertyDefinition(
                type=PropertyType.FLOAT,
                required=False,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    async with db_manager.session() as session:
        repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        created = await repo.create(rt)
        await session.commit()
        return created


class TestRelationshipCreateMany:
    """Tests for RelationshipRepository.create_many batch operation."""

    async def test_create_many_success(
        self,
        db_manager: DatabaseSessionManager,
        entities: list[Entity],
        relationship_type: RelationshipType,
        test_namespace_id: str,
    ) -> None:
        """create_many creates all relationships and returns success BatchResult."""
        now = datetime.now(UTC)
        relationships = [
            Relationship(
                id=uuid4(),
                type_id=relationship_type.id,
                from_entity_id=entities[0].id,
                to_entity_id=entities[1].id,
                version=1,
                properties={"weight": 1.0},
                created_at=now,
                updated_at=now,
            ),
            Relationship(
                id=uuid4(),
                type_id=relationship_type.id,
                from_entity_id=entities[1].id,
                to_entity_id=entities[2].id,
                version=1,
                properties={"weight": 2.5},
                created_at=now,
                updated_at=now,
            ),
        ]

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.create_many(relationships)
            await session.commit()

            assert result.success is True
            assert result.total == 2
            assert result.succeeded == 2
            assert result.failed == 0
            assert len(result.entity_ids) == 2
            assert result.errors == []

            # Verify relationships exist in database
            for rel in relationships:
                fetched = await repo.get_by_id(str(rel.id))
                assert fetched is not None
                assert fetched.type_id == relationship_type.id

    async def test_create_many_empty_list(self, db_manager: DatabaseSessionManager, test_namespace_id: str) -> None:
        """create_many with empty list returns success with zero counts."""
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.create_many([])

            assert result.success is True
            assert result.total == 0
            assert result.succeeded == 0
            assert result.entity_ids == []

    async def test_create_many_records_history(
        self,
        db_manager: DatabaseSessionManager,
        entities: list[Entity],
        relationship_type: RelationshipType,
        test_namespace_id: str,
    ) -> None:
        """create_many records history with operation=CREATE and changed_by."""
        now = datetime.now(UTC)
        rel = Relationship(
            id=uuid4(),
            type_id=relationship_type.id,
            from_entity_id=entities[0].id,
            to_entity_id=entities[2].id,
            version=1,
            properties={"weight": 3.14},
            created_at=now,
            updated_at=now,
            changed_by="history-user",
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.create_many([rel])
            await session.commit()

            assert result.success is True

            # Verify history was recorded
            history = await repo.get_history(str(rel.id))
            assert len(history) == 1
            assert history[0]["operation"] == "CREATE"
            assert history[0]["version"] == 1
            assert history[0]["changed_by"] == "history-user"


class TestRelationshipUpdateMany:
    """Tests for RelationshipRepository.update_many batch operation."""

    async def test_update_many_success(
        self,
        db_manager: DatabaseSessionManager,
        entities: list[Entity],
        relationship_type: RelationshipType,
        test_namespace_id: str,
    ) -> None:
        """update_many updates all relationships and returns success BatchResult."""
        now = datetime.now(UTC)
        relationships = [
            Relationship(
                id=uuid4(),
                type_id=relationship_type.id,
                from_entity_id=entities[0].id,
                to_entity_id=entities[1].id,
                version=1,
                properties={"weight": 1.0},
                created_at=now,
                updated_at=now,
            ),
            Relationship(
                id=uuid4(),
                type_id=relationship_type.id,
                from_entity_id=entities[1].id,
                to_entity_id=entities[2].id,
                version=1,
                properties={"weight": 2.5},
                created_at=now,
                updated_at=now,
            ),
        ]

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            create_result = await repo.create_many(relationships)
            await session.commit()
            assert create_result.success is True

        # Now update both relationships with new properties
        updated_relationships = [
            Relationship(
                id=relationships[0].id,
                type_id=relationship_type.id,
                from_entity_id=entities[0].id,
                to_entity_id=entities[1].id,
                version=1,
                properties={"weight": 10.0},
                created_at=now,
                updated_at=now,
            ),
            Relationship(
                id=relationships[1].id,
                type_id=relationship_type.id,
                from_entity_id=entities[1].id,
                to_entity_id=entities[2].id,
                version=1,
                properties={"weight": 20.0},
                created_at=now,
                updated_at=now,
            ),
        ]

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.update_many([(updated_relationships[0], 1), (updated_relationships[1], 1)])
            await session.commit()

            assert result.success is True
            assert result.total == 2
            assert result.succeeded == 2
            assert result.failed == 0
            assert len(result.entity_ids) == 2
            assert result.errors == []

            # Verify updates persisted
            fetched0 = await repo.get_by_id(str(relationships[0].id))
            assert fetched0 is not None
            assert fetched0.properties["weight"] == 10.0
            assert fetched0.version == 2

            fetched1 = await repo.get_by_id(str(relationships[1].id))
            assert fetched1 is not None
            assert fetched1.properties["weight"] == 20.0
            assert fetched1.version == 2

    async def test_update_many_version_conflict(
        self,
        db_manager: DatabaseSessionManager,
        entities: list[Entity],
        relationship_type: RelationshipType,
        test_namespace_id: str,
    ) -> None:
        """update_many with wrong version returns failure with version conflict error."""
        now = datetime.now(UTC)
        rel = Relationship(
            id=uuid4(),
            type_id=relationship_type.id,
            from_entity_id=entities[0].id,
            to_entity_id=entities[2].id,
            version=1,
            properties={"weight": 5.0},
            created_at=now,
            updated_at=now,
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            create_result = await repo.create_many([rel])
            await session.commit()
            assert create_result.success is True

        # Try to update with wrong version (99 instead of 1)
        updated_rel = Relationship(
            id=rel.id,
            type_id=relationship_type.id,
            from_entity_id=entities[0].id,
            to_entity_id=entities[2].id,
            version=1,
            properties={"weight": 99.0},
            created_at=now,
            updated_at=now,
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.update_many([(updated_rel, 99)])

            assert result.success is False
            assert result.total == 1
            assert result.succeeded == 0
            assert result.failed == 1
            assert len(result.errors) == 1
            assert "Version conflict" in result.errors[0].message

    async def test_update_many_empty_list(self, db_manager: DatabaseSessionManager, test_namespace_id: str) -> None:
        """update_many with empty list returns success with zero counts."""
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.update_many([])

            assert result.success is True
            assert result.total == 0
            assert result.succeeded == 0
            assert result.entity_ids == []

    async def test_update_many_records_history(
        self,
        db_manager: DatabaseSessionManager,
        entities: list[Entity],
        relationship_type: RelationshipType,
        test_namespace_id: str,
    ) -> None:
        """update_many records history with CREATE + UPDATE operations and changed_by."""
        now = datetime.now(UTC)
        rel = Relationship(
            id=uuid4(),
            type_id=relationship_type.id,
            from_entity_id=entities[0].id,
            to_entity_id=entities[1].id,
            version=1,
            properties={"weight": 1.0},
            created_at=now,
            updated_at=now,
            changed_by="creator-user",
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            create_result = await repo.create_many([rel])
            await session.commit()
            assert create_result.success is True

        # Update with changed_by="batch-updater"
        updated_rel = Relationship(
            id=rel.id,
            type_id=relationship_type.id,
            from_entity_id=entities[0].id,
            to_entity_id=entities[1].id,
            version=1,
            properties={"weight": 42.0},
            created_at=now,
            updated_at=now,
            changed_by="batch-updater",
        )

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.update_many([(updated_rel, 1)])
            await session.commit()
            assert result.success is True

            # Verify history has 2 records: CREATE + UPDATE
            history = await repo.get_history(str(rel.id))
            assert len(history) == 2

            assert history[0]["operation"] == "CREATE"
            assert history[0]["version"] == 1
            assert history[0]["changed_by"] == "creator-user"
            assert history[0]["valid_to"] is not None  # Closed by update

            assert history[1]["operation"] == "UPDATE"
            assert history[1]["version"] == 2
            assert history[1]["changed_by"] == "batch-updater"
            assert history[1]["valid_to"] is None  # Current version


class TestRelationshipDeleteMany:
    """Tests for RelationshipRepository.delete_many batch operation."""

    async def test_delete_many_success(
        self,
        db_manager: DatabaseSessionManager,
        entities: list[Entity],
        relationship_type: RelationshipType,
        test_namespace_id: str,
    ) -> None:
        """delete_many deletes all relationships and returns success BatchResult."""
        now = datetime.now(UTC)
        relationships = [
            Relationship(
                id=uuid4(),
                type_id=relationship_type.id,
                from_entity_id=entities[0].id,
                to_entity_id=entities[1].id,
                version=1,
                properties={"weight": 1.0},
                created_at=now,
                updated_at=now,
            ),
            Relationship(
                id=uuid4(),
                type_id=relationship_type.id,
                from_entity_id=entities[1].id,
                to_entity_id=entities[2].id,
                version=1,
                properties={"weight": 2.5},
                created_at=now,
                updated_at=now,
            ),
        ]

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            create_result = await repo.create_many(relationships)
            await session.commit()
            assert create_result.success is True

        # Delete both relationships
        rel_ids = [str(r.id) for r in relationships]
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.delete_many(rel_ids)
            await session.commit()

            assert result.success is True
            assert result.total == 2
            assert result.succeeded == 2
            assert result.failed == 0
            assert len(result.entity_ids) == 2
            assert result.errors == []

            # Verify relationships are gone
            for rel in relationships:
                fetched = await repo.get_by_id(str(rel.id))
                assert fetched is None

    async def test_delete_many_not_found(
        self,
        db_manager: DatabaseSessionManager,
        test_namespace_id: str,
    ) -> None:
        """delete_many with non-existent ID returns failure with not-found error."""
        fake_id = str(uuid4())

        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.delete_many([fake_id])

            assert result.success is False
            assert result.total == 1
            assert result.succeeded == 0
            assert result.failed == 1
            assert len(result.errors) == 1
            assert "not found" in result.errors[0].message

    async def test_delete_many_empty_list(
        self,
        db_manager: DatabaseSessionManager,
        test_namespace_id: str,
    ) -> None:
        """delete_many with empty list returns success with zero counts."""
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            result = await repo.delete_many([])

            assert result.success is True
            assert result.total == 0
            assert result.succeeded == 0
            assert result.entity_ids == []
