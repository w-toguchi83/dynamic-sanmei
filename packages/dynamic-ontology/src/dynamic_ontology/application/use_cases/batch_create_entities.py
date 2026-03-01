"""エンティティ一括作成ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from dynamic_ontology.domain.exceptions import BatchOperationError
from dynamic_ontology.domain.models.batch import BatchItemError, BatchResult
from dynamic_ontology.domain.models.entity import Entity

if TYPE_CHECKING:
    from dynamic_ontology.domain.ports.repository import EntityRepository, EntityTypeRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork
    from dynamic_ontology.domain.services.validation import ValidationEngine


@dataclass(frozen=True)
class BatchCreateItem:
    """一括作成の1件分の入力。"""

    type_id: UUID
    properties: dict[str, Any]


class BatchCreateEntitiesUseCase:
    """エンティティを一括作成し、バリデーション・コミットを行うユースケース。

    All-or-nothing: 1件でもバリデーションエラーがあれば全体が失敗する。
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
        items: list[BatchCreateItem],
        principal_id: str | None = None,
    ) -> BatchResult:
        """エンティティを一括作成する。

        Args:
            items: 作成するエンティティのリスト.
            principal_id: 操作者ID.

        Returns:
            BatchResult（成功時は entity_ids を含む）.

        Raises:
            BatchOperationError: バリデーションエラーが1件以上ある場合.
        """
        errors: list[BatchItemError] = []
        entities: list[Entity] = []
        now = datetime.now(UTC)

        # Phase 1: 全件のバリデーション
        for index, item in enumerate(items):
            entity_type = await self._entity_type_repo.get_by_id(str(item.type_id))
            if entity_type is None:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=None,
                        message=f"EntityType {item.type_id} not found",
                    )
                )
                continue

            try:
                validated_properties = self._validation_engine.validate_and_apply_defaults(
                    item.properties,
                    entity_type,
                )
            except Exception as e:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=None,
                        message=str(e),
                    )
                )
                continue

            entities.append(
                Entity(
                    id=uuid4(),
                    type_id=item.type_id,
                    version=1,
                    properties=validated_properties,
                    created_at=now,
                    updated_at=now,
                    changed_by=principal_id,
                )
            )

        # バリデーションエラーがあれば即座に失敗
        if errors:
            raise BatchOperationError(errors=errors, operation="create")

        # Phase 2: 一括作成
        result = await self._entity_repo.create_many(entities)

        if not result.success:
            await self._uow.rollback()

        return result
