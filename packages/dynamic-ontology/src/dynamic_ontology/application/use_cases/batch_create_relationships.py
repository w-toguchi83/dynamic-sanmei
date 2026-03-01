"""リレーションシップ一括作成ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from dynamic_ontology.domain.exceptions import BatchOperationError
from dynamic_ontology.domain.models.batch import BatchItemError
from dynamic_ontology.domain.models.relationship import Relationship

if TYPE_CHECKING:
    from dynamic_ontology.domain.models.batch import BatchResult
    from dynamic_ontology.domain.ports.repository import (
        EntityRepository,
        RelationshipRepository,
        RelationshipTypeRepository,
    )
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class BatchCreateRelationshipItem:
    """一括作成の個別アイテム。"""

    type_id: UUID
    from_entity_id: UUID
    to_entity_id: UUID
    properties: dict[str, Any]


class BatchCreateRelationshipsUseCase:
    """リレーションシップを一括作成するユースケース。

    All-or-nothing: バリデーションエラーが1件でもあればロールバック。
    """

    def __init__(
        self,
        *,
        relationship_type_repo: RelationshipTypeRepository,
        entity_repo: EntityRepository,
        relationship_repo: RelationshipRepository,
        uow: UnitOfWork,
    ) -> None:
        self._relationship_type_repo = relationship_type_repo
        self._entity_repo = entity_repo
        self._relationship_repo = relationship_repo
        self._uow = uow

    async def execute(
        self,
        *,
        items: list[BatchCreateRelationshipItem],
        principal_id: str | None = None,
    ) -> BatchResult:
        """リレーションシップを一括作成する。

        Args:
            items: 作成対象リスト.
            principal_id: 操作者ID.

        Returns:
            BatchResult.

        Raises:
            BatchOperationError: バリデーションエラー時.
        """
        relationships: list[Relationship] = []
        errors: list[BatchItemError] = []
        seen_pairs: set[tuple[str, str, str]] = set()

        for index, item in enumerate(items):
            rel_type = await self._relationship_type_repo.get_by_id(str(item.type_id))
            if rel_type is None:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=None,
                        message=f"RelationshipType {item.type_id} not found",
                    )
                )
                continue

            from_entity = await self._entity_repo.get_by_id(str(item.from_entity_id))
            if from_entity is None:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=None,
                        message=f"Entity {item.from_entity_id} not found",
                    )
                )
                continue

            to_entity = await self._entity_repo.get_by_id(str(item.to_entity_id))
            if to_entity is None:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=None,
                        message=f"Entity {item.to_entity_id} not found",
                    )
                )
                continue

            if (
                rel_type.allowed_source_types
                and from_entity.type_id not in rel_type.allowed_source_types
            ):
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=None,
                        message=(
                            f"Entity type of source entity is not allowed "
                            f"for relationship type '{rel_type.name}'"
                        ),
                    )
                )
                continue

            if (
                rel_type.allowed_target_types
                and to_entity.type_id not in rel_type.allowed_target_types
            ):
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=None,
                        message=(
                            f"Entity type of target entity is not allowed "
                            f"for relationship type '{rel_type.name}'"
                        ),
                    )
                )
                continue

            # 重複リレーションチェック
            if not rel_type.allow_duplicates:
                pair_key = (str(item.type_id), str(item.from_entity_id), str(item.to_entity_id))
                reverse_key = (str(item.type_id), str(item.to_entity_id), str(item.from_entity_id))

                # DB 重複チェック
                db_exists = await self._relationship_repo.exists_by_pair(
                    type_id=str(item.type_id),
                    from_entity_id=str(item.from_entity_id),
                    to_entity_id=str(item.to_entity_id),
                )
                if db_exists:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=None,
                            message=(
                                f"Duplicate relationship: type={item.type_id}, "
                                f"from={item.from_entity_id}, to={item.to_entity_id} already exists"
                            ),
                        )
                    )
                    continue

                # directional=false の場合、逆方向の DB チェック
                if not rel_type.directional:
                    reverse_exists = await self._relationship_repo.exists_by_pair(
                        type_id=str(item.type_id),
                        from_entity_id=str(item.to_entity_id),
                        to_entity_id=str(item.from_entity_id),
                    )
                    if reverse_exists:
                        errors.append(
                            BatchItemError(
                                index=index,
                                entity_id=None,
                                message=(
                                    f"Duplicate relationship: type={item.type_id}, "
                                    f"from={item.from_entity_id}, to={item.to_entity_id} already exists"
                                ),
                            )
                        )
                        continue

                # バッチ内重複チェック
                if pair_key in seen_pairs:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=None,
                            message=(
                                f"Duplicate relationship within batch: type={item.type_id}, "
                                f"from={item.from_entity_id}, to={item.to_entity_id}"
                            ),
                        )
                    )
                    continue

                if not rel_type.directional and reverse_key in seen_pairs:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=None,
                            message=(
                                f"Duplicate relationship within batch: type={item.type_id}, "
                                f"from={item.from_entity_id}, to={item.to_entity_id}"
                            ),
                        )
                    )
                    continue

                seen_pairs.add(pair_key)

            now = datetime.now(UTC)
            relationship = Relationship(
                id=uuid4(),
                type_id=item.type_id,
                from_entity_id=item.from_entity_id,
                to_entity_id=item.to_entity_id,
                version=1,
                properties=item.properties,
                created_at=now,
                updated_at=now,
                changed_by=principal_id,
            )
            relationships.append(relationship)

        if errors:
            raise BatchOperationError(errors=errors, operation="create")

        result = await self._relationship_repo.create_many(relationships)

        if not result.success:
            await self._uow.rollback()

        return result
