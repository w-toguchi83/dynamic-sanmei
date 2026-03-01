"""Relationship レスポンスのエンティティ表示名テスト."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestRelationshipDisplayNames:
    """Relationship レスポンスに type_name, display_name が含まれる."""

    @pytest.mark.asyncio
    async def test_create_relationship_includes_display_names(self, client: AsyncClient) -> None:
        """POST /relationships レスポンスに type_name, display_name が含まれる."""
        # Setup: EntityType with display_property
        et_name = f"Node_{uuid4().hex[:8]}"
        et_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "properties": {
                    "title": {"type": "string", "required": True, "indexed": False},
                },
                "display_property": "title",
            },
        )
        assert et_resp.status_code == 201
        et_id = et_resp.json()["id"]

        rt_name = f"links_to_{uuid4().hex[:8]}"
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={"name": rt_name, "directional": True},
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        e1 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"title": "Alice"}},
        )
        assert e1.status_code == 201
        e2 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"title": "Bob"}},
        )
        assert e2.status_code == 201

        rel = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": e1.json()["id"],
                "to_entity_id": e2.json()["id"],
            },
        )
        assert rel.status_code == 201
        rel_data = rel.json()

        assert rel_data["type_name"] == rt_name
        assert rel_data["from_entity_display_name"] == "Alice"
        assert rel_data["to_entity_display_name"] == "Bob"
        assert rel_data["from_entity_type_name"] == et_name
        assert rel_data["to_entity_type_name"] == et_name

    @pytest.mark.asyncio
    async def test_get_relationship_includes_display_names(self, client: AsyncClient) -> None:
        """GET /relationships/{id} レスポンスに type_name, display_name が含まれる."""
        et_name = f"Item_{uuid4().hex[:8]}"
        et_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "properties": {
                    "label": {"type": "string", "required": True, "indexed": False},
                },
                "display_property": "label",
            },
        )
        assert et_resp.status_code == 201
        et_id = et_resp.json()["id"]

        rt_name = f"connects_{uuid4().hex[:8]}"
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={"name": rt_name, "directional": False},
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        e1 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"label": "Alpha"}},
        )
        assert e1.status_code == 201
        e2 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"label": "Beta"}},
        )
        assert e2.status_code == 201

        rel = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": e1.json()["id"],
                "to_entity_id": e2.json()["id"],
            },
        )
        assert rel.status_code == 201
        rel_id = rel.json()["id"]

        # GET the relationship
        get_resp = await client.get(f"/relationships/{rel_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()

        assert data["type_name"] == rt_name
        assert data["from_entity_display_name"] == "Alpha"
        assert data["to_entity_display_name"] == "Beta"
        assert data["from_entity_type_name"] == et_name
        assert data["to_entity_type_name"] == et_name

    @pytest.mark.asyncio
    async def test_entity_relationships_list_includes_display_names(self, client: AsyncClient) -> None:
        """GET /entities/{id}/relationships レスポンスに display_name が含まれる."""
        et_name = f"Doc_{uuid4().hex[:8]}"
        et_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "properties": {
                    "name": {"type": "string", "required": True, "indexed": False},
                },
                "display_property": "name",
            },
        )
        assert et_resp.status_code == 201
        et_id = et_resp.json()["id"]

        rt_name = f"refs_{uuid4().hex[:8]}"
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={"name": rt_name, "directional": True},
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        e1 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"name": "Doc1"}},
        )
        assert e1.status_code == 201
        e2 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"name": "Doc2"}},
        )
        assert e2.status_code == 201

        rel = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": e1.json()["id"],
                "to_entity_id": e2.json()["id"],
            },
        )
        assert rel.status_code == 201

        # List relationships for entity1
        list_resp = await client.get(f"/entities/{e1.json()['id']}/relationships")
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        assert len(items) >= 1

        item = items[0]
        assert item["type_name"] == rt_name
        assert item["from_entity_display_name"] == "Doc1"
        assert item["to_entity_display_name"] == "Doc2"
        assert item["from_entity_type_name"] == et_name
        assert item["to_entity_type_name"] == et_name

    @pytest.mark.asyncio
    async def test_display_name_none_when_no_display_property(self, client: AsyncClient) -> None:
        """display_property 未設定の EntityType では display_name が None."""
        et_name = f"Plain_{uuid4().hex[:8]}"
        et_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "properties": {
                    "value": {"type": "integer", "required": True, "indexed": False},
                },
            },
        )
        assert et_resp.status_code == 201
        et_id = et_resp.json()["id"]

        rt_name = f"pair_{uuid4().hex[:8]}"
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={"name": rt_name, "directional": True},
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        e1 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"value": 42}},
        )
        assert e1.status_code == 201
        e2 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"value": 99}},
        )
        assert e2.status_code == 201

        rel = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": e1.json()["id"],
                "to_entity_id": e2.json()["id"],
            },
        )
        assert rel.status_code == 201
        data = rel.json()

        assert data["type_name"] == rt_name
        assert data["from_entity_display_name"] is None
        assert data["to_entity_display_name"] is None
        # type_name は display_property に関わらず常に含まれる
        assert data["from_entity_type_name"] == et_name
        assert data["to_entity_type_name"] == et_name

    @pytest.mark.asyncio
    async def test_update_relationship_includes_display_names(self, client: AsyncClient) -> None:
        """PUT /relationships/{id} レスポンスに display_name が含まれる."""
        et_name = f"Task_{uuid4().hex[:8]}"
        et_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "properties": {
                    "title": {"type": "string", "required": True, "indexed": False},
                },
                "display_property": "title",
            },
        )
        assert et_resp.status_code == 201
        et_id = et_resp.json()["id"]

        rt_name = f"depends_on_{uuid4().hex[:8]}"
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": rt_name,
                "directional": True,
                "properties": {
                    "weight": {"type": "integer", "required": False, "indexed": False},
                },
            },
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        e1 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"title": "TaskA"}},
        )
        assert e1.status_code == 201
        e2 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {"title": "TaskB"}},
        )
        assert e2.status_code == 201

        rel = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": e1.json()["id"],
                "to_entity_id": e2.json()["id"],
                "properties": {"weight": 5},
            },
        )
        assert rel.status_code == 201
        rel_id = rel.json()["id"]

        # Update the relationship
        update_resp = await client.put(
            f"/relationships/{rel_id}",
            json={"properties": {"weight": 10}, "version": 1},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()

        assert data["type_name"] == rt_name
        assert data["from_entity_display_name"] == "TaskA"
        assert data["to_entity_display_name"] == "TaskB"
        assert data["from_entity_type_name"] == et_name
        assert data["to_entity_type_name"] == et_name
