"""Integration tests for EntityType CRUD API endpoints."""

from uuid import uuid4

from httpx import AsyncClient


class TestEntityTypeCRUDAPI:
    """Tests for EntityType CRUD endpoints."""

    async def test_create_entity_type(self, client: AsyncClient) -> None:
        """POST /schema/entity-types returns 201 with created entity."""
        unique_name = f"Task_{uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "description": "A test entity type",
            "properties": {
                "title": {
                    "type": "string",
                    "required": True,
                    "indexed": True,
                }
            },
            "custom_validators": [],
        }

        response = await client.post("/schema/entity-types", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == unique_name
        assert data["description"] == "A test entity type"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["properties"]["title"]["type"] == "string"
        assert data["properties"]["title"]["required"] is True
        assert data["properties"]["title"]["indexed"] is True

    async def test_get_entity_type_by_id(self, client: AsyncClient) -> None:
        """POST then GET by ID returns 200 with entity type."""
        unique_name = f"Task_{uuid4().hex[:8]}"
        create_payload = {
            "name": unique_name,
            "description": "Entity for GET test",
            "properties": {},
            "custom_validators": [],
        }

        create_response = await client.post(
            "/schema/entity-types", json=create_payload
        )
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        response = await client.get(f"/schema/entity-types/{created_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["name"] == unique_name

    async def test_get_entity_type_not_found(self, client: AsyncClient) -> None:
        """GET non-existent ID returns 404."""
        non_existent_id = str(uuid4())

        response = await client.get(f"/schema/entity-types/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_list_entity_types(self, client: AsyncClient) -> None:
        """Create then list, verify at least 1 entity type."""
        unique_name = f"Task_{uuid4().hex[:8]}"
        create_payload = {
            "name": unique_name,
            "description": "Entity for list test",
            "properties": {},
            "custom_validators": [],
        }

        await client.post("/schema/entity-types", json=create_payload)

        response = await client.get("/schema/entity-types")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        names = [et["name"] for et in data]
        assert unique_name in names

    async def test_update_entity_type(self, client: AsyncClient) -> None:
        """Create, update description, verify change."""
        unique_name = f"Task_{uuid4().hex[:8]}"
        create_payload = {
            "name": unique_name,
            "description": "Original description",
            "properties": {},
            "custom_validators": [],
        }

        create_response = await client.post(
            "/schema/entity-types", json=create_payload
        )
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        update_payload = {
            "description": "Updated description",
        }

        response = await client.put(
            f"/schema/entity-types/{created_id}", json=update_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["description"] == "Updated description"
        assert data["name"] == unique_name

    async def test_update_entity_type_not_found(self, client: AsyncClient) -> None:
        """PUT non-existent ID returns 404."""
        non_existent_id = str(uuid4())
        update_payload = {
            "description": "Updated description",
        }

        response = await client.put(
            f"/schema/entity-types/{non_existent_id}", json=update_payload
        )

        assert response.status_code == 404

    async def test_delete_entity_type(self, client: AsyncClient) -> None:
        """Create then DELETE returns 204."""
        unique_name = f"Task_{uuid4().hex[:8]}"
        create_payload = {
            "name": unique_name,
            "description": "Entity for delete test",
            "properties": {},
            "custom_validators": [],
        }

        create_response = await client.post(
            "/schema/entity-types", json=create_payload
        )
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        response = await client.delete(f"/schema/entity-types/{created_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/schema/entity-types/{created_id}")
        assert get_response.status_code == 404

    async def test_delete_entity_type_not_found(self, client: AsyncClient) -> None:
        """DELETE non-existent ID returns 404."""
        non_existent_id = str(uuid4())

        response = await client.delete(f"/schema/entity-types/{non_existent_id}")

        assert response.status_code == 404
