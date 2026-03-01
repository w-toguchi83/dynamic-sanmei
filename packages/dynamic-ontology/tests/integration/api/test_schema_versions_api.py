"""Integration tests for SchemaVersion API endpoints.

エンティティタイプ / リレーションシップタイプのスキーマバージョン
一覧取得・個別取得・差分取得の API テスト。
"""

import json
from datetime import UTC, datetime
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.domain.models.schema_version import CompatibilityLevel, TypeKind


async def _insert_schema_version(
    db_session: AsyncSession,
    *,
    type_id: str,
    type_kind: TypeKind,
    version: int,
    schema_definition: dict[str, object],
    compatibility: CompatibilityLevel | None = None,
    change_summary: dict[str, object] | None = None,
    created_by: str | None = None,
    previous_version_id: str | None = None,
    namespace_id: str,
) -> str:
    """テスト用にスキーマバージョンを直接 DB に挿入する。"""
    sv_id = str(uuid4())
    query = text("""
        INSERT INTO do_schema_versions (
            id, type_kind, type_id, version, schema_definition,
            previous_version_id, compatibility, change_summary,
            created_at, created_by, namespace_id
        ) VALUES (
            :id, :type_kind, :type_id, :version, :schema_definition,
            :previous_version_id, :compatibility, :change_summary,
            :created_at, :created_by, :namespace_id
        )
    """)
    await db_session.execute(
        query,
        {
            "id": sv_id,
            "type_kind": type_kind.value,
            "type_id": type_id,
            "version": version,
            "schema_definition": json.dumps(schema_definition),
            "previous_version_id": previous_version_id,
            "compatibility": compatibility.value if compatibility else None,
            "change_summary": json.dumps(change_summary) if change_summary else None,
            "created_at": datetime.now(UTC),
            "created_by": created_by,
            "namespace_id": namespace_id,
        },
    )
    await db_session.commit()
    return sv_id


class TestEntityTypeVersionsAPI:
    """エンティティタイプのスキーマバージョン API テスト。"""

    async def test_list_versions_empty(self, client: AsyncClient) -> None:
        """バージョンが存在しない場合は空リストを返す。"""
        non_existent_id = str(uuid4())
        response = await client.get(f"/schema/entity-types/{non_existent_id}/versions")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_versions_with_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_namespace_id: str,
    ) -> None:
        """バージョンが存在する場合はバージョン昇順でリストを返す。"""
        # エンティティタイプを作成
        et_name = f"VersionTest_{uuid4().hex[:8]}"
        create_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "description": "test",
                "properties": {"title": {"type": "string", "required": True}},
                "custom_validators": [],
            },
        )
        assert create_resp.status_code == 201
        et_id = create_resp.json()["id"]

        # CREATE で v1 が自動記録されるため、v2 のみ手動挿入
        result = await db_session.execute(
            text("SELECT id FROM do_schema_versions WHERE type_id = :type_id AND version = 1"),
            {"type_id": et_id},
        )
        sv1_id = str(result.scalar_one())

        schema_v2 = {
            "properties": {
                "title": {"type": "string", "required": True},
                "body": {"type": "string", "required": False},
            }
        }
        await _insert_schema_version(
            db_session,
            type_id=et_id,
            type_kind=TypeKind.ENTITY_TYPE,
            version=2,
            schema_definition=schema_v2,
            compatibility=CompatibilityLevel.BACKWARD,
            previous_version_id=sv1_id,
            created_by="test-user",
            namespace_id=test_namespace_id,
        )

        response = await client.get(f"/schema/entity-types/{et_id}/versions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["version"] == 1
        assert data[1]["version"] == 2
        assert data[0]["type_kind"] == "entity_type"
        assert data[0]["type_id"] == et_id
        assert data[1]["compatibility"] == "backward"

    async def test_get_specific_version(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_namespace_id: str,
    ) -> None:
        """特定バージョンを取得できる。"""
        et_name = f"VersionGet_{uuid4().hex[:8]}"
        create_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "description": "",
                "properties": {},
                "custom_validators": [],
            },
        )
        assert create_resp.status_code == 201
        et_id = create_resp.json()["id"]

        # CREATE で v1 が自動記録されるため、v2 を手動挿入して取得テスト
        result = await db_session.execute(
            text("SELECT id FROM do_schema_versions WHERE type_id = :type_id AND version = 1"),
            {"type_id": et_id},
        )
        sv1_id = str(result.scalar_one())

        schema_def = {"properties": {"name": {"type": "string", "required": True}}}
        await _insert_schema_version(
            db_session,
            type_id=et_id,
            type_kind=TypeKind.ENTITY_TYPE,
            version=2,
            schema_definition=schema_def,
            created_by="tester",
            previous_version_id=sv1_id,
            namespace_id=test_namespace_id,
        )

        response = await client.get(f"/schema/entity-types/{et_id}/versions/2")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == 2
        assert data["type_id"] == et_id
        assert data["created_by"] == "tester"
        assert data["schema_definition"]["properties"]["name"]["type"] == "string"

    async def test_get_version_not_found(self, client: AsyncClient) -> None:
        """存在しないバージョンを取得すると 404 を返す。"""
        non_existent_id = str(uuid4())
        response = await client.get(f"/schema/entity-types/{non_existent_id}/versions/999")
        assert response.status_code == 404

    async def test_diff_between_versions(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_namespace_id: str,
    ) -> None:
        """2つのバージョン間の差分を正しく計算する。"""
        et_name = f"DiffTest_{uuid4().hex[:8]}"
        create_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "description": "",
                "properties": {},
                "custom_validators": [],
            },
        )
        assert create_resp.status_code == 201
        et_id = create_resp.json()["id"]

        # CREATE で v1 が自動記録されるため、v2 と v3 を手動挿入
        result = await db_session.execute(
            text("SELECT id FROM do_schema_versions WHERE type_id = :type_id AND version = 1"),
            {"type_id": et_id},
        )
        sv1_id = str(result.scalar_one())

        schema_v2 = {"properties": {"title": {"type": "string", "required": True}}}
        sv2_id = await _insert_schema_version(
            db_session,
            type_id=et_id,
            type_kind=TypeKind.ENTITY_TYPE,
            version=2,
            schema_definition=schema_v2,
            previous_version_id=sv1_id,
            namespace_id=test_namespace_id,
        )
        schema_v3 = {
            "properties": {
                "title": {"type": "string", "required": True},
                "body": {"type": "string", "required": False},
            }
        }
        await _insert_schema_version(
            db_session,
            type_id=et_id,
            type_kind=TypeKind.ENTITY_TYPE,
            version=3,
            schema_definition=schema_v3,
            previous_version_id=sv2_id,
            namespace_id=test_namespace_id,
        )

        response = await client.get(
            f"/schema/entity-types/{et_id}/diff",
            params={"from_version": 2, "to_version": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert "body" in data["added_fields"]
        assert data["removed_fields"] == []
        assert data["modified_fields"] == {}
        assert data["compatibility"] == "backward"

    async def test_diff_with_nonexistent_version(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_namespace_id: str,
    ) -> None:
        """差分取得で存在しないバージョンを指定すると 404 を返す。"""
        et_name = f"DiffNotFound_{uuid4().hex[:8]}"
        create_resp = await client.post(
            "/schema/entity-types",
            json={
                "name": et_name,
                "description": "",
                "properties": {},
                "custom_validators": [],
            },
        )
        assert create_resp.status_code == 201
        et_id = create_resp.json()["id"]

        # CREATE で v1 が自動記録されるため、手動挿入不要

        # from_version は存在するが to_version は存在しない
        response = await client.get(
            f"/schema/entity-types/{et_id}/diff",
            params={"from_version": 1, "to_version": 99},
        )
        assert response.status_code == 404


class TestRelationshipTypeVersionsAPI:
    """リレーションシップタイプのスキーマバージョン API テスト。"""

    async def test_list_versions_empty(self, client: AsyncClient) -> None:
        """バージョンが存在しない場合は空リストを返す。"""
        non_existent_id = str(uuid4())
        response = await client.get(f"/schema/relationship-types/{non_existent_id}/versions")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_versions_with_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_namespace_id: str,
    ) -> None:
        """リレーションシップタイプのバージョン一覧を取得する。"""
        # リレーションシップタイプを作成
        rt_name = f"RTVersion_{uuid4().hex[:8]}"
        create_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": rt_name,
                "description": "test relationship type",
                "directional": True,
                "properties": {},
                "custom_validators": [],
            },
        )
        assert create_resp.status_code == 201
        rt_id = create_resp.json()["id"]

        # CREATE で v1 が自動記録されるため、v2 のみ手動挿入
        result = await db_session.execute(
            text("SELECT id FROM do_schema_versions WHERE type_id = :type_id AND version = 1"),
            {"type_id": rt_id},
        )
        sv1_id = str(result.scalar_one())

        schema_v2 = {"properties": {"weight": {"type": "float", "required": False}}}
        await _insert_schema_version(
            db_session,
            type_id=rt_id,
            type_kind=TypeKind.RELATIONSHIP_TYPE,
            version=2,
            schema_definition=schema_v2,
            previous_version_id=sv1_id,
            compatibility=CompatibilityLevel.BACKWARD,
            namespace_id=test_namespace_id,
        )

        response = await client.get(f"/schema/relationship-types/{rt_id}/versions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["version"] == 1
        assert data[1]["version"] == 2
        assert data[0]["type_kind"] == "relationship_type"

    async def test_get_specific_version(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_namespace_id: str,
    ) -> None:
        """リレーションシップタイプの特定バージョンを取得する。"""
        rt_name = f"RTVersionGet_{uuid4().hex[:8]}"
        create_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": rt_name,
                "description": "",
                "directional": True,
                "properties": {},
                "custom_validators": [],
            },
        )
        assert create_resp.status_code == 201
        rt_id = create_resp.json()["id"]

        # CREATE で v1 が自動記録されるため、v2 を手動挿入して取得テスト
        result = await db_session.execute(
            text("SELECT id FROM do_schema_versions WHERE type_id = :type_id AND version = 1"),
            {"type_id": rt_id},
        )
        sv1_id = str(result.scalar_one())

        schema_def = {"properties": {"label": {"type": "string", "required": False}}}
        await _insert_schema_version(
            db_session,
            type_id=rt_id,
            type_kind=TypeKind.RELATIONSHIP_TYPE,
            version=2,
            schema_definition=schema_def,
            created_by="rt-tester",
            previous_version_id=sv1_id,
            namespace_id=test_namespace_id,
        )

        response = await client.get(f"/schema/relationship-types/{rt_id}/versions/2")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == 2
        assert data["type_id"] == rt_id
        assert data["created_by"] == "rt-tester"
        assert data["type_kind"] == "relationship_type"

    async def test_get_version_not_found(self, client: AsyncClient) -> None:
        """存在しないリレーションシップタイプバージョンを取得すると 404 を返す。"""
        non_existent_id = str(uuid4())
        response = await client.get(f"/schema/relationship-types/{non_existent_id}/versions/999")
        assert response.status_code == 404

    async def test_diff_between_versions(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_namespace_id: str,
    ) -> None:
        """リレーションシップタイプの2つのバージョン間の差分を計算する。"""
        rt_name = f"RTDiff_{uuid4().hex[:8]}"
        create_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": rt_name,
                "description": "",
                "directional": False,
                "properties": {},
                "custom_validators": [],
            },
        )
        assert create_resp.status_code == 201
        rt_id = create_resp.json()["id"]

        # CREATE で v1 が自動記録されるため、v2 と v3 を手動挿入
        result = await db_session.execute(
            text("SELECT id FROM do_schema_versions WHERE type_id = :type_id AND version = 1"),
            {"type_id": rt_id},
        )
        sv1_id = str(result.scalar_one())

        schema_v2 = {
            "properties": {
                "weight": {"type": "float", "required": True},
                "label": {"type": "string", "required": False},
            }
        }
        sv2_id = await _insert_schema_version(
            db_session,
            type_id=rt_id,
            type_kind=TypeKind.RELATIONSHIP_TYPE,
            version=2,
            schema_definition=schema_v2,
            previous_version_id=sv1_id,
            namespace_id=test_namespace_id,
        )
        schema_v3 = {
            "properties": {
                "weight": {"type": "float", "required": True},
            }
        }
        await _insert_schema_version(
            db_session,
            type_id=rt_id,
            type_kind=TypeKind.RELATIONSHIP_TYPE,
            version=3,
            schema_definition=schema_v3,
            previous_version_id=sv2_id,
            namespace_id=test_namespace_id,
        )

        response = await client.get(
            f"/schema/relationship-types/{rt_id}/diff",
            params={"from_version": 2, "to_version": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["added_fields"] == []
        assert "label" in data["removed_fields"]
        assert data["compatibility"] == "forward"

    async def test_diff_with_nonexistent_version(self, client: AsyncClient) -> None:
        """差分取得で存在しないリレーションシップタイプバージョンを指定すると 404 を返す。"""
        non_existent_id = str(uuid4())
        response = await client.get(
            f"/schema/relationship-types/{non_existent_id}/diff",
            params={"from_version": 1, "to_version": 2},
        )
        assert response.status_code == 404
