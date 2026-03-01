"""重複リレーション制約の E2E 統合テスト."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _create_entity_type(client: AsyncClient, name_suffix: str) -> dict[str, str]:
    """テスト用エンティティタイプを作成."""
    resp = await client.post(
        "/schema/entity-types",
        json={
            "name": f"DupTest_{name_suffix}_{uuid4().hex[:8]}",
            "description": "Entity type for duplicate relationship tests",
            "properties": {
                "name": {
                    "type": "string",
                    "required": True,
                    "indexed": True,
                },
            },
            "custom_validators": [],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_entity(client: AsyncClient, type_id: str) -> dict[str, str]:
    """テスト用エンティティを作成."""
    resp = await client.post(
        "/entities",
        json={
            "type_id": type_id,
            "properties": {"name": f"node_{uuid4().hex[:8]}"},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_relationship_type(
    client: AsyncClient,
    name_suffix: str,
    *,
    allow_duplicates: bool = True,
    directional: bool = True,
) -> dict[str, object]:
    """テスト用リレーションシップタイプを作成."""
    resp = await client.post(
        "/schema/relationship-types",
        json={
            "name": f"rt_{name_suffix}_{uuid4().hex[:8]}",
            "description": "Relationship type for duplicate tests",
            "directional": directional,
            "allow_duplicates": allow_duplicates,
            "properties": {},
            "custom_validators": [],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
class TestDuplicateRelationshipConstraint:
    """allow_duplicates=False の重複制約テスト."""

    async def test_duplicate_rejected_409(self, client: AsyncClient) -> None:
        """同一ペアの2回目の作成が 409 で拒否される."""
        et = await _create_entity_type(client, "dup")
        e1 = await _create_entity(client, et["id"])
        e2 = await _create_entity(client, et["id"])
        rt = await _create_relationship_type(client, "dup", allow_duplicates=False)

        # 1回目: 成功
        resp1 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp1.status_code == 201

        # 2回目: 409 Conflict
        resp2 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp2.status_code == 409

    async def test_duplicate_allowed_when_flag_true(self, client: AsyncClient) -> None:
        """allow_duplicates=True（デフォルト）なら重複可能."""
        et = await _create_entity_type(client, "dup_ok")
        e1 = await _create_entity(client, et["id"])
        e2 = await _create_entity(client, et["id"])
        rt = await _create_relationship_type(client, "dup_ok", allow_duplicates=True)

        resp1 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp2.status_code == 201

    async def test_non_directional_reverse_duplicate_rejected(self, client: AsyncClient) -> None:
        """directional=False で (A->B) 後に (B->A) が 409 で拒否される."""
        et = await _create_entity_type(client, "nd_dup")
        e1 = await _create_entity(client, et["id"])
        e2 = await _create_entity(client, et["id"])
        rt = await _create_relationship_type(client, "nd_dup", allow_duplicates=False, directional=False)

        resp1 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp1.status_code == 201

        # 逆方向: 409
        resp2 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e2["id"],
                "to_entity_id": e1["id"],
                "properties": {},
            },
        )
        assert resp2.status_code == 409

    async def test_directional_reverse_not_duplicate(self, client: AsyncClient) -> None:
        """directional=True では (A->B) と (B->A) は別のリレーション."""
        et = await _create_entity_type(client, "dir_rev")
        e1 = await _create_entity(client, et["id"])
        e2 = await _create_entity(client, et["id"])
        rt = await _create_relationship_type(client, "dir_rev", allow_duplicates=False, directional=True)

        resp1 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp1.status_code == 201

        # 逆方向: directional=True なので許可
        resp2 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e2["id"],
                "to_entity_id": e1["id"],
                "properties": {},
            },
        )
        assert resp2.status_code == 201

    async def test_different_type_not_duplicate(self, client: AsyncClient) -> None:
        """異なるリレーションシップタイプなら同一ペアでも許可."""
        et = await _create_entity_type(client, "diff_type")
        e1 = await _create_entity(client, et["id"])
        e2 = await _create_entity(client, et["id"])
        rt1 = await _create_relationship_type(client, "dt1", allow_duplicates=False)
        rt2 = await _create_relationship_type(client, "dt2", allow_duplicates=False)

        resp1 = await client.post(
            "/relationships",
            json={
                "type_id": rt1["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            "/relationships",
            json={
                "type_id": rt2["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp2.status_code == 201

    async def test_batch_create_duplicate_rejected(self, client: AsyncClient) -> None:
        """バッチ作成でも重複が拒否される."""
        et = await _create_entity_type(client, "batch_dup")
        e1 = await _create_entity(client, et["id"])
        e2 = await _create_entity(client, et["id"])
        rt = await _create_relationship_type(client, "batch_dup", allow_duplicates=False)

        # 1件目を先に作成
        resp1 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp1.status_code == 201

        # バッチで同じペアを作成 -> 400 (BatchOperationError)
        resp = await client.post(
            "/relationships/batch",
            json={
                "relationships": [
                    {
                        "type_id": rt["id"],
                        "from_entity_id": e1["id"],
                        "to_entity_id": e2["id"],
                        "properties": {},
                    },
                ],
            },
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["detail"]["success"] is False
        assert "duplicate" in data["detail"]["errors"][0]["message"].lower()

    async def test_batch_create_intra_batch_duplicate_rejected(self, client: AsyncClient) -> None:
        """バッチ内で同一ペアが2回指定された場合もエラー."""
        et = await _create_entity_type(client, "intra_dup")
        e1 = await _create_entity(client, et["id"])
        e2 = await _create_entity(client, et["id"])
        rt = await _create_relationship_type(client, "intra_dup", allow_duplicates=False)

        resp = await client.post(
            "/relationships/batch",
            json={
                "relationships": [
                    {
                        "type_id": rt["id"],
                        "from_entity_id": e1["id"],
                        "to_entity_id": e2["id"],
                        "properties": {},
                    },
                    {
                        "type_id": rt["id"],
                        "from_entity_id": e1["id"],
                        "to_entity_id": e2["id"],
                        "properties": {},
                    },
                ],
            },
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["detail"]["success"] is False
        assert "duplicate" in data["detail"]["errors"][0]["message"].lower()

    async def test_relationship_type_response_includes_allow_duplicates(self, client: AsyncClient) -> None:
        """レスポンスに allow_duplicates フィールドが含まれる."""
        rt = await _create_relationship_type(client, "resp_check", allow_duplicates=False)
        assert rt["allow_duplicates"] is False

        # GET で確認
        resp = await client.get(f"/schema/relationship-types/{rt['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["allow_duplicates"] is False

    async def test_default_allow_duplicates_is_true(self, client: AsyncClient) -> None:
        """allow_duplicates を指定しない場合、デフォルトで True."""
        resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": f"rt_default_{uuid4().hex[:8]}",
                "description": "Default allow_duplicates test",
                "directional": True,
                "properties": {},
                "custom_validators": [],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["allow_duplicates"] is True

    async def test_delete_then_recreate_allowed(self, client: AsyncClient) -> None:
        """削除後に同じペアで再作成が可能."""
        et = await _create_entity_type(client, "del_recreate")
        e1 = await _create_entity(client, et["id"])
        e2 = await _create_entity(client, et["id"])
        rt = await _create_relationship_type(client, "del_recreate", allow_duplicates=False)

        # 作成
        resp1 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp1.status_code == 201
        rel_id = resp1.json()["id"]

        # 削除
        resp_del = await client.delete(f"/relationships/{rel_id}")
        assert resp_del.status_code == 204

        # 再作成: 削除済みなので成功するはず
        resp2 = await client.post(
            "/relationships",
            json={
                "type_id": rt["id"],
                "from_entity_id": e1["id"],
                "to_entity_id": e2["id"],
                "properties": {},
            },
        )
        assert resp2.status_code == 201
