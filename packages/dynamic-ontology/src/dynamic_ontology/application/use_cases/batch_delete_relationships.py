"""リレーションシップ一括削除ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from dynamic_ontology.domain.models.batch import BatchResult
    from dynamic_ontology.domain.ports.repository import RelationshipRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork


class BatchDeleteRelationshipsUseCase:
    """リレーションシップを一括削除するユースケース。

    All-or-nothing: リポジトリが失敗を返した場合はロールバック。
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
        relationship_ids: list[UUID],
    ) -> BatchResult:
        """リレーションシップを一括削除する。

        Args:
            relationship_ids: 削除対象のリレーションシップID一覧.

        Returns:
            BatchResult.
        """
        result = await self._relationship_repo.delete_many([str(rid) for rid in relationship_ids])

        if not result.success:
            await self._uow.rollback()

        return result
