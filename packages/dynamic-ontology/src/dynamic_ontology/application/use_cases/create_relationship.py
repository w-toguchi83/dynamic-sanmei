"""リレーションシップ作成ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from dynamic_ontology.domain.exceptions import (
    DuplicateRelationshipError,
    EntityNotFoundError,
    ValidationError,
)
from dynamic_ontology.domain.models.relationship import Relationship

if TYPE_CHECKING:
    from dynamic_ontology.domain.ports.repository import (
        EntityRepository,
        RelationshipRepository,
        RelationshipTypeRepository,
    )
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CreateRelationshipResult:
    """リレーションシップ作成結果。"""

    relationship: Relationship
    type_name: str

    @property
    def id(self) -> UUID:
        return self.relationship.id

    @property
    def type_id(self) -> UUID:
        return self.relationship.type_id


class CreateRelationshipUseCase:
    """リレーションシップを作成し、バリデーション・永続化を行うユースケース。

    コミットはルートハンドラ側で Outbox 書き込み後に実行される。
    """

    def __init__(
        self,
        *,
        relationship_type_repo: RelationshipTypeRepository,
        relationship_repo: RelationshipRepository,
        entity_repo: EntityRepository,
        uow: UnitOfWork,
    ) -> None:
        self._relationship_type_repo = relationship_type_repo
        self._relationship_repo = relationship_repo
        self._entity_repo = entity_repo
        self._uow = uow

    async def execute(
        self,
        *,
        type_id: UUID,
        from_entity_id: UUID,
        to_entity_id: UUID,
        properties: dict[str, Any] | None = None,
        principal_id: str | None = None,
    ) -> CreateRelationshipResult:
        """リレーションシップを作成する。

        Args:
            type_id: リレーションシップタイプID.
            from_entity_id: ソースエンティティID.
            to_entity_id: ターゲットエンティティID.
            properties: リレーションシップのプロパティ.
            principal_id: 操作者ID.

        Returns:
            作成結果（リレーションシップ + タイプ名）.

        Raises:
            EntityNotFoundError: タイプまたはエンティティが存在しない場合.
            ValidationError: source/target タイプ制約に違反した場合.
        """
        rel_type = await self._relationship_type_repo.get_by_id(str(type_id))
        if rel_type is None:
            raise EntityNotFoundError(str(type_id), "RelationshipType")

        from_entity = await self._entity_repo.get_by_id(str(from_entity_id))
        if from_entity is None:
            raise EntityNotFoundError(str(from_entity_id), "Entity (source)")

        to_entity = await self._entity_repo.get_by_id(str(to_entity_id))
        if to_entity is None:
            raise EntityNotFoundError(str(to_entity_id), "Entity (target)")

        # allowed_source_types / allowed_target_types 制約チェック
        if rel_type.allowed_source_types and from_entity.type_id not in rel_type.allowed_source_types:
            raise ValidationError(
                [
                    {
                        "field": "from_entity_id",
                        "message": (
                            f"Source entity type {from_entity.type_id} is not allowed"
                            f" for relationship type {rel_type.name}"
                        ),
                    }
                ]
            )

        if rel_type.allowed_target_types and to_entity.type_id not in rel_type.allowed_target_types:
            raise ValidationError(
                [
                    {
                        "field": "to_entity_id",
                        "message": (
                            f"Target entity type {to_entity.type_id} is not allowed"
                            f" for relationship type {rel_type.name}"
                        ),
                    }
                ]
            )

        # 重複リレーションチェック
        if not rel_type.allow_duplicates:
            exists = await self._relationship_repo.exists_by_pair(
                type_id=str(type_id),
                from_entity_id=str(from_entity_id),
                to_entity_id=str(to_entity_id),
            )
            if exists:
                raise DuplicateRelationshipError(
                    type_id=str(type_id),
                    from_entity_id=str(from_entity_id),
                    to_entity_id=str(to_entity_id),
                )
            # directional=false の場合、逆方向もチェック
            if not rel_type.directional:
                reverse_exists = await self._relationship_repo.exists_by_pair(
                    type_id=str(type_id),
                    from_entity_id=str(to_entity_id),
                    to_entity_id=str(from_entity_id),
                )
                if reverse_exists:
                    raise DuplicateRelationshipError(
                        type_id=str(type_id),
                        from_entity_id=str(from_entity_id),
                        to_entity_id=str(to_entity_id),
                    )

        now = datetime.now(UTC)
        relationship = Relationship(
            id=uuid4(),
            type_id=type_id,
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            version=1,
            properties=properties or {},
            created_at=now,
            updated_at=now,
            changed_by=principal_id,
        )

        created = await self._relationship_repo.create(relationship)

        return CreateRelationshipResult(
            relationship=created,
            type_name=rel_type.name,
        )
