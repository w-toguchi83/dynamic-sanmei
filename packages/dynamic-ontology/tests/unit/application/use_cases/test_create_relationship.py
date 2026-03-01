"""CreateRelationshipUseCase のテスト。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from dynamic_ontology.application.use_cases.create_relationship import CreateRelationshipUseCase
from dynamic_ontology.domain.exceptions import (
    DuplicateRelationshipError,
    EntityNotFoundError,
    ValidationError,
)
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.relationship import Relationship, RelationshipType


@pytest.fixture
def rel_type() -> RelationshipType:
    now = datetime.now(UTC)
    return RelationshipType(
        id=uuid4(),
        name="belongs_to",
        description="所属関係",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def from_entity() -> Entity:
    now = datetime.now(UTC)
    return Entity(
        id=uuid4(),
        type_id=uuid4(),
        version=1,
        properties={"name": "source"},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def to_entity() -> Entity:
    now = datetime.now(UTC)
    return Entity(
        id=uuid4(),
        type_id=uuid4(),
        version=1,
        properties={"name": "target"},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def deps(
    rel_type: RelationshipType,
    from_entity: Entity,
    to_entity: Entity,
) -> dict[str, AsyncMock]:
    relationship_type_repo = AsyncMock()
    relationship_type_repo.get_by_id.return_value = rel_type

    entity_repo = AsyncMock()

    async def get_entity(eid: str, at_time: str | None = None) -> Entity | None:
        if eid == str(from_entity.id):
            return from_entity
        if eid == str(to_entity.id):
            return to_entity
        return None

    entity_repo.get_by_id.side_effect = get_entity

    created_rel = Relationship(
        id=uuid4(),
        type_id=rel_type.id,
        from_entity_id=from_entity.id,
        to_entity_id=to_entity.id,
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    relationship_repo = AsyncMock()
    relationship_repo.create.return_value = created_rel

    uow = AsyncMock()

    return {
        "relationship_type_repo": relationship_type_repo,
        "relationship_repo": relationship_repo,
        "entity_repo": entity_repo,
        "uow": uow,
    }


@pytest.mark.asyncio
async def test_creates_relationship_and_commits(
    rel_type: RelationshipType,
    from_entity: Entity,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """リレーションシップを作成し、コミットする。"""
    use_case = CreateRelationshipUseCase(**deps)

    result = await use_case.execute(
        type_id=rel_type.id,
        from_entity_id=from_entity.id,
        to_entity_id=to_entity.id,
        principal_id="user-1",
    )

    deps["relationship_repo"].create.assert_awaited_once()
    # コミットはルートハンドラ側で outbox append 後に実行される
    deps["uow"].commit.assert_not_awaited()
    assert result.type_name == "belongs_to"


@pytest.mark.asyncio
async def test_raises_not_found_when_rel_type_missing(
    from_entity: Entity,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """RelationshipType が存在しない場合 EntityNotFoundError を発生させる。"""
    deps["relationship_type_repo"].get_by_id.return_value = None

    use_case = CreateRelationshipUseCase(**deps)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            type_id=uuid4(),
            from_entity_id=from_entity.id,
            to_entity_id=to_entity.id,
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_not_found_when_source_entity_missing(
    rel_type: RelationshipType,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """ソースエンティティが存在しない場合 EntityNotFoundError を発生させる。"""
    use_case = CreateRelationshipUseCase(**deps)

    with pytest.raises(EntityNotFoundError, match="source"):
        await use_case.execute(
            type_id=rel_type.id,
            from_entity_id=uuid4(),  # 存在しない ID
            to_entity_id=to_entity.id,
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_validation_error_on_source_type_constraint(
    rel_type: RelationshipType,
    from_entity: Entity,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """allowed_source_types 制約違反時に ValidationError を発生させる。"""
    # 許可されていないタイプを設定
    rel_type.allowed_source_types = [uuid4()]  # from_entity.type_id とは別の ID

    use_case = CreateRelationshipUseCase(**deps)

    with pytest.raises(ValidationError):
        await use_case.execute(
            type_id=rel_type.id,
            from_entity_id=from_entity.id,
            to_entity_id=to_entity.id,
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_validation_error_on_target_type_constraint(
    rel_type: RelationshipType,
    from_entity: Entity,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """allowed_target_types 制約違反時に ValidationError を発生させる。"""
    rel_type.allowed_target_types = [uuid4()]  # to_entity.type_id とは別の ID

    use_case = CreateRelationshipUseCase(**deps)

    with pytest.raises(ValidationError):
        await use_case.execute(
            type_id=rel_type.id,
            from_entity_id=from_entity.id,
            to_entity_id=to_entity.id,
        )

    deps["uow"].commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_relationship_duplicate_rejected_when_not_allowed(
    rel_type: RelationshipType,
    from_entity: Entity,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """allow_duplicates=False で既存ペアがある場合 DuplicateRelationshipError を発生させる。"""
    rel_type.allow_duplicates = False
    deps["relationship_repo"].exists_by_pair.return_value = True

    use_case = CreateRelationshipUseCase(**deps)

    with pytest.raises(DuplicateRelationshipError):
        await use_case.execute(
            type_id=rel_type.id,
            from_entity_id=from_entity.id,
            to_entity_id=to_entity.id,
        )

    deps["relationship_repo"].exists_by_pair.assert_awaited_once()
    deps["relationship_repo"].create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_relationship_duplicate_allowed_when_flag_true(
    rel_type: RelationshipType,
    from_entity: Entity,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """allow_duplicates=True の場合 exists_by_pair は呼ばれず作成される。"""
    rel_type.allow_duplicates = True

    use_case = CreateRelationshipUseCase(**deps)

    result = await use_case.execute(
        type_id=rel_type.id,
        from_entity_id=from_entity.id,
        to_entity_id=to_entity.id,
    )

    deps["relationship_repo"].exists_by_pair.assert_not_awaited()
    deps["relationship_repo"].create.assert_awaited_once()
    assert result.type_name == "belongs_to"


@pytest.mark.asyncio
async def test_create_relationship_non_directional_checks_reverse_pair(
    rel_type: RelationshipType,
    from_entity: Entity,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """directional=False, allow_duplicates=False で逆方向ペアが存在する場合エラー。"""
    rel_type.allow_duplicates = False
    rel_type.directional = False
    # 順方向は存在しないが、逆方向は存在する
    deps["relationship_repo"].exists_by_pair.side_effect = [False, True]

    use_case = CreateRelationshipUseCase(**deps)

    with pytest.raises(DuplicateRelationshipError):
        await use_case.execute(
            type_id=rel_type.id,
            from_entity_id=from_entity.id,
            to_entity_id=to_entity.id,
        )

    assert deps["relationship_repo"].exists_by_pair.await_count == 2
    deps["relationship_repo"].create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_relationship_non_directional_both_clear(
    rel_type: RelationshipType,
    from_entity: Entity,
    to_entity: Entity,
    deps: dict[str, AsyncMock],
) -> None:
    """directional=False, allow_duplicates=False で両方向ともクリアなら作成成功。"""
    rel_type.allow_duplicates = False
    rel_type.directional = False
    # 順方向も逆方向も存在しない
    deps["relationship_repo"].exists_by_pair.side_effect = [False, False]

    use_case = CreateRelationshipUseCase(**deps)

    result = await use_case.execute(
        type_id=rel_type.id,
        from_entity_id=from_entity.id,
        to_entity_id=to_entity.id,
    )

    assert deps["relationship_repo"].exists_by_pair.await_count == 2
    deps["relationship_repo"].create.assert_awaited_once()
    assert result.type_name == "belongs_to"
