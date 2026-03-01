"""Repository port definitions (interfaces)."""

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from dynamic_ontology.domain.models.batch import BatchResult
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.entity_type import EntityType
from dynamic_ontology.domain.models.history import EntitySnapshot
from dynamic_ontology.domain.models.relationship import Relationship, RelationshipType


class EntityTypeRepository(Protocol):
    """Repository interface for EntityType."""

    async def create(self, entity_type: EntityType) -> EntityType:
        """Create a new entity type."""
        ...

    async def get_by_id(self, entity_type_id: str) -> EntityType | None:
        """Get entity type by ID."""
        ...

    async def get_by_name(self, name: str) -> EntityType | None:
        """Get entity type by name."""
        ...

    async def list_all(self) -> list[EntityType]:
        """List all entity types."""
        ...

    async def update(self, entity_type: EntityType) -> EntityType:
        """Update an existing entity type."""
        ...

    async def delete(self, entity_type_id: str) -> bool:
        """Delete an entity type."""
        ...


class EntityRepository(Protocol):
    """Repository interface for Entity."""

    async def create(self, entity: Entity) -> Entity:
        """Create a new entity."""
        ...

    async def get_by_id(self, entity_id: str, at_time: str | None = None) -> Entity | None:
        """Get entity by ID, optionally at a specific point in time."""
        ...

    async def list_by_type(
        self,
        type_id: str,
        limit: int = 100,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[Entity], int]:
        """List entities by type with total count.

        Args:
            type_id: エンティティタイプのUUID文字列.
            limit: 最大取得件数.
            offset: スキップ件数（cursor未指定時に使用）.
            cursor: カーソル文字列（指定時はoffsetを無視）.

        Returns:
            (エンティティリスト, 総件数) のタプル.
        """
        ...

    async def update(self, entity: Entity, current_version: int) -> Entity:
        """Update an existing entity with optimistic locking."""
        ...

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity."""
        ...

    async def get_history(self, entity_id: str) -> list[dict[str, Any]]:
        """Get version history for an entity."""
        ...

    async def get_snapshots(self, entity_id: str) -> list[EntitySnapshot]:
        """エンティティの全履歴スナップショットを取得.

        Args:
            entity_id: エンティティのUUID文字列

        Returns:
            バージョン昇順でソートされたEntitySnapshotのリスト
        """
        ...

    async def get_snapshot_by_version(self, entity_id: str, version: int) -> EntitySnapshot | None:
        """指定バージョンのスナップショットを取得.

        Args:
            entity_id: エンティティのUUID文字列
            version: 取得したいバージョン番号

        Returns:
            指定バージョンのEntitySnapshot、見つからなければNone
        """
        ...

    async def get_snapshot_at_time(self, entity_id: str, at_time: datetime) -> EntitySnapshot | None:
        """指定時刻に有効なスナップショットを取得.

        Args:
            entity_id: エンティティのUUID文字列
            at_time: 取得したい時点のdatetime

        Returns:
            指定時刻に有効なEntitySnapshot、見つからなければNone
        """
        ...

    async def create_many(self, entities: list[Entity]) -> BatchResult:
        """Create multiple entities in a single transaction.

        All-or-nothing: if any entity fails validation or creation,
        the entire batch is rolled back.

        Args:
            entities: List of Entity domain models to create.

        Returns:
            BatchResult with success status and entity IDs or errors.
        """
        ...

    async def update_many(self, updates: list[tuple[Entity, int]]) -> BatchResult:
        """Update multiple entities in a single transaction.

        All-or-nothing: if any entity fails validation or update,
        the entire batch is rolled back.

        Args:
            updates: List of (entity, current_version) tuples.

        Returns:
            BatchResult with success status and entity IDs or errors.
        """
        ...

    async def delete_many(self, entity_ids: list[str]) -> BatchResult:
        """Delete multiple entities in a single transaction.

        All-or-nothing: if any entity is not found,
        the entire batch is rolled back.

        Args:
            entity_ids: List of entity UUID strings to delete.

        Returns:
            BatchResult with success status or errors.
        """
        ...


class RelationshipTypeRepository(Protocol):
    """Repository interface for RelationshipType."""

    async def create(self, relationship_type: RelationshipType) -> RelationshipType:
        """Create a new relationship type."""
        ...

    async def get_by_id(self, relationship_type_id: str) -> RelationshipType | None:
        """Get relationship type by ID."""
        ...

    async def get_by_name(self, name: str) -> RelationshipType | None:
        """Get relationship type by name."""
        ...

    async def list_all(self) -> list[RelationshipType]:
        """List all relationship types."""
        ...

    async def update(self, relationship_type: RelationshipType) -> RelationshipType:
        """Update an existing relationship type."""
        ...

    async def delete(self, relationship_type_id: str) -> bool:
        """Delete a relationship type."""
        ...


@runtime_checkable
class RelationshipRepository(Protocol):
    """Repository interface for Relationship."""

    async def create(self, relationship: Relationship) -> Relationship:
        """Create a new relationship."""
        ...

    async def get_by_id(
        self,
        relationship_id: str,
        at_time: str | None = None,
    ) -> Relationship | None:
        """Get relationship by ID, optionally at a specific point in time."""
        ...

    async def list_by_entity(
        self,
        entity_id: str,
        relationship_type: str | None = None,
        direction: str = "both",
        limit: int = 100,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[Relationship], int]:
        """List relationships for an entity with total count.

        Args:
            entity_id: エンティティのUUID文字列.
            relationship_type: フィルタするリレーションタイプID（任意）.
            direction: 方向フィルタ（outgoing, incoming, both）.
            limit: 最大取得件数.
            offset: スキップ件数（cursor未指定時に使用）.
            cursor: カーソル文字列（指定時はoffsetを無視）.

        Returns:
            (リレーションリスト, 総件数) のタプル.
        """
        ...

    async def list_all(
        self,
        type_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[Relationship], int]:
        """リレーションシップを一覧取得する.

        Args:
            type_id: フィルタするリレーションタイプID（任意）.
            limit: 最大取得件数.
            offset: スキップ件数（cursor未指定時に使用）.
            cursor: カーソル文字列（指定時はoffsetを無視）.

        Returns:
            (リレーションリスト, 総件数) のタプル.
        """
        ...

    async def list_by_type(
        self,
        type_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Relationship], int]:
        """リレーションシップタイプ別にリレーションを取得.

        Args:
            type_id: リレーションタイプのUUID文字列.
            limit: 最大取得件数.
            offset: スキップ件数.

        Returns:
            (リレーションリスト, 総件数) のタプル.
        """
        ...

    async def exists_by_pair(
        self,
        type_id: str,
        from_entity_id: str,
        to_entity_id: str,
    ) -> bool:
        """Check if a relationship with the same type and entity pair exists.

        Args:
            type_id: リレーションタイプのUUID文字列.
            from_entity_id: ソースエンティティのUUID文字列.
            to_entity_id: ターゲットエンティティのUUID文字列.

        Returns:
            True if a matching relationship exists, False otherwise.
        """
        ...

    async def update(self, relationship: Relationship, current_version: int) -> Relationship:
        """Update an existing relationship with optimistic locking."""
        ...

    async def delete(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        ...

    async def get_history(self, relationship_id: str) -> list[dict[str, Any]]:
        """Get version history for a relationship."""
        ...

    async def create_many(self, relationships: list[Relationship]) -> BatchResult:
        """Create multiple relationships in a single transaction.

        All-or-nothing: if any relationship fails validation or creation,
        the entire batch is rolled back.

        Args:
            relationships: List of Relationship domain models to create.

        Returns:
            BatchResult with success status and relationship IDs or errors.
        """
        ...

    async def update_many(self, updates: list[tuple[Relationship, int]]) -> BatchResult:
        """Update multiple relationships in a single transaction.

        All-or-nothing: if any relationship fails validation or update,
        the entire batch is rolled back.

        Args:
            updates: List of (relationship, current_version) tuples.

        Returns:
            BatchResult with success status and relationship IDs or errors.
        """
        ...

    async def delete_many(self, relationship_ids: list[str]) -> BatchResult:
        """Delete multiple relationships in a single transaction.

        All-or-nothing: if any relationship is not found,
        the entire batch is rolled back.

        Args:
            relationship_ids: List of relationship UUID strings to delete.

        Returns:
            BatchResult with success status or errors.
        """
        ...
