"""BatchDeleteEntitiesUseCase のテスト。"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.batch_delete_entities import BatchDeleteEntitiesUseCase
from dynamic_ontology.domain.models.batch import BatchResult


@pytest.fixture
def deps() -> dict[str, AsyncMock]:
    return {
        "entity_repo": AsyncMock(),
        "uow": AsyncMock(),
    }


@pytest.mark.asyncio
async def test_deletes_and_commits(deps: dict[str, AsyncMock]) -> None:
    """全削除成功時にコミットする。"""
    ids = [uuid4(), uuid4()]
    ok_result = BatchResult(
        success=True,
        total=2,
        succeeded=2,
        failed=0,
        entity_ids=ids,
        errors=[],
    )
    deps["entity_repo"].delete_many.return_value = ok_result

    uc = BatchDeleteEntitiesUseCase(**deps)
    result = await uc.execute(entity_ids=ids)

    assert result.success
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_rollbacks_on_failure(deps: dict[str, AsyncMock]) -> None:
    """delete_many 失敗時にロールバック。"""
    ids = [uuid4()]
    fail_result = BatchResult(
        success=False,
        total=1,
        succeeded=0,
        failed=1,
        entity_ids=[],
        errors=[],
    )
    deps["entity_repo"].delete_many.return_value = fail_result

    uc = BatchDeleteEntitiesUseCase(**deps)
    result = await uc.execute(entity_ids=ids)

    assert not result.success
    deps["uow"].rollback.assert_awaited_once()
    deps["uow"].commit.assert_not_awaited()
