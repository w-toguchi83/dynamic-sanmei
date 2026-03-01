"""エンティティ作成ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.entity import Entity

if TYPE_CHECKING:
    from dynamic_ontology.domain.ports.repository import EntityRepository, EntityTypeRepository
    from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork
    from dynamic_ontology.domain.services.validation import ValidationEngine


@dataclass(frozen=True)
class CreateEntityResult:
    """エンティティ作成結果。"""

    entity: Entity
    entity_type_name: str

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

    @property
    def created_at(self) -> datetime:
        return self.entity.created_at

    @property
    def updated_at(self) -> datetime:
        return self.entity.updated_at


class CreateEntityUseCase:
    """エンティティを作成し、バリデーション・永続化を行うユースケース。

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
        type_id: UUID,
        properties: dict[str, Any],
        principal_id: str | None = None,
    ) -> CreateEntityResult:
        """エンティティを作成する。

        Args:
            type_id: エンティティタイプID.
            properties: エンティティのプロパティ.
            principal_id: 操作者ID.

        Returns:
            作成結果（エンティティ + タイプ名）.

        Raises:
            EntityNotFoundError: エンティティタイプが存在しない場合.
            ValidationError: プロパティがバリデーションに失敗した場合.
        """
        entity_type = await self._entity_type_repo.get_by_id(str(type_id))
        if entity_type is None:
            raise EntityNotFoundError(str(type_id), "EntityType")

        validated_properties = self._validation_engine.validate_and_apply_defaults(
            properties,
            entity_type,
        )

        now = datetime.now(UTC)
        entity = Entity(
            id=uuid4(),
            type_id=type_id,
            version=1,
            properties=validated_properties,
            created_at=now,
            updated_at=now,
            changed_by=principal_id,
        )

        created = await self._entity_repo.create(entity)

        return CreateEntityResult(entity=created, entity_type_name=entity_type.name)
