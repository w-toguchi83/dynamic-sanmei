"""UpdateEntityUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.update_entity import UpdateEntityUseCase
from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.entity import Entity
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
def existing_entity(entity_type: EntityType) -> Entity:
    now = datetime.now(UTC)
    return Entity(
        id=uuid4(),
        type_id=entity_type.id,
        version=2,
        properties={"name": "original"},
        created_at=now,
        updated_at=now,
        changed_by="user-0",
    )


@pytest.fixture
def deps(
    entity_type: EntityType,
    existing_entity: Entity,
) -> dict[str, AsyncMock | MagicMock]:
    entity_type_repo = AsyncMock()
    entity_type_repo.get_by_id.return_value = entity_type

    entity_repo = AsyncMock()
    entity_repo.get_by_id.return_value = existing_entity

    updated = Entity(
        id=existing_entity.id,
        type_id=existing_entity.type_id,
        version=3,
        properties={"name": "updated"},
        created_at=existing_entity.created_at,
        updated_at=datetime.now(UTC),
        changed_by="user-1",
    )
    entity_repo.update.return_value = updated

    validation_engine = MagicMock()
    validation_engine.validate_and_apply_defaults.return_value = {"name": "updated"}

    uow = AsyncMock()

    return {
        "entity_type_repo": entity_type_repo,
        "entity_repo": entity_repo,
        "validation_engine": validation_engine,
        "uow": uow,
    }


@pytest.mark.asyncio
async def test_updates_entity_and_commits(
    existing_entity: Entity,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """エンティティを更新し、マージ→バリデーション→永続化→コミットの順で実行する。"""
    use_case = UpdateEntityUseCase(**deps)

    result = await use_case.execute(
        entity_id=existing_entity.id,
        properties={"name": "updated"},
        current_version=2,
        principal_id="user-1",
    )

    # プロパティがマージされてバリデーションに渡される
    deps["validation_engine"].validate_and_apply_defaults.assert_called_once()
    deps["entity_repo"].update.assert_awaited_once()
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()
    assert result.properties == {"name": "updated"}
    assert result.version == 3


@pytest.mark.asyncio
async def test_raises_not_found_when_entity_missing(
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """存在しない Entity の場合 EntityNotFoundError を発生させる。"""
    deps["entity_repo"].get_by_id.return_value = None

    use_case = UpdateEntityUseCase(**deps)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            entity_id=uuid4(),
            properties={"name": "updated"},
            current_version=1,
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_not_found_when_entity_type_missing(
    existing_entity: Entity,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """EntityType が見つからない場合 EntityNotFoundError を発生させる。"""
    deps["entity_type_repo"].get_by_id.return_value = None

    use_case = UpdateEntityUseCase(**deps)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            entity_id=existing_entity.id,
            properties={"name": "updated"},
            current_version=2,
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_before_properties(
    existing_entity: Entity,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """戻り値に更新前のプロパティを含む。"""
    use_case = UpdateEntityUseCase(**deps)

    result = await use_case.execute(
        entity_id=existing_entity.id,
        properties={"name": "updated"},
        current_version=2,
    )

    assert result.before_properties == {"name": "original"}


@pytest.mark.asyncio
async def test_merges_properties_before_validation(
    existing_entity: Entity,
    entity_type: EntityType,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """既存プロパティと更新プロパティをマージしてからバリデーションに渡す。"""
    use_case = UpdateEntityUseCase(**deps)

    await use_case.execute(
        entity_id=existing_entity.id,
        properties={"name": "updated"},
        current_version=2,
    )

    # validate_and_apply_defaults に渡されたプロパティはマージ済み
    call_args = deps["validation_engine"].validate_and_apply_defaults.call_args
    merged = call_args[0][0]
    assert merged == {"name": "updated"}
