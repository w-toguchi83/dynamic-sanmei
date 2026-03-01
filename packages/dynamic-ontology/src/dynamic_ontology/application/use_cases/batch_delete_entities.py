"""エンティティ一括削除ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from dynamic_ontology.domain.models.batch import BatchResult
    from dynamic_ontology.domain.ports.repository import EntityRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork


class BatchDeleteEntitiesUseCase:
    """エンティティを一括削除するユースケース。

    All-or-nothing: リポジトリが失敗を返した場合はロールバック。
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
        entity_ids: list[UUID],
    ) -> BatchResult:
        """エンティティを一括削除する。

        Args:
            entity_ids: 削除対象のエンティティID一覧.

        Returns:
            BatchResult.
        """
        result = await self._entity_repo.delete_many([str(eid) for eid in entity_ids])

        if not result.success:
            await self._uow.rollback()

        return result
