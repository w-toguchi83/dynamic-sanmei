"""リレーション作成時の allowed_source/target_types バリデーションテスト."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestRelationshipAllowedTypesValidation:
    """allowed_source/target_types 制約のバリデーション."""

    @pytest.mark.asyncio
    async def test_create_relationship_with_valid_types(self, client: AsyncClient) -> None:
        """許可されたタイプ間のリレーション作成は成功する."""
        # 1. EntityType 2つ作成
        person_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"Person_{uuid4().hex[:8]}", "properties": {}},
        )
        assert person_resp.status_code == 201
        person_type_id = person_resp.json()["id"]

        company_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"Company_{uuid4().hex[:8]}", "properties": {}},
        )
        assert company_resp.status_code == 201
        company_type_id = company_resp.json()["id"]

        # 2. RelationshipType 作成（制約あり）
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": f"works_at_{uuid4().hex[:8]}",
                "directional": True,
                "allowed_source_types": [person_type_id],
                "allowed_target_types": [company_type_id],
            },
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        # 3. Entity 2つ作成
        person_entity_resp = await client.post(
            "/entities",
            json={"type_id": person_type_id, "properties": {}},
        )
        assert person_entity_resp.status_code == 201
        person_id = person_entity_resp.json()["id"]

        company_entity_resp = await client.post(
            "/entities",
            json={"type_id": company_type_id, "properties": {}},
        )
        assert company_entity_resp.status_code == 201
        company_id = company_entity_resp.json()["id"]

        # 4. リレーション作成（成功するはず）
        rel_resp = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": person_id,
                "to_entity_id": company_id,
            },
        )
        assert rel_resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_relationship_with_invalid_source_type(self, client: AsyncClient) -> None:
        """許可されていないソースタイプでの作成は 400 エラー."""
        # 1. EntityType 2つ作成
        allowed_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"Allowed_{uuid4().hex[:8]}", "properties": {}},
        )
        assert allowed_resp.status_code == 201
        allowed_type_id = allowed_resp.json()["id"]

        other_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"Other_{uuid4().hex[:8]}", "properties": {}},
        )
        assert other_resp.status_code == 201
        other_type_id = other_resp.json()["id"]

        # 2. RelationshipType（source制約あり、target制約なし）
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": f"restricted_{uuid4().hex[:8]}",
                "directional": True,
                "allowed_source_types": [allowed_type_id],
                "allowed_target_types": [],
            },
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        # 3. 不許可タイプの Entity を source として作成
        wrong_entity = await client.post(
            "/entities",
            json={"type_id": other_type_id, "properties": {}},
        )
        assert wrong_entity.status_code == 201
        wrong_id = wrong_entity.json()["id"]

        target_entity = await client.post(
            "/entities",
            json={"type_id": allowed_type_id, "properties": {}},
        )
        assert target_entity.status_code == 201
        target_id = target_entity.json()["id"]

        # 4. リレーション作成（400 エラーになるはず）
        rel_resp = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": wrong_id,
                "to_entity_id": target_id,
            },
        )
        assert rel_resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_relationship_with_invalid_target_type(self, client: AsyncClient) -> None:
        """許可されていないターゲットタイプでの作成は 400 エラー."""
        # 1. EntityType 2つ作成
        allowed_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"AllowedT_{uuid4().hex[:8]}", "properties": {}},
        )
        assert allowed_resp.status_code == 201
        allowed_type_id = allowed_resp.json()["id"]

        other_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"OtherT_{uuid4().hex[:8]}", "properties": {}},
        )
        assert other_resp.status_code == 201
        other_type_id = other_resp.json()["id"]

        # 2. RelationshipType（source制約なし、target制約あり）
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": f"target_restricted_{uuid4().hex[:8]}",
                "directional": True,
                "allowed_source_types": [],
                "allowed_target_types": [allowed_type_id],
            },
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        # 3. Entity 作成
        source_entity = await client.post(
            "/entities",
            json={"type_id": allowed_type_id, "properties": {}},
        )
        assert source_entity.status_code == 201
        source_id = source_entity.json()["id"]

        # 不許可タイプの Entity を target として作成
        wrong_target = await client.post(
            "/entities",
            json={"type_id": other_type_id, "properties": {}},
        )
        assert wrong_target.status_code == 201
        wrong_target_id = wrong_target.json()["id"]

        # 4. リレーション作成（400 エラーになるはず）
        rel_resp = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": source_id,
                "to_entity_id": wrong_target_id,
            },
        )
        assert rel_resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_relationship_no_constraint(self, client: AsyncClient) -> None:
        """制約なし（空リスト）の場合は任意のタイプを許可する."""
        et_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"Any_{uuid4().hex[:8]}", "properties": {}},
        )
        assert et_resp.status_code == 201
        et_id = et_resp.json()["id"]

        rt_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": f"free_{uuid4().hex[:8]}",
                "directional": False,
                "allowed_source_types": [],
                "allowed_target_types": [],
            },
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        e1 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {}},
        )
        e2 = await client.post(
            "/entities",
            json={"type_id": et_id, "properties": {}},
        )

        rel_resp = await client.post(
            "/relationships",
            json={
                "type_id": rt_id,
                "from_entity_id": e1.json()["id"],
                "to_entity_id": e2.json()["id"],
            },
        )
        assert rel_resp.status_code == 201

    @pytest.mark.asyncio
    async def test_batch_create_relationship_with_invalid_source_type(
        self, client: AsyncClient
    ) -> None:
        """バッチ作成でも allowed_source_types 制約が適用される."""
        # 1. EntityType 2つ作成
        allowed_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"BatchAllowed_{uuid4().hex[:8]}", "properties": {}},
        )
        assert allowed_resp.status_code == 201
        allowed_type_id = allowed_resp.json()["id"]

        other_resp = await client.post(
            "/schema/entity-types",
            json={"name": f"BatchOther_{uuid4().hex[:8]}", "properties": {}},
        )
        assert other_resp.status_code == 201
        other_type_id = other_resp.json()["id"]

        # 2. RelationshipType（source制約あり）
        rt_resp = await client.post(
            "/schema/relationship-types",
            json={
                "name": f"batch_restricted_{uuid4().hex[:8]}",
                "directional": True,
                "allowed_source_types": [allowed_type_id],
                "allowed_target_types": [],
            },
        )
        assert rt_resp.status_code == 201
        rt_id = rt_resp.json()["id"]

        # 3. 不許可タイプの Entity を source に
        wrong_entity = await client.post(
            "/entities",
            json={"type_id": other_type_id, "properties": {}},
        )
        assert wrong_entity.status_code == 201

        target_entity = await client.post(
            "/entities",
            json={"type_id": allowed_type_id, "properties": {}},
        )
        assert target_entity.status_code == 201

        # 4. バッチリレーション作成（400 エラーになるはず）
        rel_resp = await client.post(
            "/relationships/batch",
            json={
                "relationships": [
                    {
                        "type_id": rt_id,
                        "from_entity_id": wrong_entity.json()["id"],
                        "to_entity_id": target_entity.json()["id"],
                    },
                ],
            },
        )
        assert rel_resp.status_code == 400
