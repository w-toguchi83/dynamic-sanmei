"""エンティティ削除ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

from dynamic_ontology.domain.exceptions import EntityNotFoundError

if TYPE_CHECKING:
    from dynamic_ontology.domain.ports.repository import EntityRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class DeleteEntityResult:
    """エンティティ削除結果（Webhook/監査ログ用に削除前の情報を保持）。"""

    entity_id: UUID
    type_id: UUID
    version: int
    properties: dict[str, Any]


class DeleteEntityUseCase:
    """エンティティを削除し、永続化を行うユースケース。

    コミットはルートハンドラ側で Outbox 書き込み後に実行される。
    """

    def __init__(
        self,
        *,
        entity_repo: EntityRepository,
        uow: UnitOfWork,
    ) -> None:
        self._entity_repo = entity_repo
        self._uow = uow

    async def execute(
        self,
        *,
        entity_id: UUID,
    ) -> DeleteEntityResult:
        """エンティティを削除する。

        Args:
            entity_id: 削除対象のエンティティID.

        Returns:
            削除結果（削除前のエンティティ情報）.

        Raises:
            EntityNotFoundError: エンティティが存在しない場合.
        """
        existing = await self._entity_repo.get_by_id(str(entity_id))
        if existing is None:
            raise EntityNotFoundError(str(entity_id), "Entity")

        deleted = await self._entity_repo.delete(str(entity_id))
        if not deleted:
            raise EntityNotFoundError(str(entity_id), "Entity")

        return DeleteEntityResult(
            entity_id=existing.id,
            type_id=existing.type_id,
            version=existing.version,
            properties=existing.properties,
        )
