"""EntityRepository ページネーション統合テスト."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager
from dynamic_ontology.adapters.persistence.postgresql.entity_repository import PostgresEntityRepository
from dynamic_ontology.adapters.persistence.postgresql.entity_type_repository import PostgresEntityTypeRepository
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.services.cursor import encode_cursor


@pytest.fixture
def sample_entity_type() -> EntityType:
    """ページネーションテスト用のエンティティタイプ."""
    return EntityType(
        id=uuid4(),
        name=f"PaginationTest_{uuid4().hex[:8]}",
        description="For pagination tests",
        properties={
            "name": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=False,
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
    """エンティティタイプをDBに永続化."""
    async with db_manager.session() as session:
        repo = PostgresEntityTypeRepository(session, test_namespace_id)
        created = await repo.create(sample_entity_type)
        await session.commit()
        return created


@pytest.fixture
async def five_entities(
    db_manager: DatabaseSessionManager,
    persisted_entity_type: EntityType,
    test_namespace_id: str,
) -> list[Entity]:
    """5件のエンティティを作成."""
    entities: list[Entity] = []
    async with db_manager.session() as session:
        repo = PostgresEntityRepository(session, test_namespace_id)
        for i in range(5):
            e = Entity(
                id=uuid4(),
                type_id=persisted_entity_type.id,
                version=1,
                properties={"name": f"item_{i}"},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            created = await repo.create(e)
            entities.append(created)
        await session.commit()
    return entities


@pytest.mark.asyncio
class TestListByTypeWithCount:
    """list_by_type が (items, total) タプルを返すこと."""

    async def test_returns_tuple_with_total(
        self,
        db_manager: DatabaseSessionManager,
        five_entities: list[Entity],
        persisted_entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            items, total = await repo.list_by_type(str(persisted_entity_type.id), limit=3)
            assert len(items) == 3
            assert total == 5

    async def test_offset_pagination(
        self,
        db_manager: DatabaseSessionManager,
        five_entities: list[Entity],
        persisted_entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            items, total = await repo.list_by_type(str(persisted_entity_type.id), limit=3, offset=3)
            assert len(items) == 2
            assert total == 5


@pytest.mark.asyncio
class TestListByTypeCursor:
    """list_by_type のカーソルページネーション."""

    async def test_cursor_returns_next_page(
        self,
        db_manager: DatabaseSessionManager,
        five_entities: list[Entity],
        persisted_entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            page1, total = await repo.list_by_type(str(persisted_entity_type.id), limit=2)
            assert len(page1) == 2
            assert total == 5

            cursor = encode_cursor(page1[-1].created_at, page1[-1].id)
            page2, total2 = await repo.list_by_type(
                str(persisted_entity_type.id), limit=2, cursor=cursor
            )
            assert len(page2) == 2
            assert total2 == 5
            page1_ids = {e.id for e in page1}
            page2_ids = {e.id for e in page2}
            assert page1_ids.isdisjoint(page2_ids)

    async def test_cursor_ignores_offset(
        self,
        db_manager: DatabaseSessionManager,
        five_entities: list[Entity],
        persisted_entity_type: EntityType,
        test_namespace_id: str,
    ) -> None:
        async with db_manager.session() as session:
            repo = PostgresEntityRepository(session, test_namespace_id)
            page1, _ = await repo.list_by_type(str(persisted_entity_type.id), limit=2)
            cursor = encode_cursor(page1[-1].created_at, page1[-1].id)
            items_with_offset, _ = await repo.list_by_type(
                str(persisted_entity_type.id), limit=2, cursor=cursor, offset=100
            )
            items_without_offset, _ = await repo.list_by_type(
                str(persisted_entity_type.id), limit=2, cursor=cursor
            )
            assert [e.id for e in items_with_offset] == [e.id for e in items_without_offset]
