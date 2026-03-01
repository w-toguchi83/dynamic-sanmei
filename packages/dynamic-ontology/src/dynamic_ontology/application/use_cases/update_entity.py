"""エンティティ更新ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.entity import Entity

if TYPE_CHECKING:
    from dynamic_ontology.domain.ports.repository import EntityRepository, EntityTypeRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork
    from dynamic_ontology.domain.services.validation import ValidationEngine


@dataclass(frozen=True)
class UpdateEntityResult:
    """エンティティ更新結果。"""

    entity: Entity
    entity_type_name: str
    before_properties: dict[str, Any]

    @property
    def id(self) -> UUID:
        return self.entity.id

    @property
    def type_id(self) -> UUID:
        return self.entity.type_id

    @property
    def version(self) -> int:
        return self.entity.version

    @property
    def properties(self) -> dict[str, Any]:
        return self.entity.properties


class UpdateEntityUseCase:
    """エンティティを更新し、バリデーション・永続化を行うユースケース。

    コミットはルートハンドラ側で Outbox 書き込み後に実行される。
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
        entity_id: UUID,
        properties: dict[str, Any],
        current_version: int,
        principal_id: str | None = None,
    ) -> UpdateEntityResult:
        """エンティティを更新する。

        Args:
            entity_id: 更新対象のエンティティID.
            properties: 更新するプロパティ（既存プロパティとマージされる）.
            current_version: 楽観的ロック用の現在バージョン.
            principal_id: 操作者ID.

        Returns:
            更新結果（更新後エンティティ + タイプ名 + 更新前プロパティ）.

        Raises:
            EntityNotFoundError: エンティティまたはタイプが存在しない場合.
            ValidationError: プロパティがバリデーションに失敗した場合.
            VersionConflictError: バージョン競合が発生した場合.
        """
        existing = await self._entity_repo.get_by_id(str(entity_id))
        if existing is None:
            raise EntityNotFoundError(str(entity_id), "Entity")

        entity_type = await self._entity_type_repo.get_by_id(str(existing.type_id))
        if entity_type is None:
            raise EntityNotFoundError(str(existing.type_id), "EntityType")

        merged_properties = {**existing.properties, **properties}
        validated_properties = self._validation_engine.validate_and_apply_defaults(
            merged_properties,
            entity_type,
            existing_properties=existing.properties,
        )

        before_properties = existing.properties

        now = datetime.now(UTC)
        updated_entity = Entity(
            id=existing.id,
            type_id=existing.type_id,
            version=existing.version,
            properties=validated_properties,
            created_at=existing.created_at,
            updated_at=now,
            changed_by=principal_id,
        )

        updated = await self._entity_repo.update(updated_entity, current_version)

        return UpdateEntityResult(
            entity=updated,
            entity_type_name=entity_type.name,
            before_properties=before_properties,
        )
