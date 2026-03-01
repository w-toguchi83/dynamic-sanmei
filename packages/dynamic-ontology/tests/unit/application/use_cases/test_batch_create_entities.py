"""BatchCreateEntitiesUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.batch_create_entities import (
    BatchCreateEntitiesUseCase,
    BatchCreateItem,
)
from dynamic_ontology.domain.exceptions import BatchOperationError, ValidationError
from dynamic_ontology.domain.models.batch import BatchResult
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType


@pytest.fixture
def entity_type() -> EntityType:
    now = datetime.now(UTC)
    return EntityType(
        id=uuid4(),
        name="TestType",
        description="テスト用タイプ",
        properties={"name": PropertyDefinition(type=PropertyType.STRING, required=True)},
        custom_validators=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def deps(entity_type: EntityType) -> dict[str, AsyncMock | MagicMock]:
    entity_type_repo = AsyncMock()
    entity_type_repo.get_by_id.return_value = entity_type

    entity_ids = [uuid4(), uuid4()]
    entity_repo = AsyncMock()
    entity_repo.create_many.return_value = BatchResult(
        success=True,
        total=2,
        succeeded=2,
        failed=0,
        entity_ids=entity_ids,
        errors=[],
    )

    validation_engine = MagicMock()
    validation_engine.validate_and_apply_defaults.side_effect = lambda props, _et: props

    uow = AsyncMock()

    return {
        "entity_type_repo": entity_type_repo,
        "entity_repo": entity_repo,
        "validation_engine": validation_engine,
        "uow": uow,
    }


@pytest.mark.asyncio
async def test_creates_entities_and_commits(
    entity_type: EntityType,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """全件バリデーション成功 → create_many → コミットする。"""
    use_case = BatchCreateEntitiesUseCase(**deps)

    items = [
        BatchCreateItem(type_id=entity_type.id, properties={"name": "a"}),
        BatchCreateItem(type_id=entity_type.id, properties={"name": "b"}),
    ]

    result = await use_case.execute(items=items, principal_id="user-1")

    assert result.success is True
    assert result.total == 2
    deps["entity_repo"].create_many.assert_awaited_once()
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()
    deps["uow"].rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_batch_error_on_validation_failure(
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """EntityType が見つからない場合 BatchOperationError を発生させる。"""
    deps["entity_type_repo"].get_by_id.return_value = None

    use_case = BatchCreateEntitiesUseCase(**deps)

    items = [
        BatchCreateItem(type_id=uuid4(), properties={"name": "a"}),
    ]

    with pytest.raises(BatchOperationError) as exc_info:
        await use_case.execute(items=items)

    assert len(exc_info.value.errors) == 1
    assert "not found" in exc_info.value.errors[0].message
    deps["entity_repo"].create_many.assert_not_awaited()
    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_batch_error_on_property_validation_failure(
    entity_type: EntityType,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """プロパティバリデーション失敗時に BatchOperationError を発生させる。"""
    deps["validation_engine"].validate_and_apply_defaults.side_effect = ValidationError(
        [{"field": "name", "message": "必須フィールドです"}]
    )

    use_case = BatchCreateEntitiesUseCase(**deps)

    items = [
        BatchCreateItem(type_id=entity_type.id, properties={}),
    ]

    with pytest.raises(BatchOperationError) as exc_info:
        await use_case.execute(items=items)

    assert len(exc_info.value.errors) == 1
    deps["entity_repo"].create_many.assert_not_awaited()


@pytest.mark.asyncio
async def test_rollbacks_on_create_many_failure(
    entity_type: EntityType,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """create_many が失敗した場合ロールバックする。"""
    deps["entity_repo"].create_many.return_value = BatchResult(
        success=False,
        total=1,
        succeeded=0,
        failed=1,
        entity_ids=[],
        errors=[],
    )

    use_case = BatchCreateEntitiesUseCase(**deps)

    items = [
        BatchCreateItem(type_id=entity_type.id, properties={"name": "a"}),
    ]

    result = await use_case.execute(items=items)

    assert result.success is False
    deps["uow"].rollback.assert_awaited_once()
    deps["uow"].commit.assert_not_awaited()
