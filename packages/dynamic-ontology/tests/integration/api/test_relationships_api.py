"""Integration tests for RelationshipType and Relationship CRUD API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def setup_data(client: AsyncClient) -> dict[str, str]:
    """Create entity type, 2 entities, and relationship type for testing.

    Returns:
        Dictionary with entity_type_id, entity1_id, entity2_id, relationship_type_id.
    """
    # Create entity type
    unique_name = f"Person_{uuid4().hex[:8]}"
    entity_type_payload = {
        "name": unique_name,
        "description": "Person entity type for relationship tests",
        "properties": {
            "name": {
                "type": "string",
                "required": True,
                "indexed": True,
            },
        },
        "custom_validators": [],
    }
    et_response = await client.post("/schema/entity-types", json=entity_type_payload)
    assert et_response.status_code == 201
    entity_type_id = et_response.json()["id"]

    # Create entity 1
    entity1_payload = {
        "type_id": entity_type_id,
        "properties": {"name": "Alice"},
    }
    e1_response = await client.post("/entities", json=entity1_payload)
    assert e1_response.status_code == 201
    entity1_id = e1_response.json()["id"]

    # Create entity 2
    entity2_payload = {
        "type_id": entity_type_id,
        "properties": {"name": "Bob"},
    }
    e2_response = await client.post("/entities", json=entity2_payload)
    assert e2_response.status_code == 201
    entity2_id = e2_response.json()["id"]

    # Create relationship type
    rt_unique_name = f"knows_{uuid4().hex[:8]}"
    relationship_type_payload = {
        "name": rt_unique_name,
        "description": "Person knows another person",
        "directional": True,
        "properties": {
            "since": {
                "type": "integer",
                "required": False,
            },
        },
        "custom_validators": [],
    }
    rt_response = await client.post("/schema/relationship-types", json=relationship_type_payload)
    assert rt_response.status_code == 201
    relationship_type_id = rt_response.json()["id"]

    return {
        "entity_type_id": entity_type_id,
        "entity1_id": entity1_id,
        "entity2_id": entity2_id,
        "relationship_type_id": relationship_type_id,
    }


class TestRelationshipTypeCRUDAPI:
    """Tests for RelationshipType CRUD endpoints."""

    async def test_create_relationship_type(self, client: AsyncClient) -> None:
        """POST /schema/relationship-types returns 201 with created relationship type."""
        unique_name = f"follows_{uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "description": "User follows another user",
            "directional": True,
            "properties": {
                "since": {
                    "type": "date",
                    "required": False,
                },
            },
            "custom_validators": [],
        }

        response = await client.post("/schema/relationship-types", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == unique_name
        assert data["description"] == "User follows another user"
        assert data["directional"] is True
        assert "since" in data["properties"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_list_relationship_types(self, client: AsyncClient) -> None:
        """POST then GET list returns 200 with at least 1 item."""
        unique_name = f"likes_{uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "description": "User likes something",
            "directional": True,
            "properties": {},
            "custom_validators": [],
        }
        await client.post("/schema/relationship-types", json=payload)

        response = await client.get("/schema/relationship-types")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Verify structure
        for item in data:
            assert "id" in item
            assert "name" in item
            assert "directional" in item

    async def test_get_relationship_type_by_id(self, client: AsyncClient) -> None:
        """POST then GET by ID returns 200 with relationship type."""
        unique_name = f"owns_{uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "description": "User owns something",
            "directional": True,
            "properties": {},
            "custom_validators": [],
        }
        create_response = await client.post("/schema/relationship-types", json=payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        response = await client.get(f"/schema/relationship-types/{created_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["name"] == unique_name

    async def test_get_relationship_type_not_found(self, client: AsyncClient) -> None:
        """GET non-existent ID returns 404."""
        non_existent_id = str(uuid4())

        response = await client.get(f"/schema/relationship-types/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_delete_relationship_type(self, client: AsyncClient) -> None:
        """POST then DELETE returns 204."""
        unique_name = f"manages_{uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "description": "Manager manages employee",
            "directional": True,
            "properties": {},
            "custom_validators": [],
        }
        create_response = await client.post("/schema/relationship-types", json=payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        response = await client.delete(f"/schema/relationship-types/{created_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/schema/relationship-types/{created_id}")
        assert get_response.status_code == 404

    async def test_update_relationship_type(self, client: AsyncClient) -> None:
        """PUT /schema/relationship-types/{id} returns 200 with updated relationship type."""
        unique_name = f"mentors_{uuid4().hex[:8]}"
        create_payload = {
            "name": unique_name,
            "description": "Original description",
            "directional": True,
            "properties": {
                "weight": {
                    "type": "integer",
                    "required": False,
                },
            },
            "custom_validators": [],
        }
        create_response = await client.post("/schema/relationship-types", json=create_payload)
        assert create_response.status_code == 201
        created = create_response.json()
        created_id = created["id"]

        update_payload = {
            "description": "Updated description",
            "directional": False,
        }

        response = await client.put(f"/schema/relationship-types/{created_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["name"] == unique_name
        assert data["description"] == "Updated description"
        assert data["directional"] is False
        assert "weight" in data["properties"]
        assert data["created_at"] == created["created_at"]
        assert data["updated_at"] != created["updated_at"]

    async def test_update_relationship_type_not_found(self, client: AsyncClient) -> None:
        """PUT non-existent ID returns 404."""
        non_existent_id = str(uuid4())
        update_payload = {
            "description": "Does not matter",
        }

        response = await client.put(f"/schema/relationship-types/{non_existent_id}", json=update_payload)

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_update_relationship_type_duplicate_name(self, client: AsyncClient) -> None:
        """PUT with duplicate name returns 400."""
        name_a = f"rel_a_{uuid4().hex[:8]}"
        name_b = f"rel_b_{uuid4().hex[:8]}"

        payload_a = {
            "name": name_a,
            "description": "Relationship type A",
            "directional": True,
            "properties": {},
            "custom_validators": [],
        }
        await client.post("/schema/relationship-types", json=payload_a)

        payload_b = {
            "name": name_b,
            "description": "Relationship type B",
            "directional": True,
            "properties": {},
            "custom_validators": [],
        }
        create_b_response = await client.post("/schema/relationship-types", json=payload_b)
        assert create_b_response.status_code == 201
        id_b = create_b_response.json()["id"]

        # Try to rename B to A's name
        update_payload = {
            "name": name_a,
        }

        response = await client.put(f"/schema/relationship-types/{id_b}", json=update_payload)

        assert response.status_code == 400

    async def test_update_relationship_type_properties(self, client: AsyncClient) -> None:
        """PUT with new properties fully replaces old properties."""
        unique_name = f"supervises_{uuid4().hex[:8]}"
        create_payload = {
            "name": unique_name,
            "description": "Supervision relationship",
            "directional": True,
            "properties": {
                "old_prop": {
                    "type": "string",
                    "required": False,
                },
            },
            "custom_validators": [],
        }
        create_response = await client.post("/schema/relationship-types", json=create_payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        update_payload = {
            "properties": {
                "new_prop": {
                    "type": "integer",
                    "required": True,
                },
            },
        }

        response = await client.put(
            f"/schema/relationship-types/{created_id}?force=true",
            json=update_payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert "new_prop" in data["properties"]
        assert "old_prop" not in data["properties"]
        assert data["properties"]["new_prop"]["type"] == "integer"


class TestRelationshipCRUDAPI:
    """Tests for Relationship CRUD endpoints."""

    async def test_create_relationship(self, client: AsyncClient, setup_data: dict[str, str]) -> None:
        """POST /relationships returns 201 with created relationship."""
        payload = {
            "type_id": setup_data["relationship_type_id"],
            "from_entity_id": setup_data["entity1_id"],
            "to_entity_id": setup_data["entity2_id"],
            "properties": {"since": 2020},
        }

        response = await client.post("/relationships", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["type_id"] == setup_data["relationship_type_id"]
        assert data["from_entity_id"] == setup_data["entity1_id"]
        assert data["to_entity_id"] == setup_data["entity2_id"]
        assert data["version"] == 1
        assert data["properties"]["since"] == 2020
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_relationship_by_id(self, client: AsyncClient, setup_data: dict[str, str]) -> None:
        """POST then GET by ID returns 200 with relationship."""
        create_payload = {
            "type_id": setup_data["relationship_type_id"],
            "from_entity_id": setup_data["entity1_id"],
            "to_entity_id": setup_data["entity2_id"],
            "properties": {},
        }
        create_response = await client.post("/relationships", json=create_payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        response = await client.get(f"/relationships/{created_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["from_entity_id"] == setup_data["entity1_id"]
        assert data["to_entity_id"] == setup_data["entity2_id"]

    async def test_get_relationship_not_found(self, client: AsyncClient) -> None:
        """GET non-existent ID returns 404."""
        non_existent_id = str(uuid4())

        response = await client.get(f"/relationships/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_get_entity_relationships_outgoing(self, client: AsyncClient, setup_data: dict[str, str]) -> None:
        """Create relationship, GET /entities/{id}/relationships?direction=outgoing returns relationship."""
        # Create relationship from entity1 to entity2
        create_payload = {
            "type_id": setup_data["relationship_type_id"],
            "from_entity_id": setup_data["entity1_id"],
            "to_entity_id": setup_data["entity2_id"],
            "properties": {},
        }
        await client.post("/relationships", json=create_payload)

        # Get outgoing relationships for entity1
        response = await client.get(f"/entities/{setup_data['entity1_id']}/relationships?direction=outgoing")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        # Verify at least one relationship has entity1 as from_entity
        from_entity_ids = [r["from_entity_id"] for r in data["items"]]
        assert setup_data["entity1_id"] in from_entity_ids

    async def test_get_entity_relationships_incoming(self, client: AsyncClient, setup_data: dict[str, str]) -> None:
        """Create relationship, GET /entities/{id}/relationships?direction=incoming returns relationship."""
        # Create relationship from entity1 to entity2
        create_payload = {
            "type_id": setup_data["relationship_type_id"],
            "from_entity_id": setup_data["entity1_id"],
            "to_entity_id": setup_data["entity2_id"],
            "properties": {},
        }
        await client.post("/relationships", json=create_payload)

        # Get incoming relationships for entity2
        response = await client.get(f"/entities/{setup_data['entity2_id']}/relationships?direction=incoming")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        # Verify at least one relationship has entity2 as to_entity
        to_entity_ids = [r["to_entity_id"] for r in data["items"]]
        assert setup_data["entity2_id"] in to_entity_ids

    async def test_get_entity_relationships_with_type_filter(
        self, client: AsyncClient, setup_data: dict[str, str]
    ) -> None:
        """Create relationship, filter by type_id."""
        create_payload = {
            "type_id": setup_data["relationship_type_id"],
            "from_entity_id": setup_data["entity1_id"],
            "to_entity_id": setup_data["entity2_id"],
            "properties": {},
        }
        await client.post("/relationships", json=create_payload)

        # Get relationships filtered by type
        response = await client.get(
            f"/entities/{setup_data['entity1_id']}/relationships?type_id={setup_data['relationship_type_id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        # Verify all relationships have the correct type
        for rel in data["items"]:
            assert rel["type_id"] == setup_data["relationship_type_id"]

    async def test_update_relationship(self, client: AsyncClient, setup_data: dict[str, str]) -> None:
        """Create, update properties, verify change and version increment."""
        create_payload = {
            "type_id": setup_data["relationship_type_id"],
            "from_entity_id": setup_data["entity1_id"],
            "to_entity_id": setup_data["entity2_id"],
            "properties": {"since": 2019},
        }
        create_response = await client.post("/relationships", json=create_payload)
        assert create_response.status_code == 201
        created = create_response.json()
        created_id = created["id"]
        assert created["version"] == 1

        update_payload = {
            "properties": {"since": 2020},
            "version": 1,
        }

        response = await client.put(f"/relationships/{created_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["properties"]["since"] == 2020
        assert data["version"] == 2

    async def test_update_relationship_version_conflict(self, client: AsyncClient, setup_data: dict[str, str]) -> None:
        """PUT with wrong version returns 409 Conflict."""
        create_payload = {
            "type_id": setup_data["relationship_type_id"],
            "from_entity_id": setup_data["entity1_id"],
            "to_entity_id": setup_data["entity2_id"],
            "properties": {},
        }
        create_response = await client.post("/relationships", json=create_payload)
        assert create_response.status_code == 201
        created = create_response.json()
        created_id = created["id"]

        # Try to update with wrong version
        update_payload = {
            "properties": {"since": 2021},
            "version": 2,  # Wrong version, current is 1
        }

        response = await client.put(f"/relationships/{created_id}", json=update_payload)

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data

    async def test_delete_relationship(self, client: AsyncClient, setup_data: dict[str, str]) -> None:
        """Create then DELETE returns 204."""
        create_payload = {
            "type_id": setup_data["relationship_type_id"],
            "from_entity_id": setup_data["entity1_id"],
            "to_entity_id": setup_data["entity2_id"],
            "properties": {},
        }
        create_response = await client.post("/relationships", json=create_payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        response = await client.delete(f"/relationships/{created_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/relationships/{created_id}")
        assert get_response.status_code == 404

    async def test_get_entity_relationships_entity_not_found(self, client: AsyncClient) -> None:
        """GET relationships for non-existent entity returns 404."""
        non_existent_id = str(uuid4())

        response = await client.get(f"/entities/{non_existent_id}/relationships")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
