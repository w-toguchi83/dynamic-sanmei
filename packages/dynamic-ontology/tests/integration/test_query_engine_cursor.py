"""QueryEngine カーソルページネーション統合テスト."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager
from dynamic_ontology.adapters.persistence.postgresql.entity_repository import PostgresEntityRepository
from dynamic_ontology.adapters.persistence.postgresql.entity_type_repository import PostgresEntityTypeRepository
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.query import Query, SortDirection, SortField
from dynamic_ontology.domain.services.query_engine import QueryEngine


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
async def cursor_test_setup(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> tuple[str, list[str], str]:
    """テスト用にエンティティタイプと5件のエンティティを作成.

    Returns:
        (entity_type_name, entity_ids, entity_type_id) のタプル
    """
    suffix = uuid4().hex[:8]
    et_name = f"QueryCursorType_{suffix}"

    et = EntityType(
        id=uuid4(),
        name=et_name,
        description="",
        properties={
            "name": PropertyDefinition(type=PropertyType.STRING, required=True, indexed=False),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    entity_ids: list[str] = []

    async with db_manager.session() as session:
        et_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        await et_repo.create(et)

        e_repo = PostgresEntityRepository(session, test_namespace_id)
        for i in range(5):
            e = Entity(
                id=uuid4(),
                type_id=et.id,
                version=1,
                properties={"name": f"item_{i}"},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            created = await e_repo.create(e)
            entity_ids.append(str(created.id))

    yield et_name, entity_ids, str(et.id)

    # クリーンアップ
    async with db_manager.session() as session:
        for eid in entity_ids:
            await session.execute(
                text("DELETE FROM do_entity_history WHERE entity_id = :id"),
                {"id": eid},
            )
            await session.execute(
                text("DELETE FROM do_entities WHERE id = :id"),
                {"id": eid},
            )
        await session.execute(
            text("DELETE FROM do_entity_types WHERE id = :id"),
            {"id": str(et.id)},
        )


@pytest.mark.asyncio
class TestQueryEngineCursor:
    async def test_first_page_has_next_cursor(
        self,
        db_manager: DatabaseSessionManager,
        cursor_test_setup: tuple[str, list[str], str],
        test_namespace_id: str,
    ) -> None:
        """最初のページにnext_cursorが含まれることを確認."""
        et_name, _entity_ids, _et_id = cursor_test_setup

        async with db_manager.session() as session:
            engine = QueryEngine(session, test_namespace_id)
            result = await engine.execute(Query(entity_type=et_name, limit=2))

        assert len(result.items) == 2
        assert result.total == 5
        assert result.next_cursor is not None
        assert result.has_more is True

    async def test_cursor_returns_next_page(
        self,
        db_manager: DatabaseSessionManager,
        cursor_test_setup: tuple[str, list[str], str],
        test_namespace_id: str,
    ) -> None:
        """カーソルで次のページを取得できることを確認."""
        et_name, _entity_ids, _et_id = cursor_test_setup

        async with db_manager.session() as session:
            engine = QueryEngine(session, test_namespace_id)
            page1 = await engine.execute(Query(entity_type=et_name, limit=2))

        assert page1.next_cursor is not None

        async with db_manager.session() as session:
            engine = QueryEngine(session, test_namespace_id)
            page2 = await engine.execute(
                Query(entity_type=et_name, limit=2, cursor=page1.next_cursor)
            )

        assert len(page2.items) == 2
        assert page2.has_more is True
        ids1 = {e.id for e in page1.items}
        ids2 = {e.id for e in page2.items}
        assert ids1.isdisjoint(ids2)

    async def test_last_page_has_no_cursor(
        self,
        db_manager: DatabaseSessionManager,
        cursor_test_setup: tuple[str, list[str], str],
        test_namespace_id: str,
    ) -> None:
        """最後のページではnext_cursorがNoneであることを確認."""
        et_name, _entity_ids, _et_id = cursor_test_setup

        async with db_manager.session() as session:
            engine = QueryEngine(session, test_namespace_id)
            result = await engine.execute(Query(entity_type=et_name, limit=5))

        assert result.has_more is False
        assert result.next_cursor is None

    async def test_cursor_with_custom_sort_raises_error(
        self,
        db_manager: DatabaseSessionManager,
        cursor_test_setup: tuple[str, list[str], str],
        test_namespace_id: str,
    ) -> None:
        """カーソルとカスタムソートの併用でValueErrorが発生することを確認."""
        et_name, _entity_ids, _et_id = cursor_test_setup

        async with db_manager.session() as session:
            engine = QueryEngine(session, test_namespace_id)
            with pytest.raises(ValueError, match="custom sort"):
                await engine.execute(
                    Query(
                        entity_type=et_name,
                        limit=2,
                        cursor="dummy",
                        sort=[SortField(field="name", direction=SortDirection.ASC)],
                    )
                )

    async def test_full_cursor_traversal(
        self,
        db_manager: DatabaseSessionManager,
        cursor_test_setup: tuple[str, list[str], str],
        test_namespace_id: str,
    ) -> None:
        """カーソルで全ページを巡回して全アイテムを取得できることを確認."""
        et_name, _entity_ids, _et_id = cursor_test_setup

        all_ids: set[str] = set()
        cursor: str | None = None
        pages = 0

        while True:
            async with db_manager.session() as session:
                engine = QueryEngine(session, test_namespace_id)
                result = await engine.execute(Query(entity_type=et_name, limit=2, cursor=cursor))

            for item in result.items:
                all_ids.add(str(item.id))
            pages += 1
            cursor = result.next_cursor

            if not result.has_more:
                break

        # 5件を2件ずつ → 3ページ（2+2+1）
        assert pages == 3
        assert len(all_ids) == 5
