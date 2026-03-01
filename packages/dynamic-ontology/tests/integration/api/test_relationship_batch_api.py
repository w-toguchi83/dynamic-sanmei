"""Integration tests for Relationship Batch API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def setup(client: AsyncClient) -> dict[str, str]:
    """Create entity type, relationship type, and two entities for batch tests.

    Returns:
        Dict with keys: entity_type_id, relationship_type_id, entity_a_id, entity_b_id, entity_c_id
    """
    suffix = uuid4().hex[:8]

    # Create entity type
    et_payload = {
        "name": f"RelBatchNode_{suffix}",
        "description": "Entity type for relationship batch tests",
        "properties": {
            "name": {"type": "string", "required": True, "indexed": True},
        },
        "custom_validators": [],
    }
    et_resp = await client.post("/schema/entity-types", json=et_payload)
    assert et_resp.status_code == 201
    entity_type_id = et_resp.json()["id"]

    # Create relationship type
    rt_payload = {
        "name": f"rel_batch_link_{suffix}",
        "description": "Relationship type for batch tests",
        "directional": True,
        "properties": {
            "weight": {"type": "integer", "required": False, "default": 1},
        },
        "custom_validators": [],
    }
    rt_resp = await client.post("/schema/relationship-types", json=rt_payload)
    assert rt_resp.status_code == 201
    relationship_type_id = rt_resp.json()["id"]

    # Create three entities
    entities = []
    for label in ["A", "B", "C"]:
        e_payload = {
            "type_id": entity_type_id,
            "properties": {"name": f"Node {label} {suffix}"},
        }
        e_resp = await client.post("/entities", json=e_payload)
        assert e_resp.status_code == 201
        entities.append(e_resp.json()["id"])

    return {
        "entity_type_id": entity_type_id,
        "relationship_type_id": relationship_type_id,
        "entity_a_id": entities[0],
        "entity_b_id": entities[1],
        "entity_c_id": entities[2],
    }


class TestRelationshipBatchCreate:
    """Tests for POST /relationships/batch endpoint."""

    async def test_batch_create_success(self, client: AsyncClient, setup: dict[str, str]) -> None:
        """POST /relationships/batch creates multiple relationships."""
        payload = {
            "relationships": [
                {
                    "type_id": setup["relationship_type_id"],
                    "from_entity_id": setup["entity_a_id"],
                    "to_entity_id": setup["entity_b_id"],
                    "properties": {"weight": 10},
                },
                {
                    "type_id": setup["relationship_type_id"],
                    "from_entity_id": setup["entity_a_id"],
                    "to_entity_id": setup["entity_c_id"],
                    "properties": {"weight": 20},
                },
            ]
        }

        response = await client.post("/relationships/batch", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2
        assert data["succeeded"] == 2
        assert data["failed"] == 0
        assert len(data["entity_ids"]) == 2
        assert data["errors"] == []

    async def test_batch_create_invalid_type(
        self, client: AsyncClient, setup: dict[str, str]
    ) -> None:
        """POST /relationships/batch fails on non-existent relationship type."""
        fake_type_id = str(uuid4())
        payload = {
            "relationships": [
                {
                    "type_id": fake_type_id,
                    "from_entity_id": setup["entity_a_id"],
                    "to_entity_id": setup["entity_b_id"],
                    "properties": {},
                },
            ]
        }

        response = await client.post("/relationships/batch", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert "not found" in data["detail"]["errors"][0]["message"].lower()

    async def test_batch_create_invalid_entity(
        self, client: AsyncClient, setup: dict[str, str]
    ) -> None:
        """POST /relationships/batch fails on non-existent from_entity."""
        fake_entity_id = str(uuid4())
        payload = {
            "relationships": [
                {
                    "type_id": setup["relationship_type_id"],
                    "from_entity_id": fake_entity_id,
                    "to_entity_id": setup["entity_b_id"],
                    "properties": {},
                },
            ]
        }

        response = await client.post("/relationships/batch", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert "not found" in data["detail"]["errors"][0]["message"].lower()


class TestRelationshipBatchUpdate:
    """Tests for PATCH /relationships/batch endpoint."""

    async def test_batch_update_success(self, client: AsyncClient, setup: dict[str, str]) -> None:
        """PATCH /relationships/batch updates multiple relationships."""
        # Create relationships first
        create_payload = {
            "relationships": [
                {
                    "type_id": setup["relationship_type_id"],
                    "from_entity_id": setup["entity_a_id"],
                    "to_entity_id": setup["entity_b_id"],
                    "properties": {"weight": 1},
                },
                {
                    "type_id": setup["relationship_type_id"],
                    "from_entity_id": setup["entity_a_id"],
                    "to_entity_id": setup["entity_c_id"],
                    "properties": {"weight": 2},
                },
            ]
        }
        create_resp = await client.post(
            "/relationships/batch", json=create_payload
        )
        assert create_resp.status_code == 201
        rel_ids = create_resp.json()["entity_ids"]

        # Batch update
        update_payload = {
            "updates": [
                {
                    "id": rel_ids[0],
                    "version": 1,
                    "properties": {"weight": 100},
                },
                {
                    "id": rel_ids[1],
                    "version": 1,
                    "properties": {"weight": 200},
                },
            ]
        }

        response = await client.patch("/relationships/batch", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2
        assert data["succeeded"] == 2

    async def test_batch_update_version_conflict(
        self, client: AsyncClient, setup: dict[str, str]
    ) -> None:
        """PATCH /relationships/batch fails on version conflict."""
        # Create a relationship
        create_payload = {
            "relationships": [
                {
                    "type_id": setup["relationship_type_id"],
                    "from_entity_id": setup["entity_a_id"],
                    "to_entity_id": setup["entity_b_id"],
                    "properties": {"weight": 1},
                },
            ]
        }
        create_resp = await client.post(
            "/relationships/batch", json=create_payload
        )
        assert create_resp.status_code == 201
        rel_id = create_resp.json()["entity_ids"][0]

        # Try to update with wrong version
        update_payload = {
            "updates": [
                {
                    "id": rel_id,
                    "version": 999,
                    "properties": {"weight": 50},
                },
            ]
        }

        response = await client.patch("/relationships/batch", json=update_payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert "version" in data["detail"]["errors"][0]["message"].lower()


class TestRelationshipBatchDelete:
    """Tests for DELETE /relationships/batch endpoint."""

    async def test_batch_delete_success(self, client: AsyncClient, setup: dict[str, str]) -> None:
        """DELETE /relationships/batch deletes multiple relationships."""
        # Create relationships first
        create_payload = {
            "relationships": [
                {
                    "type_id": setup["relationship_type_id"],
                    "from_entity_id": setup["entity_a_id"],
                    "to_entity_id": setup["entity_b_id"],
                    "properties": {},
                },
                {
                    "type_id": setup["relationship_type_id"],
                    "from_entity_id": setup["entity_a_id"],
                    "to_entity_id": setup["entity_c_id"],
                    "properties": {},
                },
            ]
        }
        create_resp = await client.post(
            "/relationships/batch", json=create_payload
        )
        assert create_resp.status_code == 201
        rel_ids = create_resp.json()["entity_ids"]

        # Batch delete
        delete_payload = {"relationship_ids": rel_ids}

        response = await client.request(
            "DELETE", "/relationships/batch", json=delete_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2
        assert data["succeeded"] == 2

        # Verify deleted
        for rel_id in rel_ids:
            get_resp = await client.get(f"/relationships/{rel_id}")
            assert get_resp.status_code == 404

    async def test_batch_delete_not_found(self, client: AsyncClient) -> None:
        """DELETE /relationships/batch fails when relationship not found."""
        fake_id = str(uuid4())
        delete_payload = {"relationship_ids": [fake_id]}

        response = await client.request(
            "DELETE", "/relationships/batch", json=delete_payload
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert "not found" in data["detail"]["errors"][0]["message"].lower()
