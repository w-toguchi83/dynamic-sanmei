"""Relationship ページネーション API 統合テスト."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def paginated_relationships(client: AsyncClient) -> tuple[str, str]:
    """1 source + 5 relationships を作成."""
    suffix = uuid4().hex[:8]
    type_resp = await client.post(
        "/schema/entity-types",
        json={
            "name": f"RelPagApi_{suffix}",
            "properties": {"name": {"type": "string", "required": True}},
        },
    )
    type_id = type_resp.json()["id"]
    rt_resp = await client.post(
        "/schema/relationship-types",
        json={"name": f"rel_pag_api_{suffix}", "directional": True},
    )
    rt_id = rt_resp.json()["id"]

    source_resp = await client.post(
        "/entities",
        json={"type_id": type_id, "properties": {"name": "source"}},
    )
    source_id = source_resp.json()["id"]

    for i in range(5):
        t_resp = await client.post(
            "/entities",
            json={"type_id": type_id, "properties": {"name": f"target_{i}"}},
        )
        t_id = t_resp.json()["id"]
        await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": source_id,
                "to_entity_id": t_id,
                "properties": {},
            },
        )

    return source_id, rt_id


@pytest.mark.asyncio
class TestRelationshipListPagination:
    async def test_returns_paginated_response(
        self,
        client: AsyncClient,
        paginated_relationships: tuple[str, str],
    ) -> None:
        source_id, _ = paginated_relationships
        resp = await client.get(f"/entities/{source_id}/relationships?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"] is not None
        assert data["limit"] == 2
        assert data["offset"] == 0

    async def test_cursor_pagination(
        self,
        client: AsyncClient,
        paginated_relationships: tuple[str, str],
    ) -> None:
        source_id, _ = paginated_relationships
        resp1 = await client.get(f"/entities/{source_id}/relationships?limit=2")
        cursor = resp1.json()["next_cursor"]

        resp2 = await client.get(f"/entities/{source_id}/relationships?limit=2&cursor={cursor}")
        data2 = resp2.json()
        assert len(data2["items"]) == 2
        ids1 = {item["id"] for item in resp1.json()["items"]}
        ids2 = {item["id"] for item in data2["items"]}
        assert ids1.isdisjoint(ids2)
