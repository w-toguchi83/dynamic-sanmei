"""リレーションシップ一括更新ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from dynamic_ontology.domain.exceptions import BatchOperationError
from dynamic_ontology.domain.models.batch import BatchItemError
from dynamic_ontology.domain.models.relationship import Relationship

if TYPE_CHECKING:
    from dynamic_ontology.domain.models.batch import BatchResult
    from dynamic_ontology.domain.ports.repository import RelationshipRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class BatchUpdateRelationshipItem:
    """一括更新の個別アイテム。"""

    id: UUID
    properties: dict[str, Any]
    version: int


class BatchUpdateRelationshipsUseCase:
    """リレーションシップを一括更新するユースケース。

    All-or-nothing: バリデーションエラーが1件でもあればロールバック。
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
        items: list[BatchUpdateRelationshipItem],
        principal_id: str | None = None,
    ) -> BatchResult:
        """リレーションシップを一括更新する。

        Args:
            items: 更新対象リスト.
            principal_id: 操作者ID.

        Returns:
            BatchResult.

        Raises:
            BatchOperationError: バリデーションエラー時.
        """
        updates: list[tuple[Relationship, int]] = []
        errors: list[BatchItemError] = []

        for index, item in enumerate(items):
            existing = await self._relationship_repo.get_by_id(str(item.id))
            if existing is None:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=item.id,
                        message=f"Relationship {item.id} not found",
                    )
                )
                continue

            merged = {**existing.properties, **item.properties}
            now = datetime.now(UTC)
            updated = Relationship(
                id=existing.id,
                type_id=existing.type_id,
                from_entity_id=existing.from_entity_id,
                to_entity_id=existing.to_entity_id,
                version=item.version + 1,
                properties=merged,
                created_at=existing.created_at,
                updated_at=now,
                changed_by=principal_id,
            )
            updates.append((updated, item.version))

        if errors:
            raise BatchOperationError(errors=errors, operation="update")

        result = await self._relationship_repo.update_many(updates)

        if not result.success:
            await self._uow.rollback()

        return result
