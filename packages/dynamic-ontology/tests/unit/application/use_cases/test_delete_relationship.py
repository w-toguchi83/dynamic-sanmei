"""DeleteRelationshipUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.delete_relationship import DeleteRelationshipUseCase
from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.relationship import Relationship


@pytest.fixture
def existing_relationship() -> Relationship:
    now = datetime.now(UTC)
    return Relationship(
        id=uuid4(),
        type_id=uuid4(),
        from_entity_id=uuid4(),
        to_entity_id=uuid4(),
        version=1,
        properties={"label": "test"},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def deps(existing_relationship: Relationship) -> dict[str, AsyncMock]:
    relationship_repo = AsyncMock()
    relationship_repo.get_by_id.return_value = existing_relationship
    relationship_repo.delete.return_value = True

    uow = AsyncMock()

    return {
        "relationship_repo": relationship_repo,
        "uow": uow,
    }


@pytest.mark.asyncio
async def test_deletes_relationship_and_commits(
    existing_relationship: Relationship,
    deps: dict[str, AsyncMock],
) -> None:
    """リレーションシップを削除し、コミットする。"""
    use_case = DeleteRelationshipUseCase(**deps)

    result = await use_case.execute(relationship_id=existing_relationship.id)

    deps["relationship_repo"].delete.assert_awaited_once_with(str(existing_relationship.id))
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()
    assert result.relationship_id == existing_relationship.id


@pytest.mark.asyncio
async def test_raises_not_found_when_relationship_missing(
    deps: dict[str, AsyncMock],
) -> None:
    """存在しないリレーションシップの場合 EntityNotFoundError を発生させる。"""
    deps["relationship_repo"].get_by_id.return_value = None

    use_case = DeleteRelationshipUseCase(**deps)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(relationship_id=uuid4())

    deps["relationship_repo"].delete.assert_not_awaited()
    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_deleted_relationship_info(
    existing_relationship: Relationship,
    deps: dict[str, AsyncMock],
) -> None:
    """削除前のリレーションシップ情報を戻り値に含む。"""
    use_case = DeleteRelationshipUseCase(**deps)

    result = await use_case.execute(relationship_id=existing_relationship.id)

    assert result.relationship_id == existing_relationship.id
    assert result.type_id == existing_relationship.type_id
    assert result.from_entity_id == existing_relationship.from_entity_id
    assert result.to_entity_id == existing_relationship.to_entity_id
    assert result.properties == {"label": "test"}
