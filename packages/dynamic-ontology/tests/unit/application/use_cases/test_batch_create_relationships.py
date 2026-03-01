"""BatchCreateRelationshipsUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.batch_create_relationships import (
    BatchCreateRelationshipItem,
    BatchCreateRelationshipsUseCase,
)
from dynamic_ontology.domain.exceptions import BatchOperationError
from dynamic_ontology.domain.models.batch import BatchResult
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.relationship import RelationshipType


def _make_entity() -> Entity:
    now = datetime.now(UTC)
    return Entity(
        id=uuid4(),
        type_id=uuid4(),
        version=1,
        properties={},
        created_at=now,
        updated_at=now,
    )


def _make_rel_type() -> RelationshipType:
    now = datetime.now(UTC)
    return RelationshipType(
        id=uuid4(),
        name="belongs_to",
        description="",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def deps() -> dict[str, AsyncMock]:
    return {
        "relationship_type_repo": AsyncMock(),
        "entity_repo": AsyncMock(),
        "relationship_repo": AsyncMock(),
        "uow": AsyncMock(),
    }


@pytest.mark.asyncio
async def test_creates_and_commits(deps: dict[str, AsyncMock]) -> None:
    """全アイテム作成成功時にコミットする。"""
    rt = _make_rel_type()
    from_e = _make_entity()
    to_e = _make_entity()

    deps["relationship_type_repo"].get_by_id.return_value = rt

    async def get_entity(eid: str, **_: object) -> Entity | None:
        if eid == str(from_e.id):
            return from_e
        if eid == str(to_e.id):
            return to_e
        return None

    deps["entity_repo"].get_by_id.side_effect = get_entity

    ok_result = BatchResult(
        success=True,
        total=1,
        succeeded=1,
        failed=0,
        entity_ids=[uuid4()],
        errors=[],
    )
    deps["relationship_repo"].create_many.return_value = ok_result

    uc = BatchCreateRelationshipsUseCase(**deps)
    result = await uc.execute(
        items=[
            BatchCreateRelationshipItem(
                type_id=rt.id,
                from_entity_id=from_e.id,
                to_entity_id=to_e.id,
                properties={},
            )
        ],
    )

    assert result.success
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_batch_error_on_type_not_found(deps: dict[str, AsyncMock]) -> None:
    """リレーションシップタイプ未検出時に BatchOperationError。"""
    deps["relationship_type_repo"].get_by_id.return_value = None

    uc = BatchCreateRelationshipsUseCase(**deps)

    with pytest.raises(BatchOperationError):
        await uc.execute(
            items=[
                BatchCreateRelationshipItem(
                    type_id=uuid4(),
                    from_entity_id=uuid4(),
                    to_entity_id=uuid4(),
                    properties={},
                )
            ],
        )


@pytest.mark.asyncio
async def test_raises_batch_error_on_source_type_constraint(
    deps: dict[str, AsyncMock],
) -> None:
    """allowed_source_types 制約違反時に BatchOperationError。"""
    rt = _make_rel_type()
    rt.allowed_source_types = [uuid4()]  # from_entity の type_id とは異なる

    from_e = _make_entity()
    to_e = _make_entity()

    deps["relationship_type_repo"].get_by_id.return_value = rt

    async def get_entity(eid: str, **_: object) -> Entity | None:
        if eid == str(from_e.id):
            return from_e
        if eid == str(to_e.id):
            return to_e
        return None

    deps["entity_repo"].get_by_id.side_effect = get_entity

    uc = BatchCreateRelationshipsUseCase(**deps)

    with pytest.raises(BatchOperationError):
        await uc.execute(
            items=[
                BatchCreateRelationshipItem(
                    type_id=rt.id,
                    from_entity_id=from_e.id,
                    to_entity_id=to_e.id,
                    properties={},
                )
            ],
        )


@pytest.mark.asyncio
async def test_batch_create_duplicate_rejected(deps: dict[str, AsyncMock]) -> None:
    """allow_duplicates=False で DB に既存ペアがある場合 BatchOperationError。"""
    rt = _make_rel_type()
    rt.allow_duplicates = False
    from_e = _make_entity()
    to_e = _make_entity()

    deps["relationship_type_repo"].get_by_id.return_value = rt

    async def get_entity(eid: str, **_: object) -> Entity | None:
        if eid == str(from_e.id):
            return from_e
        if eid == str(to_e.id):
            return to_e
        return None

    deps["entity_repo"].get_by_id.side_effect = get_entity
    deps["relationship_repo"].exists_by_pair.return_value = True

    uc = BatchCreateRelationshipsUseCase(**deps)

    with pytest.raises(BatchOperationError):
        await uc.execute(
            items=[
                BatchCreateRelationshipItem(
                    type_id=rt.id,
                    from_entity_id=from_e.id,
                    to_entity_id=to_e.id,
                    properties={},
                )
            ],
        )


@pytest.mark.asyncio
async def test_batch_create_intra_batch_duplicate_rejected(
    deps: dict[str, AsyncMock],
) -> None:
    """バッチ内で同一ペアが重複する場合 BatchOperationError。"""
    rt = _make_rel_type()
    rt.allow_duplicates = False
    from_e = _make_entity()
    to_e = _make_entity()

    deps["relationship_type_repo"].get_by_id.return_value = rt

    async def get_entity(eid: str, **_: object) -> Entity | None:
        if eid == str(from_e.id):
            return from_e
        if eid == str(to_e.id):
            return to_e
        return None

    deps["entity_repo"].get_by_id.side_effect = get_entity
    # DB には存在しない
    deps["relationship_repo"].exists_by_pair.return_value = False

    item = BatchCreateRelationshipItem(
        type_id=rt.id,
        from_entity_id=from_e.id,
        to_entity_id=to_e.id,
        properties={},
    )

    uc = BatchCreateRelationshipsUseCase(**deps)

    with pytest.raises(BatchOperationError):
        await uc.execute(items=[item, item])


@pytest.mark.asyncio
async def test_batch_create_non_directional_reverse_duplicate(
    deps: dict[str, AsyncMock],
) -> None:
    """非方向性タイプで順方向+逆方向ペアがバッチ内にある場合 BatchOperationError。"""
    rt = _make_rel_type()
    rt.allow_duplicates = False
    rt.directional = False
    from_e = _make_entity()
    to_e = _make_entity()

    deps["relationship_type_repo"].get_by_id.return_value = rt

    async def get_entity(eid: str, **_: object) -> Entity | None:
        if eid == str(from_e.id):
            return from_e
        if eid == str(to_e.id):
            return to_e
        return None

    deps["entity_repo"].get_by_id.side_effect = get_entity
    # DB には存在しない
    deps["relationship_repo"].exists_by_pair.return_value = False

    forward_item = BatchCreateRelationshipItem(
        type_id=rt.id,
        from_entity_id=from_e.id,
        to_entity_id=to_e.id,
        properties={},
    )
    reverse_item = BatchCreateRelationshipItem(
        type_id=rt.id,
        from_entity_id=to_e.id,
        to_entity_id=from_e.id,
        properties={},
    )

    uc = BatchCreateRelationshipsUseCase(**deps)

    with pytest.raises(BatchOperationError):
        await uc.execute(items=[forward_item, reverse_item])


@pytest.mark.asyncio
async def test_batch_create_allows_duplicates_when_flag_true(
    deps: dict[str, AsyncMock],
) -> None:
    """allow_duplicates=True の場合、同一ペアが複数あっても成功する。"""
    rt = _make_rel_type()
    rt.allow_duplicates = True
    from_e = _make_entity()
    to_e = _make_entity()

    deps["relationship_type_repo"].get_by_id.return_value = rt

    async def get_entity(eid: str, **_: object) -> Entity | None:
        if eid == str(from_e.id):
            return from_e
        if eid == str(to_e.id):
            return to_e
        return None

    deps["entity_repo"].get_by_id.side_effect = get_entity

    ok_result = BatchResult(
        success=True,
        total=2,
        succeeded=2,
        failed=0,
        entity_ids=[uuid4(), uuid4()],
        errors=[],
    )
    deps["relationship_repo"].create_many.return_value = ok_result

    item = BatchCreateRelationshipItem(
        type_id=rt.id,
        from_entity_id=from_e.id,
        to_entity_id=to_e.id,
        properties={},
    )

    uc = BatchCreateRelationshipsUseCase(**deps)
    result = await uc.execute(items=[item, item])

    assert result.success
    deps["relationship_repo"].exists_by_pair.assert_not_awaited()
