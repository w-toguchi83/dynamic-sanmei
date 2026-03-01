"""Integration tests for RelationshipType CRUD API endpoints."""

from uuid import uuid4

from httpx import AsyncClient


class TestRelationshipTypeCRUDAPI:
    """RelationshipType CRUD エンドポイントの基本テスト。"""

    async def test_create_relationship_type(self, client: AsyncClient) -> None:
        unique_name = f"Rel_{uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "description": "A test relationship type",
            "directional": True,
            "properties": {},
            "custom_validators": [],
            "allowed_source_types": [],
            "allowed_target_types": [],
            "allow_duplicates": True,
        }

        response = await client.post("/schema/relationship-types", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == unique_name
        assert data["directional"] is True

    async def test_list_relationship_types(self, client: AsyncClient) -> None:
        unique_name = f"Rel_{uuid4().hex[:8]}"
        await client.post(
            "/schema/relationship-types",
            json={
                "name": unique_name,
                "directional": False,
                "properties": {},
                "custom_validators": [],
                "allowed_source_types": [],
                "allowed_target_types": [],
                "allow_duplicates": False,
            },
        )

        response = await client.get("/schema/relationship-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(rt["name"] == unique_name for rt in data)
