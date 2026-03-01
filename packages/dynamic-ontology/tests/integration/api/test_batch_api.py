"""Integration tests for Batch Entity API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def entity_type_id(client: AsyncClient) -> str:
    """Create entity type for batch tests."""
    unique_name = f"BatchTask_{uuid4().hex[:8]}"
    payload = {
        "name": unique_name,
        "description": "Entity type for batch tests",
        "properties": {
            "title": {"type": "string", "required": True, "indexed": True},
            "priority": {"type": "integer", "required": False, "default": 1},
        },
        "custom_validators": [],
    }
    response = await client.post("/schema/entity-types", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


class TestBatchCreate:
    """Tests for POST /entities/batch endpoint."""

    async def test_batch_create_success(self, client: AsyncClient, entity_type_id: str) -> None:
        """POST /entities/batch creates multiple entities."""
        payload = {"entities": [{"type_id": entity_type_id, "properties": {"title": f"Task {i}"}} for i in range(3)]}

        response = await client.post("/entities/batch", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 3
        assert data["succeeded"] == 3
        assert data["failed"] == 0
        assert len(data["entity_ids"]) == 3
        assert data["errors"] == []

    async def test_batch_create_validation_error(self, client: AsyncClient, entity_type_id: str) -> None:
        """POST /entities/batch fails on validation error (all-or-nothing)."""
        payload = {
            "entities": [
                {"type_id": entity_type_id, "properties": {"title": "Valid"}},
                {"type_id": entity_type_id, "properties": {}},  # Missing required title
            ]
        }

        response = await client.post("/entities/batch", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["failed"] >= 1
        assert len(data["detail"]["errors"]) >= 1

    async def test_batch_create_invalid_type(self, client: AsyncClient) -> None:
        """POST /entities/batch fails on invalid type_id."""
        fake_type_id = str(uuid4())
        payload = {"entities": [{"type_id": fake_type_id, "properties": {"title": "Test"}}]}

        response = await client.post("/entities/batch", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert "not found" in data["detail"]["errors"][0]["message"].lower()

    async def test_batch_create_empty_list(self, client: AsyncClient) -> None:
        """POST /entities/batch with empty list returns 422."""
        payload = {"entities": []}

        response = await client.post("/entities/batch", json=payload)

        assert response.status_code == 422  # Pydantic validation error (min_length=1)


class TestBatchUpdate:
    """Tests for PATCH /entities/batch endpoint."""

    async def test_batch_update_success(self, client: AsyncClient, entity_type_id: str) -> None:
        """PATCH /entities/batch updates multiple entities."""
        # Create entities first
        create_payload = {
            "entities": [{"type_id": entity_type_id, "properties": {"title": f"Original {i}"}} for i in range(3)]
        }
        create_response = await client.post("/entities/batch", json=create_payload)
        assert create_response.status_code == 201
        entity_ids = create_response.json()["entity_ids"]

        # Update all
        update_payload = {
            "updates": [
                {
                    "id": entity_id,
                    "version": 1,
                    "properties": {"title": f"Updated {i}"},
                }
                for i, entity_id in enumerate(entity_ids)
            ]
        }

        response = await client.patch("/entities/batch", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 3
        assert data["succeeded"] == 3

    async def test_batch_update_version_conflict(self, client: AsyncClient, entity_type_id: str) -> None:
        """PATCH /entities/batch fails on version conflict."""
        # Create entity
        create_payload = {"entities": [{"type_id": entity_type_id, "properties": {"title": "Test"}}]}
        create_response = await client.post("/entities/batch", json=create_payload)
        entity_id = create_response.json()["entity_ids"][0]

        # Try to update with wrong version
        update_payload = {"updates": [{"id": entity_id, "version": 999, "properties": {"title": "Updated"}}]}

        response = await client.patch("/entities/batch", json=update_payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert "version" in data["detail"]["errors"][0]["message"].lower()

    async def test_batch_update_not_found(self, client: AsyncClient) -> None:
        """PATCH /entities/batch fails when entity not found."""
        fake_id = str(uuid4())
        update_payload = {"updates": [{"id": fake_id, "version": 1, "properties": {"title": "Test"}}]}

        response = await client.patch("/entities/batch", json=update_payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert "not found" in data["detail"]["errors"][0]["message"].lower()


class TestBatchDelete:
    """Tests for DELETE /entities/batch endpoint."""

    async def test_batch_delete_success(self, client: AsyncClient, entity_type_id: str) -> None:
        """DELETE /entities/batch deletes multiple entities."""
        # Create entities first
        create_payload = {
            "entities": [{"type_id": entity_type_id, "properties": {"title": f"ToDelete {i}"}} for i in range(3)]
        }
        create_response = await client.post("/entities/batch", json=create_payload)
        entity_ids = create_response.json()["entity_ids"]

        # Delete all
        delete_payload = {"entity_ids": entity_ids}

        response = await client.request("DELETE", "/entities/batch", json=delete_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 3
        assert data["succeeded"] == 3

        # Verify deleted
        for entity_id in entity_ids:
            get_response = await client.get(f"/entities/{entity_id}")
            assert get_response.status_code == 404

    async def test_batch_delete_not_found(self, client: AsyncClient) -> None:
        """DELETE /entities/batch fails when entity not found."""
        fake_id = str(uuid4())
        delete_payload = {"entity_ids": [fake_id]}

        response = await client.request("DELETE", "/entities/batch", json=delete_payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert "not found" in data["detail"]["errors"][0]["message"].lower()

    async def test_batch_delete_partial_not_found(self, client: AsyncClient, entity_type_id: str) -> None:
        """DELETE /entities/batch fails if any entity not found (all-or-nothing)."""
        # Create one entity
        create_payload = {"entities": [{"type_id": entity_type_id, "properties": {"title": "Exists"}}]}
        create_response = await client.post("/entities/batch", json=create_payload)
        entity_id = create_response.json()["entity_ids"][0]

        # Try to delete existing + non-existing
        delete_payload = {"entity_ids": [entity_id, str(uuid4())]}

        response = await client.request("DELETE", "/entities/batch", json=delete_payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False

        # Verify existing entity was NOT deleted (rollback)
        get_response = await client.get(f"/entities/{entity_id}")
        assert get_response.status_code == 200
