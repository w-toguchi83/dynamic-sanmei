"""Integration tests for EntityRepository batch operations."""

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
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType


@pytest.fixture
async def db_manager(database_url: str) -> AsyncGenerator[DatabaseSessionManager]:
    """Create and initialize database manager."""
    manager = DatabaseSessionManager()
    manager.init(database_url)
    yield manager
    await manager.close()


@pytest.fixture
async def entity_type(db_manager: DatabaseSessionManager, test_namespace_id: str) -> EntityType:
    """Create an entity type for batch tests."""
    entity_type = EntityType(
        id=uuid4(),
        name=f"BatchTest_{uuid4().hex[:8]}",
        description="Entity type for batch tests",
        properties={
            "title": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=True,
            ),
            "count": PropertyDefinition(
                type=PropertyType.INTEGER,
                required=False,
                default=0,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        created = await repo.create(entity_type)
        await session.commit()
        return created


class TestCreateMany:
    """Tests for create_many batch operation."""

    async def test_create_many_success(
        self,
        db_manager: DatabaseSessionManager,
        entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        """create_many creates all entities and returns success BatchResult."""
        now = datetime.now(UTC)
        entities = [
            Entity(
                id=uuid4(),
                type_id=entity_type.id,
                version=1,
                properties={"title": f"Entity {i}", "count": i},
                created_at=now,
                updated_at=now,
            )
            for i in range(3)
        ]

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            result = await repo.create_many(entities)
            await session.commit()

            assert result.success is True
            assert result.total == 3
            assert result.succeeded == 3
            assert result.failed == 0
            assert len(result.entity_ids) == 3
            assert result.errors == []

            # Verify entities exist
            for entity in entities:
                fetched = await repo.get_by_id(str(entity.id))
                assert fetched is not None
                assert fetched.properties["title"] == entity.properties["title"]

    async def test_create_many_empty_list(self, db_manager: DatabaseSessionManager, test_namespace_id: str) -> None:
        """create_many with empty list returns success with zero counts."""
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            result = await repo.create_many([])

            assert result.success is True
            assert result.total == 0
            assert result.succeeded == 0
            assert result.entity_ids == []

    async def test_create_many_records_history(
        self,
        db_manager: DatabaseSessionManager,
        entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        """create_many records history for each created entity."""
        now = datetime.now(UTC)
        entities = [
            Entity(
                id=uuid4(),
                type_id=entity_type.id,
                version=1,
                properties={"title": f"History Test {i}"},
                created_at=now,
                updated_at=now,
            )
            for i in range(2)
        ]

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            await repo.create_many(entities)
            await session.commit()

            # Check history exists for each entity
            for entity in entities:
                history = await repo.get_history(str(entity.id))
                assert len(history) == 1
                assert history[0]["operation"] == "CREATE"
                assert history[0]["version"] == 1


class TestUpdateMany:
    """Tests for update_many batch operation."""

    async def test_update_many_success(
        self,
        db_manager: DatabaseSessionManager,
        entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        """update_many updates all entities and returns success BatchResult."""
        now = datetime.now(UTC)
        # Create entities first
        entities = [
            Entity(
                id=uuid4(),
                type_id=entity_type.id,
                version=1,
                properties={"title": f"Original {i}"},
                created_at=now,
                updated_at=now,
            )
            for i in range(3)
        ]

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            await repo.create_many(entities)
            await session.commit()

            # Prepare updates
            updates: list[tuple[Entity, int]] = []
            for entity in entities:
                updated_entity = Entity(
                    id=entity.id,
                    type_id=entity.type_id,
                    version=2,
                    properties={"title": f"Updated {entity.properties['title']}"},
                    created_at=entity.created_at,
                    updated_at=now,
                )
                updates.append((updated_entity, 1))  # current_version=1

            result = await repo.update_many(updates)
            await session.commit()

            assert result.success is True
            assert result.total == 3
            assert result.succeeded == 3
            assert result.failed == 0
            assert len(result.entity_ids) == 3

            # Verify updates
            for entity in entities:
                fetched = await repo.get_by_id(str(entity.id))
                assert fetched is not None
                assert fetched.version == 2
                assert "Updated" in fetched.properties["title"]

    async def test_update_many_version_conflict(
        self,
        db_manager: DatabaseSessionManager,
        entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        """update_many fails on version conflict."""
        now = datetime.now(UTC)
        entity = Entity(
            id=uuid4(),
            type_id=entity_type.id,
            version=1,
            properties={"title": "Original"},
            created_at=now,
            updated_at=now,
        )

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            await repo.create_many([entity])
            await session.commit()

            # Try to update with wrong version
            updated_entity = Entity(
                id=entity.id,
                type_id=entity.type_id,
                version=2,
                properties={"title": "Updated"},
                created_at=entity.created_at,
                updated_at=now,
            )
            result = await repo.update_many([(updated_entity, 999)])  # Wrong version

            assert result.success is False
            assert result.failed == 1
            assert len(result.errors) == 1
            assert "version" in result.errors[0].message.lower()

    async def test_update_many_records_history(
        self,
        db_manager: DatabaseSessionManager,
        entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        """update_many records history for each updated entity."""
        now = datetime.now(UTC)
        entity = Entity(
            id=uuid4(),
            type_id=entity_type.id,
            version=1,
            properties={"title": "Original"},
            created_at=now,
            updated_at=now,
        )

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            await repo.create_many([entity])
            await session.commit()

            # Update
            updated_entity = Entity(
                id=entity.id,
                type_id=entity.type_id,
                version=2,
                properties={"title": "Updated"},
                created_at=entity.created_at,
                updated_at=now,
            )
            await repo.update_many([(updated_entity, 1)])
            await session.commit()

            # Check history
            history = await repo.get_history(str(entity.id))
            assert len(history) == 2
            operations = [h["operation"] for h in history]
            assert "CREATE" in operations
            assert "UPDATE" in operations

    async def test_update_many_empty_list(self, db_manager: DatabaseSessionManager, test_namespace_id: str) -> None:
        """update_many with empty list returns success with zero counts."""
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            result = await repo.update_many([])

            assert result.success is True
            assert result.total == 0
            assert result.succeeded == 0
            assert result.entity_ids == []


class TestDeleteMany:
    """Tests for delete_many batch operation."""

    async def test_delete_many_success(
        self,
        db_manager: DatabaseSessionManager,
        entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        """delete_many deletes all entities and returns success BatchResult."""
        now = datetime.now(UTC)
        entities = [
            Entity(
                id=uuid4(),
                type_id=entity_type.id,
                version=1,
                properties={"title": f"To Delete {i}"},
                created_at=now,
                updated_at=now,
            )
            for i in range(3)
        ]

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            await repo.create_many(entities)
            await session.commit()

            # Delete all
            entity_ids = [str(e.id) for e in entities]
            result = await repo.delete_many(entity_ids)
            await session.commit()

            assert result.success is True
            assert result.total == 3
            assert result.succeeded == 3
            assert result.failed == 0

            # Verify deleted
            for entity in entities:
                fetched = await repo.get_by_id(str(entity.id))
                assert fetched is None

    async def test_delete_many_not_found(self, db_manager: DatabaseSessionManager, test_namespace_id: str) -> None:
        """delete_many fails when entity not found."""
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            non_existent_id = str(uuid4())

            result = await repo.delete_many([non_existent_id])

            assert result.success is False
            assert result.failed == 1
            assert len(result.errors) == 1
            assert "not found" in result.errors[0].message.lower()

    async def test_delete_many_partial_not_found(
        self,
        db_manager: DatabaseSessionManager,
        entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        """delete_many fails if any entity not found (all-or-nothing)."""
        now = datetime.now(UTC)
        entity = Entity(
            id=uuid4(),
            type_id=entity_type.id,
            version=1,
            properties={"title": "Exists"},
            created_at=now,
            updated_at=now,
        )

        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            await repo.create_many([entity])
            await session.commit()

            # Try to delete existing + non-existing
            result = await repo.delete_many([str(entity.id), str(uuid4())])

            assert result.success is False
            assert result.failed == 1  # One not found

    async def test_delete_many_empty_list(self, db_manager: DatabaseSessionManager, test_namespace_id: str) -> None:
        """delete_many with empty list returns success."""
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            result = await repo.delete_many([])

            assert result.success is True
            assert result.total == 0
