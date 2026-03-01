"""Integration tests for PostgresEntityRepository."""

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
from dynamic_ontology.domain.exceptions import VersionConflictError
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType


@pytest.fixture
def sample_entity_type() -> EntityType:
    """Create a sample entity type for testing."""
    return EntityType(
        id=uuid4(),
        name=f"EntityRepoTestType_{uuid4().hex[:8]}",
        description="A test entity type for entity repository tests",
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
def sample_entity(persisted_entity_type: EntityType) -> Entity:
    """Create a sample entity for testing."""
    return Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "Test Entity", "count": 42},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
async def cleanup_entities(db_manager: DatabaseSessionManager):
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
async def test_create_entity(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test creating an entity in the database."""
    entity = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "Created Entity", "count": 100},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result = await repo.create(entity)
        cleanup_entities["entities"].append(str(result.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

        assert result.id == entity.id
        assert result.type_id == entity.type_id
        assert result.version == 1
        assert result.properties == {"title": "Created Entity", "count": 100}


@pytest.mark.asyncio
async def test_get_entity_by_id(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test retrieving an entity by ID."""
    entity = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "Retrieve Test", "count": 50},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        created = await repo.create(entity)
        cleanup_entities["entities"].append(str(created.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # Retrieve in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result = await repo.get_by_id(str(entity.id))

        assert result is not None
        assert result.id == entity.id
        assert result.type_id == entity.type_id
        assert result.properties["title"] == "Retrieve Test"


@pytest.mark.asyncio
async def test_get_entity_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test retrieving a non-existent entity returns None."""
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result = await repo.get_by_id(str(uuid4()))
        assert result is None


@pytest.mark.asyncio
async def test_list_entities_by_type(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test listing entities by type."""
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": f"List Test {i}", "count": i * 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(3)
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            cleanup_entities["entities"].append(str(created.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # List in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result, total = await repo.list_by_type(str(persisted_entity_type.id))

        assert len(result) == 3
        assert total == 3
        result_ids = {str(e.id) for e in result}
        expected_ids = {str(e.id) for e in entities}
        assert result_ids == expected_ids


@pytest.mark.asyncio
async def test_list_entities_by_type_with_pagination(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test listing entities by type with pagination."""
    entities = [
        Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": f"Paginated {i}", "count": i},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(5)
    ]

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for entity in entities:
            created = await repo.create(entity)
            cleanup_entities["entities"].append(str(created.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # List with pagination
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result, total = await repo.list_by_type(str(persisted_entity_type.id), limit=2, offset=0)
        assert len(result) == 2
        assert total == 5

        result2, total2 = await repo.list_by_type(str(persisted_entity_type.id), limit=2, offset=2)
        assert len(result2) == 2
        assert total2 == 5


@pytest.mark.asyncio
async def test_update_entity_with_version(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test updating an entity increments version."""
    entity = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "Original Title", "count": 10},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        created = await repo.create(entity)
        cleanup_entities["entities"].append(str(created.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # Update in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        updated_entity = Entity(
            id=entity.id,
            type_id=entity.type_id,
            version=1,  # This is the current version we're updating from
            properties={"title": "Updated Title", "count": 20},
            created_at=entity.created_at,
            updated_at=datetime.now(UTC),
        )

        result = await repo.update(updated_entity, current_version=1)

        assert result.id == entity.id
        assert result.version == 2  # Version should be incremented
        assert result.properties["title"] == "Updated Title"
        assert result.properties["count"] == 20


@pytest.mark.asyncio
async def test_update_entity_version_conflict(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test that updating with wrong version raises VersionConflictError."""
    entity = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "Conflict Test", "count": 10},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        created = await repo.create(entity)
        cleanup_entities["entities"].append(str(created.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # Try to update with wrong version
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        updated_entity = Entity(
            id=entity.id,
            type_id=entity.type_id,
            version=99,  # Wrong version
            properties={"title": "Should Fail", "count": 999},
            created_at=entity.created_at,
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(VersionConflictError) as exc_info:
            await repo.update(updated_entity, current_version=99)

        assert exc_info.value.entity_id == str(entity.id)
        assert exc_info.value.current_version == 1
        assert exc_info.value.provided_version == 99


@pytest.mark.asyncio
async def test_delete_entity(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test deleting an entity."""
    entity = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "Delete Test"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        await repo.create(entity)
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # Delete in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result = await repo.delete(str(entity.id))
        assert result is True

    # Verify deletion
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result = await repo.get_by_id(str(entity.id))
        assert result is None


@pytest.mark.asyncio
async def test_delete_entity_not_found(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """Test deleting a non-existent entity returns False."""
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        result = await repo.delete(str(uuid4()))
        assert result is False


@pytest.mark.asyncio
async def test_entity_history_on_create(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test that creating an entity records history."""
    entity = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "History Create Test", "count": 5},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        created = await repo.create(entity)
        cleanup_entities["entities"].append(str(created.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # Check history in a new session
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        history = await repo.get_history(str(entity.id))

        assert len(history) == 1
        assert history[0]["entity_id"] == str(entity.id)
        assert history[0]["version"] == 1
        assert history[0]["operation"] == "CREATE"
        assert history[0]["properties"]["title"] == "History Create Test"
        assert history[0]["valid_to"] is None  # Current record has no end time


@pytest.mark.asyncio
async def test_entity_history_on_update(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test that updating an entity records history."""
    entity = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "Original", "count": 1},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        created = await repo.create(entity)
        cleanup_entities["entities"].append(str(created.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # Update the entity
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        updated_entity = Entity(
            id=entity.id,
            type_id=entity.type_id,
            version=1,
            properties={"title": "Updated", "count": 2},
            created_at=entity.created_at,
            updated_at=datetime.now(UTC),
        )
        await repo.update(updated_entity, current_version=1)

    # Check history
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        history = await repo.get_history(str(entity.id))

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
        assert history_sorted[1]["properties"]["title"] == "Updated"


@pytest.mark.asyncio
async def test_get_entity_at_time(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    cleanup_entities: dict[str, list[str]],
    test_namespace_id: str,
) -> None:
    """Test time-travel query to get entity at a specific point in time."""
    entity = Entity(
        id=uuid4(),
        type_id=persisted_entity_type.id,
        version=1,
        properties={"title": "Time Travel Original", "count": 100},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        created = await repo.create(entity)
        cleanup_entities["entities"].append(str(created.id))
        cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

    # Record time between create and update
    time_after_create = datetime.now(UTC)

    # Small delay to ensure time difference
    import asyncio

    await asyncio.sleep(0.1)

    # Update the entity
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        updated_entity = Entity(
            id=entity.id,
            type_id=entity.type_id,
            version=1,
            properties={"title": "Time Travel Updated", "count": 200},
            created_at=entity.created_at,
            updated_at=datetime.now(UTC),
        )
        await repo.update(updated_entity, current_version=1)

    # Query at time before update - should get original
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)

        # Get entity at time after create (should return v1)
        result = await repo.get_by_id(str(entity.id), at_time=time_after_create.isoformat())

        assert result is not None
        assert result.version == 1
        assert result.properties["title"] == "Time Travel Original"

    # Get current entity (no time specified) - should get updated version
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        current = await repo.get_by_id(str(entity.id))

        assert current is not None
        assert current.version == 2
        assert current.properties["title"] == "Time Travel Updated"


class TestEntityRepositoryTimeTravel:
    """EntityRepository のタイムトラベル機能（スナップショットクエリ）のテスト."""

    @pytest.mark.asyncio
    async def test_get_snapshots_returns_all_history(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        cleanup_entities: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """全履歴スナップショットが取得できることを確認.

        エンティティ作成 → 2回更新 → 3つのスナップショット確認
        """
        import asyncio

        entity = Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Snapshot Test v1", "count": 10},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # エンティティ作成
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            created = await repo.create(entity)
            cleanup_entities["entities"].append(str(created.id))
            cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

        # 1回目の更新
        await asyncio.sleep(0.05)
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            updated_entity = Entity(
                id=entity.id,
                type_id=entity.type_id,
                version=1,
                properties={"title": "Snapshot Test v2", "count": 20},
                created_at=entity.created_at,
                updated_at=datetime.now(UTC),
            )
            await repo.update(updated_entity, current_version=1)

        # 2回目の更新
        await asyncio.sleep(0.05)
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            updated_entity2 = Entity(
                id=entity.id,
                type_id=entity.type_id,
                version=2,
                properties={"title": "Snapshot Test v3", "count": 30},
                created_at=entity.created_at,
                updated_at=datetime.now(UTC),
            )
            await repo.update(updated_entity2, current_version=2)

        # 全スナップショット取得
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            snapshots = await repo.get_snapshots(str(entity.id))

            assert len(snapshots) == 3
            # バージョン順にソートされていることを確認
            assert snapshots[0].version == 1
            assert snapshots[1].version == 2
            assert snapshots[2].version == 3

            # 各スナップショットのプロパティを確認
            assert snapshots[0].properties["title"] == "Snapshot Test v1"
            assert snapshots[1].properties["title"] == "Snapshot Test v2"
            assert snapshots[2].properties["title"] == "Snapshot Test v3"

            # 最新以外は valid_to が設定されていることを確認
            assert snapshots[0].valid_to is not None
            assert snapshots[1].valid_to is not None
            assert snapshots[2].valid_to is None  # 最新は None

    @pytest.mark.asyncio
    async def test_get_snapshot_by_version(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        cleanup_entities: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """指定バージョンのスナップショットが取得できることを確認."""
        import asyncio

        entity = Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Version Query v1", "count": 100},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # エンティティ作成
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            created = await repo.create(entity)
            cleanup_entities["entities"].append(str(created.id))
            cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

        # 更新
        await asyncio.sleep(0.05)
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            updated_entity = Entity(
                id=entity.id,
                type_id=entity.type_id,
                version=1,
                properties={"title": "Version Query v2", "count": 200},
                created_at=entity.created_at,
                updated_at=datetime.now(UTC),
            )
            await repo.update(updated_entity, current_version=1)

        # バージョン1のスナップショットを取得
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            snapshot = await repo.get_snapshot_by_version(str(entity.id), version=1)

            assert snapshot is not None
            assert snapshot.entity_id == entity.id
            assert snapshot.version == 1
            assert snapshot.properties["title"] == "Version Query v1"
            assert snapshot.operation == "CREATE"
            assert snapshot.valid_to is not None  # 古いバージョンなので終了時刻あり

    @pytest.mark.asyncio
    async def test_get_snapshot_by_version_not_found(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        cleanup_entities: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """存在しないバージョンで None が返却されることを確認."""
        entity = Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Not Found Test"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # エンティティ作成
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            created = await repo.create(entity)
            cleanup_entities["entities"].append(str(created.id))
            cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

        # 存在しないバージョンで検索
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            snapshot = await repo.get_snapshot_by_version(str(entity.id), version=999)

            assert snapshot is None

    @pytest.mark.asyncio
    async def test_get_snapshot_at_time(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        cleanup_entities: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """指定時刻に有効なスナップショットが取得できることを確認."""
        import asyncio

        entity = Entity(
            id=uuid4(),
            type_id=persisted_entity_type.id,
            version=1,
            properties={"title": "Time Query v1", "count": 50},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # エンティティ作成
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            created = await repo.create(entity)
            cleanup_entities["entities"].append(str(created.id))
            cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

        # 時間を記録（作成後、更新前）
        await asyncio.sleep(0.1)
        time_between = datetime.now(UTC)
        await asyncio.sleep(0.1)

        # 更新
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            updated_entity = Entity(
                id=entity.id,
                type_id=entity.type_id,
                version=1,
                properties={"title": "Time Query v2", "count": 150},
                created_at=entity.created_at,
                updated_at=datetime.now(UTC),
            )
            await repo.update(updated_entity, current_version=1)

        # 過去の時点（更新前）のスナップショットを取得
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            snapshot = await repo.get_snapshot_at_time(str(entity.id), at_time=time_between)

            assert snapshot is not None
            assert snapshot.entity_id == entity.id
            assert snapshot.version == 1
            assert snapshot.properties["title"] == "Time Query v1"
            assert snapshot.operation == "CREATE"

        # 現在時刻のスナップショットを取得
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            current_snapshot = await repo.get_snapshot_at_time(str(entity.id), at_time=datetime.now(UTC))

            assert current_snapshot is not None
            assert current_snapshot.version == 2
            assert current_snapshot.properties["title"] == "Time Query v2"


class TestEntityRepositorySearchVector:
    """Tests for search_vector maintenance."""

    @pytest.mark.asyncio
    async def test_create_populates_search_vector(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        cleanup_entities: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Create should populate search_vector from properties."""
        repo_session = db_manager.session()
        async with repo_session as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            entity = Entity(
                id=uuid4(),
                type_id=persisted_entity_type.id,
                version=1,
                properties={"title": "Python Programming", "description": "Learn Python basics"},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            created = await repo.create(entity)
            cleanup_entities["entities"].append(str(created.id))
            cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

            # Verify search_vector was populated
            result = await session.execute(
                text("SELECT search_vector FROM do_entities WHERE id = :id"),
                {"id": str(created.id)},
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] is not None  # search_vector should be populated
            # Verify it contains expected tokens
            assert "python" in str(row[0]).lower()
            assert "programming" in str(row[0]).lower()

    @pytest.mark.asyncio
    async def test_update_updates_search_vector(
        self,
        db_manager: DatabaseSessionManager,
        persisted_entity_type: EntityType,
        cleanup_entities: dict[str, list[str]],
        test_namespace_id: str,
    ) -> None:
        """Update should refresh search_vector from new properties."""
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            entity = Entity(
                id=uuid4(),
                type_id=persisted_entity_type.id,
                version=1,
                properties={"title": "Original Title"},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            created = await repo.create(entity)
            cleanup_entities["entities"].append(str(created.id))
            cleanup_entities["entity_types"].append(str(persisted_entity_type.id))

            # Update with new properties
            updated_entity = Entity(
                id=created.id,
                type_id=created.type_id,
                version=created.version,
                properties={"title": "Updated Python Tutorial"},
                created_at=created.created_at,
                updated_at=created.updated_at,
            )
            await repo.update(updated_entity, current_version=1)

            # Verify search_vector was updated
            result = await session.execute(
                text("SELECT search_vector FROM do_entities WHERE id = :id"),
                {"id": str(created.id)},
            )
            row = result.fetchone()
            assert row is not None
            search_vector_str = str(row[0]).lower()
            assert "updated" in search_vector_str
            assert "python" in search_vector_str
            assert "tutorial" in search_vector_str
