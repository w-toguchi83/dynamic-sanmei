"""CreateEntityUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.create_entity import CreateEntityUseCase
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
def deps(entity_type: EntityType) -> dict[str, AsyncMock | MagicMock]:
    entity_type_repo = AsyncMock()
    entity_type_repo.get_by_id.return_value = entity_type

    created_entity = Entity(
        id=uuid4(),
        type_id=entity_type.id,
        version=1,
        properties={"name": "test"},
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )
    entity_repo = AsyncMock()
    entity_repo.create.return_value = created_entity

    validation_engine = MagicMock()
    validation_engine.validate_and_apply_defaults.return_value = {"name": "test"}

    uow = AsyncMock()

    return {
        "entity_type_repo": entity_type_repo,
        "entity_repo": entity_repo,
        "validation_engine": validation_engine,
        "uow": uow,
    }


@pytest.mark.asyncio
async def test_creates_entity_and_commits(
    entity_type: EntityType,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """エンティティを作成し、バリデーション→永続化→コミットの順で実行する。"""
    use_case = CreateEntityUseCase(**deps)

    result = await use_case.execute(
        type_id=entity_type.id,
        properties={"name": "test"},
        principal_id="user-1",
    )

    deps["validation_engine"].validate_and_apply_defaults.assert_called_once()
    deps["entity_repo"].create.assert_awaited_once()
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()
    assert result.properties == {"name": "test"}


@pytest.mark.asyncio
async def test_raises_not_found_when_entity_type_missing(
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """存在しない EntityType の場合 EntityNotFoundError を発生させる。"""
    deps["entity_type_repo"].get_by_id.return_value = None

    use_case = CreateEntityUseCase(**deps)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            type_id=uuid4(),
            properties={"name": "test"},
            principal_id="user-1",
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_entity_type_name(
    entity_type: EntityType,
    deps: dict[str, AsyncMock | MagicMock],
) -> None:
    """戻り値にエンティティタイプ名を含む。"""
    use_case = CreateEntityUseCase(**deps)

    result = await use_case.execute(
        type_id=entity_type.id,
        properties={"name": "test"},
        principal_id="user-1",
    )

    assert result.entity_type_name == entity_type.name
