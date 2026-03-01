"""リレーションシップ更新ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.relationship import Relationship

if TYPE_CHECKING:
    from dynamic_ontology.domain.ports.repository import RelationshipRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateRelationshipResult:
    """リレーションシップ更新結果。"""

    relationship: Relationship
    before_properties: dict[str, Any]

    @property
    def id(self) -> UUID:
        return self.relationship.id

    @property
    def version(self) -> int:
        return self.relationship.version

    @property
    def properties(self) -> dict[str, Any]:
        return self.relationship.properties


class UpdateRelationshipUseCase:
    """リレーションシップを更新し、永続化を行うユースケース。

    コミットはルートハンドラ側で Outbox 書き込み後に実行される。
    """

    def __init__(
        self,
        *,
        relationship_repo: RelationshipRepository,
        uow: UnitOfWork,
    ) -> None:
        self._relationship_repo = relationship_repo
        self._uow = uow

    async def execute(
        self,
        *,
        relationship_id: UUID,
        properties: dict[str, Any],
        current_version: int,
        principal_id: str | None = None,
    ) -> UpdateRelationshipResult:
        """リレーションシップを更新する。

        Args:
            relationship_id: 更新対象のリレーションシップID.
            properties: 更新するプロパティ（既存とマージ）.
            current_version: 楽観的ロック用の現在バージョン.
            principal_id: 操作者ID.

        Returns:
            更新結果（更新後リレーションシップ + 更新前プロパティ）.

        Raises:
            EntityNotFoundError: リレーションシップが存在しない場合.
            VersionConflictError: バージョン競合が発生した場合.
        """
        existing = await self._relationship_repo.get_by_id(str(relationship_id))
        if existing is None:
            raise EntityNotFoundError(str(relationship_id), "Relationship")

        before_properties = existing.properties
        merged_properties = {**existing.properties, **properties}

        now = datetime.now(UTC)
        updated_relationship = Relationship(
            id=existing.id,
            type_id=existing.type_id,
            from_entity_id=existing.from_entity_id,
            to_entity_id=existing.to_entity_id,
            version=existing.version,
            properties=merged_properties,
            created_at=existing.created_at,
            updated_at=now,
            changed_by=principal_id,
        )

        updated = await self._relationship_repo.update(
            updated_relationship,
            current_version,
        )

        return UpdateRelationshipResult(
            relationship=updated,
            before_properties=before_properties,
        )
