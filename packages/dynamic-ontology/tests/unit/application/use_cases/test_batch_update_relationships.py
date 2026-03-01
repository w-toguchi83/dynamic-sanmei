"""BatchUpdateRelationshipsUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.batch_update_relationships import (
    BatchUpdateRelationshipItem,
    BatchUpdateRelationshipsUseCase,
)
from dynamic_ontology.domain.exceptions import BatchOperationError
from dynamic_ontology.domain.models.batch import BatchResult
from dynamic_ontology.domain.models.relationship import Relationship


def _make_relationship() -> Relationship:
    now = datetime.now(UTC)
    return Relationship(
        id=uuid4(),
        type_id=uuid4(),
        from_entity_id=uuid4(),
        to_entity_id=uuid4(),
        version=2,
        properties={"weight": 1.0},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def deps() -> dict[str, AsyncMock]:
    return {
        "relationship_repo": AsyncMock(),
        "uow": AsyncMock(),
    }


@pytest.mark.asyncio
async def test_updates_and_commits(deps: dict[str, AsyncMock]) -> None:
    """全アイテム更新成功時にコミットする。"""
    rel = _make_relationship()
    deps["relationship_repo"].get_by_id.return_value = rel

    ok_result = BatchResult(
        success=True,
        total=1,
        succeeded=1,
        failed=0,
        entity_ids=[rel.id],
        errors=[],
    )
    deps["relationship_repo"].update_many.return_value = ok_result

    uc = BatchUpdateRelationshipsUseCase(**deps)
    result = await uc.execute(
        items=[
            BatchUpdateRelationshipItem(
                id=rel.id,
                properties={"weight": 2.0},
                version=2,
            )
        ],
    )

    assert result.success
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_batch_error_on_not_found(deps: dict[str, AsyncMock]) -> None:
    """リレーションシップ未検出時に BatchOperationError。"""
    deps["relationship_repo"].get_by_id.return_value = None

    uc = BatchUpdateRelationshipsUseCase(**deps)

    with pytest.raises(BatchOperationError):
        await uc.execute(
            items=[
                BatchUpdateRelationshipItem(
                    id=uuid4(),
                    properties={},
                    version=1,
                )
            ],
        )


@pytest.mark.asyncio
async def test_rollbacks_on_update_many_failure(deps: dict[str, AsyncMock]) -> None:
    """update_many 失敗時にロールバック。"""
    rel = _make_relationship()
    deps["relationship_repo"].get_by_id.return_value = rel

    fail_result = BatchResult(
        success=False,
        total=1,
        succeeded=0,
        failed=1,
        entity_ids=[],
        errors=[],
    )
    deps["relationship_repo"].update_many.return_value = fail_result

    uc = BatchUpdateRelationshipsUseCase(**deps)
    result = await uc.execute(
        items=[
            BatchUpdateRelationshipItem(
                id=rel.id,
                properties={},
                version=2,
            )
        ],
    )

    assert not result.success
    deps["uow"].rollback.assert_awaited_once()
