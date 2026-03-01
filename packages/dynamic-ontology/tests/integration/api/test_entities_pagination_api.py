"""Entity ページネーション API 統合テスト."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def paginated_entities(client: AsyncClient) -> str:
    """5件のエンティティを作成し type_id を返す."""
    suffix = uuid4().hex[:8]
    type_resp = await client.post(
        "/schema/entity-types",
        json={
            "name": f"PagApiTest_{suffix}",
            "properties": {"name": {"type": "string", "required": True}},
        },
    )
    assert type_resp.status_code == 201
    type_id = type_resp.json()["id"]
    for i in range(5):
        resp = await client.post(
            "/entities",
            json={"type_id": type_id, "properties": {"name": f"item_{i}"}},
        )
        assert resp.status_code == 201
    return type_id


@pytest.mark.asyncio
class TestEntityListPagination:
    async def test_returns_total_from_db(
        self, client: AsyncClient, paginated_entities: str
    ) -> None:
        resp = await client.get(f"/entities?type_id={paginated_entities}&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

    async def test_cursor_pagination(self, client: AsyncClient, paginated_entities: str) -> None:
        resp1 = await client.get(f"/entities?type_id={paginated_entities}&limit=2")
        data1 = resp1.json()
        cursor = data1["next_cursor"]

        resp2 = await client.get(
            f"/entities?type_id={paginated_entities}&limit=2&cursor={cursor}"
        )
        data2 = resp2.json()
        assert len(data2["items"]) == 2
        assert data2["total"] == 5
        ids1 = {item["id"] for item in data1["items"]}
        ids2 = {item["id"] for item in data2["items"]}
        assert ids1.isdisjoint(ids2)

    async def test_last_page_no_cursor(self, client: AsyncClient, paginated_entities: str) -> None:
        resp = await client.get(f"/entities?type_id={paginated_entities}&limit=10")
        data = resp.json()
        assert data["has_more"] is False
        assert data["next_cursor"] is None
        assert data["total"] == 5

    async def test_invalid_cursor_returns_400(
        self, client: AsyncClient, paginated_entities: str
    ) -> None:
        resp = await client.get(
            f"/entities?type_id={paginated_entities}&cursor=not_valid_base64!!!"
        )
        assert resp.status_code == 400

    async def test_offset_still_works(self, client: AsyncClient, paginated_entities: str) -> None:
        resp = await client.get(
            f"/entities?type_id={paginated_entities}&limit=3&offset=3"
        )
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
