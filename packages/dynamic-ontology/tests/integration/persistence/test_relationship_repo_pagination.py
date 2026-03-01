"""RelationshipRepository ページネーション統合テスト."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager
from dynamic_ontology.adapters.persistence.postgresql.entity_repository import PostgresEntityRepository
from dynamic_ontology.adapters.persistence.postgresql.entity_type_repository import PostgresEntityTypeRepository
from dynamic_ontology.adapters.persistence.postgresql.relationship_repository import (
    PostgresRelationshipRepository,
)
from dynamic_ontology.adapters.persistence.postgresql.relationship_type_repository import (
    PostgresRelationshipTypeRepository,
)
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.relationship import Relationship, RelationshipType
from dynamic_ontology.domain.services.cursor import encode_cursor


@pytest.fixture
async def rel_pagination_setup(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> tuple[Entity, list[Relationship]]:
    """リレーションページネーション用セットアップ."""
    suffix = uuid4().hex[:8]

    async with db_manager.session() as session:
        et_repo = PostgresEntityTypeRepository(session, test_namespace_id)
        et = EntityType(
            id=uuid4(),
            name=f"RelPagNode_{suffix}",
            description="",
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
        await et_repo.create(et)

        rt_repo = PostgresRelationshipTypeRepository(session, test_namespace_id)
        rt = RelationshipType(
            id=uuid4(),
            name=f"rel_pag_link_{suffix}",
            description="",
            directional=True,
            properties={},
            custom_validators=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await rt_repo.create(rt)

        e_repo = PostgresEntityRepository(session, test_namespace_id)
        source = Entity(
            id=uuid4(),
            type_id=et.id,
            version=1,
            properties={"name": "source"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await e_repo.create(source)

        r_repo = PostgresRelationshipRepository(session, test_namespace_id)
        rels: list[Relationship] = []
        for i in range(5):
            t = Entity(
                id=uuid4(),
                type_id=et.id,
                version=1,
                properties={"name": f"target_{i}"},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            await e_repo.create(t)
            r = Relationship(
                id=uuid4(),
                type_id=rt.id,
                from_entity_id=source.id,
                to_entity_id=t.id,
                version=1,
                properties={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            await r_repo.create(r)
            rels.append(r)

        await session.commit()
        return source, rels


@pytest.mark.asyncio
class TestListByEntityPagination:
    """list_by_entity のページネーション統合テスト."""

    async def test_returns_tuple_with_total(
        self,
        db_manager: DatabaseSessionManager,
        rel_pagination_setup: tuple[Entity, list[Relationship]],
        test_namespace_id: str,
    ) -> None:
        """limit指定でアイテム数が制限され、totalが全件数を返すこと."""
        source, _ = rel_pagination_setup
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            items, total = await repo.list_by_entity(str(source.id), limit=3)
            assert len(items) == 3
            assert total == 5

    async def test_cursor_pagination(
        self,
        db_manager: DatabaseSessionManager,
        rel_pagination_setup: tuple[Entity, list[Relationship]],
        test_namespace_id: str,
    ) -> None:
        """カーソルで次ページが取得でき、前ページと重複しないこと."""
        source, _ = rel_pagination_setup
        async with db_manager.session() as session:
            repo = PostgresRelationshipRepository(session, test_namespace_id)
            page1, total = await repo.list_by_entity(str(source.id), limit=2)
            assert len(page1) == 2
            assert total == 5

            cursor = encode_cursor(page1[-1].created_at, page1[-1].id)
            page2, _ = await repo.list_by_entity(str(source.id), limit=2, cursor=cursor)
            assert len(page2) == 2
            page1_ids = {r.id for r in page1}
            page2_ids = {r.id for r in page2}
            assert page1_ids.isdisjoint(page2_ids)
