from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID

    from dynamic_ontology.domain.models.entity import Entity
    from dynamic_ontology.domain.models.history import EntityDiff


class OntologyEventHandler(Protocol):
    """動的オントロジーのイベントハンドラー Protocol.

    アプリ側でオーバーライドして、エンティティ変更時の通知を受け取る。
    """

    async def on_entity_created(self, entity: Entity) -> None: ...
    async def on_entity_updated(self, entity: Entity, diff: EntityDiff) -> None: ...
    async def on_entity_deleted(self, entity_id: UUID) -> None: ...
