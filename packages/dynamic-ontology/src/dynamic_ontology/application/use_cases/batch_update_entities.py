"""エンティティ一括更新ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from dynamic_ontology.domain.exceptions import BatchOperationError, ValidationError
from dynamic_ontology.domain.models.batch import BatchItemError
from dynamic_ontology.domain.models.entity import Entity

if TYPE_CHECKING:
    from dynamic_ontology.domain.models.batch import BatchResult
    from dynamic_ontology.domain.ports.repository import EntityRepository, EntityTypeRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork
    from dynamic_ontology.domain.services.validation import ValidationEngine


@dataclass(frozen=True)
class BatchUpdateItem:
    """一括更新の個別アイテム。"""

    id: UUID
    properties: dict[str, Any]
    version: int


class BatchUpdateEntitiesUseCase:
    """エンティティを一括更新するユースケース。

    All-or-nothing: バリデーションエラーが1件でもあればロールバック。
    """

    def __init__(
        self,
        *,
        entity_type_repo: EntityTypeRepository,
        entity_repo: EntityRepository,
        validation_engine: ValidationEngine,
        uow: UnitOfWork,
    ) -> None:
        self._entity_type_repo = entity_type_repo
        self._entity_repo = entity_repo
        self._validation_engine = validation_engine
        self._uow = uow

    async def execute(
        self,
        *,
        items: list[BatchUpdateItem],
        principal_id: str | None = None,
    ) -> BatchResult:
        """エンティティを一括更新する。

        Args:
            items: 更新対象リスト.
            principal_id: 操作者ID.

        Returns:
            BatchResult.

        Raises:
            BatchOperationError: バリデーションエラー時.
        """
        updates: list[tuple[Entity, int]] = []
        errors: list[BatchItemError] = []

        for index, item in enumerate(items):
            existing = await self._entity_repo.get_by_id(str(item.id))
            if existing is None:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=item.id,
                        message=f"Entity {item.id} not found",
                    )
                )
                continue

            entity_type = await self._entity_type_repo.get_by_id(str(existing.type_id))
            if entity_type is None:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=item.id,
                        message=f"EntityType {existing.type_id} not found",
                    )
                )
                continue

            merged = {**existing.properties, **item.properties}

            try:
                validated = self._validation_engine.validate_and_apply_defaults(
                    merged, entity_type, existing_properties=existing.properties
                )
            except ValidationError as e:
                for err in e.errors:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=item.id,
                            message=f"{err['field']}: {err['message']}",
                        )
                    )
                continue

            now = datetime.now(UTC)
            updated_entity = Entity(
                id=existing.id,
                type_id=existing.type_id,
                version=item.version + 1,
                properties=validated,
                created_at=existing.created_at,
                updated_at=now,
                changed_by=principal_id,
            )
            updates.append((updated_entity, item.version))

        if errors:
            raise BatchOperationError(errors=errors, operation="update")

        result = await self._entity_repo.update_many(updates)

        if not result.success:
            await self._uow.rollback()

        return result
