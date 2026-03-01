"""UpdateRelationshipUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.update_relationship import UpdateRelationshipUseCase
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
        version=2,
        properties={"weight": 1.0},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def deps(existing_relationship: Relationship) -> dict[str, AsyncMock]:
    relationship_repo = AsyncMock()
    relationship_repo.get_by_id.return_value = existing_relationship

    updated = Relationship(
        id=existing_relationship.id,
        type_id=existing_relationship.type_id,
        from_entity_id=existing_relationship.from_entity_id,
        to_entity_id=existing_relationship.to_entity_id,
        version=3,
        properties={"weight": 2.0},
        created_at=existing_relationship.created_at,
        updated_at=datetime.now(UTC),
    )
    relationship_repo.update.return_value = updated

    uow = AsyncMock()

    return {
        "relationship_repo": relationship_repo,
        "uow": uow,
    }


@pytest.mark.asyncio
async def test_updates_relationship_and_commits(
    existing_relationship: Relationship,
    deps: dict[str, AsyncMock],
) -> None:
    """リレーションシップを更新し、コミットする。"""
    use_case = UpdateRelationshipUseCase(**deps)

    result = await use_case.execute(
        relationship_id=existing_relationship.id,
        properties={"weight": 2.0},
        current_version=2,
        principal_id="user-1",
    )

    deps["relationship_repo"].update.assert_awaited_once()
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()
    assert result.version == 3


@pytest.mark.asyncio
async def test_raises_not_found_when_relationship_missing(
    deps: dict[str, AsyncMock],
) -> None:
    """存在しないリレーションシップの場合 EntityNotFoundError を発生させる。"""
    deps["relationship_repo"].get_by_id.return_value = None

    use_case = UpdateRelationshipUseCase(**deps)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            relationship_id=uuid4(),
            properties={"weight": 2.0},
            current_version=1,
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_before_properties(
    existing_relationship: Relationship,
    deps: dict[str, AsyncMock],
) -> None:
    """更新前のプロパティを戻り値に含む。"""
    use_case = UpdateRelationshipUseCase(**deps)

    result = await use_case.execute(
        relationship_id=existing_relationship.id,
        properties={"weight": 2.0},
        current_version=2,
    )

    assert result.before_properties == {"weight": 1.0}


@pytest.mark.asyncio
async def test_merges_properties(
    existing_relationship: Relationship,
    deps: dict[str, AsyncMock],
) -> None:
    """既存プロパティと更新プロパティをマージする。"""
    use_case = UpdateRelationshipUseCase(**deps)

    await use_case.execute(
        relationship_id=existing_relationship.id,
        properties={"weight": 2.0},
        current_version=2,
    )

    # update() に渡されたリレーションシップのプロパティを確認
    call_args = deps["relationship_repo"].update.call_args
    updated_rel = call_args[0][0]
    assert updated_rel.properties == {"weight": 2.0}
