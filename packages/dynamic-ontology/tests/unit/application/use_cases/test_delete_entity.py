"""DeleteEntityUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.delete_entity import DeleteEntityUseCase
from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.entity import Entity


@pytest.fixture
def existing_entity() -> Entity:
    now = datetime.now(UTC)
    return Entity(
        id=uuid4(),
        type_id=uuid4(),
        version=3,
        properties={"name": "to-delete"},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def deps(existing_entity: Entity) -> dict[str, AsyncMock]:
    entity_repo = AsyncMock()
    entity_repo.get_by_id.return_value = existing_entity
    entity_repo.delete.return_value = True

    uow = AsyncMock()

    return {
        "entity_repo": entity_repo,
        "uow": uow,
    }


@pytest.mark.asyncio
async def test_deletes_entity_and_commits(
    existing_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """エンティティを削除し、コミットする。"""
    use_case = DeleteEntityUseCase(**deps)

    result = await use_case.execute(entity_id=existing_entity.id)

    deps["entity_repo"].get_by_id.assert_awaited_once_with(str(existing_entity.id))
    deps["entity_repo"].delete.assert_awaited_once_with(str(existing_entity.id))
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()
    assert result.entity_id == existing_entity.id


@pytest.mark.asyncio
async def test_raises_not_found_when_entity_missing(
    deps: dict[str, AsyncMock],
) -> None:
    """存在しない Entity の場合 EntityNotFoundError を発生させる。"""
    deps["entity_repo"].get_by_id.return_value = None

    use_case = DeleteEntityUseCase(**deps)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(entity_id=uuid4())

    deps["entity_repo"].delete.assert_not_awaited()
    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_deleted_entity_info(
    existing_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """削除前のエンティティ情報を戻り値に含む。"""
    use_case = DeleteEntityUseCase(**deps)

    result = await use_case.execute(entity_id=existing_entity.id)

    assert result.entity_id == existing_entity.id
    assert result.type_id == existing_entity.type_id
    assert result.version == existing_entity.version
    assert result.properties == {"name": "to-delete"}
