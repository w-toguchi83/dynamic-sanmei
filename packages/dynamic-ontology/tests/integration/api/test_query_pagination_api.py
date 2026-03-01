"""Query ページネーション API 統合テスト."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def query_pagination_type(client: AsyncClient) -> str:
    """テスト用エンティティタイプ名を返す."""
    suffix = uuid4().hex[:8]
    type_name = f"QueryPagApi_{suffix}"
    type_resp = await client.post(
        "/schema/entity-types",
        json={
            "name": type_name,
            "properties": {"name": {"type": "string", "required": True}},
        },
    )
    type_id = type_resp.json()["id"]
    for i in range(5):
        await client.post(
            "/entities",
            json={"type_id": type_id, "properties": {"name": f"item_{i}"}},
        )
    return type_name


@pytest.mark.asyncio
class TestQueryPagination:
    async def test_returns_cursor_fields(self, client: AsyncClient, query_pagination_type: str) -> None:
        resp = await client.post(
            "/query",
            json={"entity_type": query_pagination_type, "limit": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

    async def test_cursor_pagination(self, client: AsyncClient, query_pagination_type: str) -> None:
        resp1 = await client.post(
            "/query",
            json={"entity_type": query_pagination_type, "limit": 2},
        )
        cursor = resp1.json()["next_cursor"]

        resp2 = await client.post(
            "/query",
            json={
                "entity_type": query_pagination_type,
                "limit": 2,
                "cursor": cursor,
            },
        )
        data2 = resp2.json()
        assert len(data2["items"]) == 2
        ids1 = {item["id"] for item in resp1.json()["items"]}
        ids2 = {item["id"] for item in data2["items"]}
        assert ids1.isdisjoint(ids2)

    async def test_cursor_with_sort_returns_400(self, client: AsyncClient, query_pagination_type: str) -> None:
        resp = await client.post(
            "/query",
            json={
                "entity_type": query_pagination_type,
                "limit": 2,
                "cursor": "dummy_cursor",
                "sort": [{"field": "name", "order": "asc"}],
            },
        )
        assert resp.status_code == 400

    async def test_invalid_cursor_returns_400(self, client: AsyncClient, query_pagination_type: str) -> None:
        resp = await client.post(
            "/query",
            json={
                "entity_type": query_pagination_type,
                "limit": 2,
                "cursor": "not_valid!!!",
            },
        )
        assert resp.status_code == 400

    async def test_offset_still_works(self, client: AsyncClient, query_pagination_type: str) -> None:
        resp = await client.post(
            "/query",
            json={
                "entity_type": query_pagination_type,
                "limit": 3,
                "offset": 3,
            },
        )
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
