"""Integration tests for Entity CRUD API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.fixture
async def entity_type_id(client: AsyncClient) -> str:
    """Create entity type with required 'title' property and return ID."""
    unique_name = f"Task_{uuid4().hex[:8]}"
    payload = {
        "name": unique_name,
        "description": "Entity type for entity tests",
        "properties": {
            "title": {
                "type": "string",
                "required": True,
                "indexed": True,
            },
            "priority": {
                "type": "integer",
                "required": False,
                "default": 1,
            },
        },
        "custom_validators": [],
    }
    response = await client.post("/schema/entity-types", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


class TestEntityCRUDAPI:
    """Tests for Entity CRUD endpoints."""

    async def test_create_entity(self, client: AsyncClient, entity_type_id: str) -> None:
        """POST /entities returns 201 with created entity and applies defaults."""
        payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "My First Task",
            },
        }

        response = await client.post("/entities", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["type_id"] == entity_type_id
        assert data["version"] == 1
        assert data["properties"]["title"] == "My First Task"
        # Default should be applied
        assert data["properties"]["priority"] == 1
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_entity_validation_error(
        self, client: AsyncClient, entity_type_id: str
    ) -> None:
        """POST with missing required field returns 400 with validation error."""
        payload = {
            "type_id": entity_type_id,
            "properties": {
                # Missing required 'title' field
                "priority": 5,
            },
        }

        response = await client.post("/entities", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "errors" in data
        # Check that the error mentions the 'title' field
        error_fields = [err["field"] for err in data["errors"]]
        assert "title" in error_fields

    async def test_get_entity_by_id(self, client: AsyncClient, entity_type_id: str) -> None:
        """POST then GET by ID returns 200 with entity."""
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Task to Get",
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        response = await client.get(f"/entities/{created_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["properties"]["title"] == "Task to Get"
        assert data["version"] == 1

    async def test_get_entity_not_found(self, client: AsyncClient) -> None:
        """GET non-existent ID returns 404."""
        non_existent_id = str(uuid4())

        response = await client.get(f"/entities/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_list_entities_by_type(self, client: AsyncClient, entity_type_id: str) -> None:
        """Create then list by type_id, verify at least 1 entity."""
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Task to List",
            },
        }
        await client.post("/entities", json=create_payload)

        response = await client.get(f"/entities?type_id={entity_type_id}")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        # Verify all items have the correct type_id
        for item in data["items"]:
            assert item["type_id"] == entity_type_id

    async def test_update_entity(self, client: AsyncClient, entity_type_id: str) -> None:
        """Create, update properties, verify change and version increment."""
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Original Title",
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        created = create_response.json()
        created_id = created["id"]
        assert created["version"] == 1

        update_payload = {
            "properties": {
                "title": "Updated Title",
            },
            "version": 1,
        }

        response = await client.put(f"/entities/{created_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["properties"]["title"] == "Updated Title"
        assert data["version"] == 2

    async def test_update_entity_version_conflict(
        self, client: AsyncClient, entity_type_id: str
    ) -> None:
        """PUT with wrong version returns 409 Conflict."""
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Task for Conflict",
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        created = create_response.json()
        created_id = created["id"]

        # Try to update with wrong version (version 2 when current is 1)
        update_payload = {
            "properties": {
                "title": "Should Fail",
            },
            "version": 2,  # Wrong version
        }

        response = await client.put(f"/entities/{created_id}", json=update_payload)

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data

    async def test_delete_entity(self, client: AsyncClient, entity_type_id: str) -> None:
        """Create then DELETE returns 204."""
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Task to Delete",
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        response = await client.delete(f"/entities/{created_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/entities/{created_id}")
        assert get_response.status_code == 404

    async def test_get_entity_history(self, client: AsyncClient, entity_type_id: str) -> None:
        """Create, update, get history returns 2 records (CREATE, UPDATE)."""
        # Create entity
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "History Test Task",
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        # Update entity
        update_payload = {
            "properties": {
                "title": "Updated History Task",
            },
            "version": 1,
        }
        update_response = await client.put(
            f"/entities/{created_id}", json=update_payload
        )
        assert update_response.status_code == 200

        # Get history
        response = await client.get(f"/entities/{created_id}/history")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify operations in order
        operations = [record["operation"] for record in data]
        assert operations == ["CREATE", "UPDATE"]

        # Verify versions
        versions = [record["version"] for record in data]
        assert versions == [1, 2]


class TestEntityTimeTravelAPI:
    """Tests for Entity Time Travel endpoints."""

    async def test_get_entity_at_timestamp(self, client: AsyncClient, entity_type_id: str) -> None:
        """エンティティ作成 -> 時間記録 -> 更新 -> 過去時点でスナップショット取得."""
        import time
        from datetime import UTC, datetime

        # Create entity
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Original Title",
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        created = create_response.json()
        entity_id = created["id"]

        # 作成直後の時間を記録（スナップショット取得用）
        time.sleep(0.1)  # 少し待って時間差を作る
        snapshot_time = datetime.now(UTC)

        # Update entity
        time.sleep(0.1)  # 更新前に少し待つ
        update_payload = {
            "properties": {
                "title": "Updated Title",
            },
            "version": 1,
        }
        update_response = await client.put(
            f"/entities/{entity_id}", json=update_payload
        )
        assert update_response.status_code == 200

        # 過去時点のスナップショット取得
        timestamp_str = snapshot_time.isoformat()
        response = await client.get(f"/entities/{entity_id}/at/{timestamp_str}")

        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == entity_id
        assert data["version"] == 1
        assert data["properties"]["title"] == "Original Title"
        assert data["is_current"] is False

    async def test_get_entity_diff(self, client: AsyncClient, entity_type_id: str) -> None:
        """エンティティ作成 -> 更新 -> v1とv2の差分取得 -> changes確認."""
        # Create entity
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "First Version",
                "priority": 1,
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        created = create_response.json()
        entity_id = created["id"]

        # Update entity
        update_payload = {
            "properties": {
                "title": "Second Version",
                "priority": 2,
            },
            "version": 1,
        }
        update_response = await client.put(
            f"/entities/{entity_id}", json=update_payload
        )
        assert update_response.status_code == 200

        # Get diff between v1 and v2
        response = await client.get(
            f"/entities/{entity_id}/diff",
            params={"from_version": 1, "to_version": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == entity_id
        assert data["from_version"] == 1
        assert data["to_version"] == 2
        assert data["has_changes"] is True

        # Verify changes
        changes = data["changes"]
        assert len(changes) >= 1  # At least title changed

        # Find title change
        title_change = next((c for c in changes if c["field"] == "title"), None)
        assert title_change is not None
        assert title_change["old_value"] == "First Version"
        assert title_change["new_value"] == "Second Version"
        assert title_change["change_type"] == "modified"

    async def test_get_entity_diff_not_found(self, client: AsyncClient) -> None:
        """存在しないエンティティIDで404."""
        non_existent_id = str(uuid4())

        response = await client.get(
            f"/entities/{non_existent_id}/diff",
            params={"from_version": 1, "to_version": 2},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestEntityRollbackAPI:
    """Tests for Entity Rollback endpoints."""

    async def test_rollback_to_version(self, client: AsyncClient, entity_type_id: str) -> None:
        """エンティティ作成 -> 2回更新 -> version 1 にロールバック -> version 4 として保存."""
        # Create entity (version 1)
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Version 1 Title",
                "priority": 1,
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        entity_id = create_response.json()["id"]
        assert create_response.json()["version"] == 1

        # Update 1 (version 2)
        update1_payload = {
            "properties": {"title": "Version 2 Title", "priority": 2},
            "version": 1,
        }
        update1_response = await client.put(
            f"/entities/{entity_id}", json=update1_payload
        )
        assert update1_response.status_code == 200
        assert update1_response.json()["version"] == 2

        # Update 2 (version 3)
        update2_payload = {
            "properties": {"title": "Version 3 Title", "priority": 3},
            "version": 2,
        }
        update2_response = await client.put(
            f"/entities/{entity_id}", json=update2_payload
        )
        assert update2_response.status_code == 200
        assert update2_response.json()["version"] == 3

        # Rollback to version 1 (should create version 4)
        rollback_payload = {"target_version": 1}
        rollback_response = await client.post(
            f"/entities/{entity_id}/rollback", json=rollback_payload
        )

        assert rollback_response.status_code == 200
        data = rollback_response.json()
        assert data["id"] == entity_id
        assert data["version"] == 4
        assert data["properties"]["title"] == "Version 1 Title"
        assert data["properties"]["priority"] == 1

    async def test_rollback_to_timestamp(self, client: AsyncClient, entity_type_id: str) -> None:
        """エンティティ作成 -> 時間記録 -> 更新 -> 記録した時間にロールバック."""
        import time
        from datetime import UTC, datetime

        # Create entity
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Original Title",
                "priority": 1,
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        entity_id = create_response.json()["id"]

        # 作成直後の時間を記録（ロールバック用）
        time.sleep(0.1)  # 少し待って時間差を作る
        snapshot_time = datetime.now(UTC)

        # Update entity
        time.sleep(0.1)  # 更新前に少し待つ
        update_payload = {
            "properties": {"title": "Updated Title", "priority": 2},
            "version": 1,
        }
        update_response = await client.put(
            f"/entities/{entity_id}", json=update_payload
        )
        assert update_response.status_code == 200
        assert update_response.json()["version"] == 2

        # Rollback to timestamp
        timestamp_str = snapshot_time.isoformat()
        rollback_payload = {"target_time": timestamp_str}
        rollback_response = await client.post(
            f"/entities/{entity_id}/rollback", json=rollback_payload
        )

        assert rollback_response.status_code == 200
        data = rollback_response.json()
        assert data["id"] == entity_id
        assert data["version"] == 3  # New version after rollback
        assert data["properties"]["title"] == "Original Title"
        assert data["properties"]["priority"] == 1

    async def test_rollback_version_not_found(
        self, client: AsyncClient, entity_type_id: str
    ) -> None:
        """存在しないバージョンへのロールバックで 404."""
        # Create entity
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Test Title",
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        entity_id = create_response.json()["id"]

        # Try to rollback to non-existent version
        rollback_payload = {"target_version": 999}
        rollback_response = await client.post(
            f"/entities/{entity_id}/rollback", json=rollback_payload
        )

        assert rollback_response.status_code == 404
        data = rollback_response.json()
        assert "detail" in data

    async def test_rollback_requires_version_or_time(
        self, client: AsyncClient, entity_type_id: str
    ) -> None:
        """target_version も target_time も指定しないで 422 (Pydantic validation)."""
        # Create entity
        create_payload = {
            "type_id": entity_type_id,
            "properties": {
                "title": "Test Title",
            },
        }
        create_response = await client.post("/entities", json=create_payload)
        assert create_response.status_code == 201
        entity_id = create_response.json()["id"]

        # Try to rollback without specifying target_version or target_time
        rollback_payload: dict[str, str | int] = {}
        rollback_response = await client.post(
            f"/entities/{entity_id}/rollback", json=rollback_payload
        )

        assert rollback_response.status_code == 422
