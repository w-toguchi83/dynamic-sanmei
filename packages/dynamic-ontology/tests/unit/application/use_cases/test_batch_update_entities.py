"""BatchUpdateEntitiesUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.batch_update_entities import (
    BatchUpdateEntitiesUseCase,
    BatchUpdateItem,
)
from dynamic_ontology.domain.exceptions import BatchOperationError, ValidationError
from dynamic_ontology.domain.models.batch import BatchResult
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType


def _make_entity(*, type_id: None | object = None) -> Entity:
    now = datetime.now(UTC)
    return Entity(
        id=uuid4(),
        type_id=type_id or uuid4(),
        version=2,
        properties={"name": "original"},
        created_at=now,
        updated_at=now,
    )


def _make_entity_type(*, type_id: None | object = None) -> EntityType:
    now = datetime.now(UTC)
    return EntityType(
        id=type_id or uuid4(),
        name="TestType",
        description="",
        properties={},
        custom_validators=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def deps() -> dict[str, AsyncMock]:
    return {
        "entity_type_repo": AsyncMock(),
        "entity_repo": AsyncMock(),
        "validation_engine": MagicMock(),
        "uow": AsyncMock(),
    }


@pytest.mark.asyncio
async def test_updates_and_commits(deps: dict[str, AsyncMock]) -> None:
    """全アイテム更新成功時にコミットする。"""
    entity = _make_entity()
    entity_type = _make_entity_type(type_id=entity.type_id)
    deps["entity_repo"].get_by_id.return_value = entity
    deps["entity_type_repo"].get_by_id.return_value = entity_type
    deps["validation_engine"].validate_and_apply_defaults.return_value = {"name": "updated"}

    ok_result = BatchResult(
        success=True,
        total=1,
        succeeded=1,
        failed=0,
        entity_ids=[entity.id],
        errors=[],
    )
    deps["entity_repo"].update_many.return_value = ok_result

    uc = BatchUpdateEntitiesUseCase(**deps)
    result = await uc.execute(
        items=[BatchUpdateItem(id=entity.id, properties={"name": "updated"}, version=2)],
    )

    assert result.success
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_batch_error_on_entity_not_found(deps: dict[str, AsyncMock]) -> None:
    """エンティティ未検出時に BatchOperationError。"""
    deps["entity_repo"].get_by_id.return_value = None

    uc = BatchUpdateEntitiesUseCase(**deps)

    with pytest.raises(BatchOperationError):
        await uc.execute(
            items=[BatchUpdateItem(id=uuid4(), properties={}, version=1)],
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_batch_error_on_validation_failure(deps: dict[str, AsyncMock]) -> None:
    """バリデーションエラー時に BatchOperationError。"""
    entity = _make_entity()
    entity_type = _make_entity_type(type_id=entity.type_id)
    deps["entity_repo"].get_by_id.return_value = entity
    deps["entity_type_repo"].get_by_id.return_value = entity_type
    deps["validation_engine"].validate_and_apply_defaults.side_effect = ValidationError(
        [{"field": "name", "message": "required"}]
    )

    uc = BatchUpdateEntitiesUseCase(**deps)

    with pytest.raises(BatchOperationError):
        await uc.execute(
            items=[BatchUpdateItem(id=entity.id, properties={}, version=2)],
        )


@pytest.mark.asyncio
async def test_rollbacks_on_update_many_failure(deps: dict[str, AsyncMock]) -> None:
    """update_many 失敗時にロールバック。"""
    entity = _make_entity()
    entity_type = _make_entity_type(type_id=entity.type_id)
    deps["entity_repo"].get_by_id.return_value = entity
    deps["entity_type_repo"].get_by_id.return_value = entity_type
    deps["validation_engine"].validate_and_apply_defaults.return_value = {"name": "x"}

    fail_result = BatchResult(
        success=False,
        total=1,
        succeeded=0,
        failed=1,
        entity_ids=[],
        errors=[],
    )
    deps["entity_repo"].update_many.return_value = fail_result

    uc = BatchUpdateEntitiesUseCase(**deps)
    result = await uc.execute(
        items=[BatchUpdateItem(id=entity.id, properties={"name": "x"}, version=2)],
    )

    assert not result.success
    deps["uow"].rollback.assert_awaited_once()
    deps["uow"].commit.assert_not_awaited()
