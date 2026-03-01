"""リレーションシップ削除ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

from dynamic_ontology.domain.exceptions import EntityNotFoundError

if TYPE_CHECKING:
    from dynamic_ontology.domain.ports.repository import RelationshipRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class DeleteRelationshipResult:
    """リレーションシップ削除結果（Webhook/監査ログ用に削除前情報を保持）。"""

    relationship_id: UUID
    type_id: UUID
    from_entity_id: UUID
    to_entity_id: UUID
    version: int
    properties: dict[str, Any]


class DeleteRelationshipUseCase:
    """リレーションシップを削除し、永続化を行うユースケース。

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
    ) -> DeleteRelationshipResult:
        """リレーションシップを削除する。

        Args:
            relationship_id: 削除対象のリレーションシップID.

        Returns:
            削除結果（削除前のリレーションシップ情報）.

        Raises:
            EntityNotFoundError: リレーションシップが存在しない場合.
        """
        existing = await self._relationship_repo.get_by_id(str(relationship_id))
        if existing is None:
            raise EntityNotFoundError(str(relationship_id), "Relationship")

        deleted = await self._relationship_repo.delete(str(relationship_id))
        if not deleted:
            raise EntityNotFoundError(str(relationship_id), "Relationship")

        return DeleteRelationshipResult(
            relationship_id=existing.id,
            type_id=existing.type_id,
            from_entity_id=existing.from_entity_id,
            to_entity_id=existing.to_entity_id,
            version=existing.version,
            properties=existing.properties,
        )
