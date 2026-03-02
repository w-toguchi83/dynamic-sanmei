"""PostgreSQL repository implementation for Entity."""

import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.domain.exceptions import VersionConflictError
from dynamic_ontology.domain.models.batch import BatchItemError, BatchResult
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.history import EntitySnapshot

logger = logging.getLogger(__name__)


class PostgresEntityRepository:
    """PostgreSQL implementation of EntityRepository with history tracking."""

    def __init__(self, session: AsyncSession, namespace_id: str) -> None:
        """Initialize with database session and namespace ID.

        Args:
            session: SQLAlchemy async session for database operations.
            namespace_id: ネームスペース識別子.
        """
        self._session = session
        self._namespace_id = namespace_id

    @property
    def _namespace_where(self) -> str:
        """namespace_id 条件の WHERE 句."""
        return "WHERE namespace_id = :namespace_id"

    @property
    def _namespace_and(self) -> str:
        """namespace_id 条件の AND 句."""
        return "AND namespace_id = :namespace_id"

    def _with_namespace(self, params: dict[str, object]) -> dict[str, object]:
        """パラメータに namespace_id を追加."""
        return {**params, "namespace_id": self._namespace_id}

    async def create(self, entity: Entity) -> Entity:
        """Create a new entity.

        Also records history with operation="CREATE".

        Args:
            entity: The entity domain model to persist.

        Returns:
            The created entity with timestamps from the database.
        """
        namespace_id = self._namespace_id
        now = datetime.now(UTC)

        query = text("""
            INSERT INTO do_entities (
                id, namespace_id, type_id, version, properties,
                search_vector, created_at, updated_at, changed_by
            )
            VALUES (
                :id, :namespace_id, :type_id, :version, :properties,
                to_tsvector('simple', COALESCE(:search_text, '')),
                :created_at, :updated_at, :changed_by
            )
            RETURNING
                id, type_id, version, properties,
                created_at, updated_at, changed_by
        """)

        properties_json = json.dumps(entity.properties)
        result = await self._session.execute(
            query,
            {
                "id": str(entity.id),
                "namespace_id": namespace_id,
                "type_id": str(entity.type_id),
                "version": 1,
                "properties": properties_json,
                "search_text": properties_json,
                "created_at": now,
                "updated_at": now,
                "changed_by": entity.changed_by,
            },
        )

        row = result.fetchone()
        if row is None:
            raise RuntimeError("Failed to create entity")

        created_entity = self._row_to_entity(row)

        # Record history for CREATE operation
        await self._record_history(
            entity_id=str(created_entity.id),
            type_id=str(created_entity.type_id),
            version=created_entity.version,
            properties=created_entity.properties,
            operation="CREATE",
            valid_from=now,
            changed_by=entity.changed_by,
        )

        return created_entity

    async def create_many(self, entities: list[Entity]) -> BatchResult:
        """Create multiple entities in a single transaction.

        All-or-nothing: if any entity fails, no entities are created.
        History is recorded for each successfully created entity.

        Args:
            entities: List of Entity domain models to create.

        Returns:
            BatchResult with success status and entity IDs or errors.
        """
        namespace_id = self._namespace_id
        if not entities:
            return BatchResult(
                success=True,
                total=0,
                succeeded=0,
                failed=0,
                entity_ids=[],
                errors=[],
            )

        now = datetime.now(UTC)
        created_ids: list[UUID] = []
        errors: list[BatchItemError] = []

        for index, entity in enumerate(entities):
            try:
                query = text("""
                    INSERT INTO do_entities (
                        id, namespace_id, type_id, version, properties,
                        search_vector, created_at, updated_at, changed_by
                    )
                    VALUES (
                        :id, :namespace_id, :type_id, :version, :properties,
                        to_tsvector('simple', COALESCE(:search_text, '')),
                        :created_at, :updated_at, :changed_by
                    )
                    RETURNING id
                """)

                properties_json = json.dumps(entity.properties)
                result = await self._session.execute(
                    query,
                    {
                        "id": str(entity.id),
                        "namespace_id": namespace_id,
                        "type_id": str(entity.type_id),
                        "version": 1,
                        "properties": properties_json,
                        "search_text": properties_json,
                        "created_at": now,
                        "updated_at": now,
                        "changed_by": entity.changed_by,
                    },
                )

                row = result.fetchone()
                if row is None:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=entity.id,
                            message="Failed to create entity",
                        )
                    )
                    continue

                created_ids.append(entity.id)

                # Record history for CREATE operation
                await self._record_history(
                    entity_id=str(entity.id),
                    type_id=str(entity.type_id),
                    version=1,
                    properties=entity.properties,
                    operation="CREATE",
                    valid_from=now,
                    changed_by=entity.changed_by,
                )

            except Exception:
                logger.exception("Batch create entity failed at index %d (id=%s)", index, entity.id)
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=entity.id,
                        message=f"Failed to create entity at index {index}",
                    )
                )

        if errors:
            # Transaction will be rolled back by caller
            return BatchResult(
                success=False,
                total=len(entities),
                succeeded=len(created_ids),
                failed=len(errors),
                entity_ids=[],
                errors=errors,
            )

        return BatchResult(
            success=True,
            total=len(entities),
            succeeded=len(created_ids),
            failed=0,
            entity_ids=created_ids,
            errors=[],
        )

    async def update_many(self, updates: list[tuple[Entity, int]]) -> BatchResult:
        """Update multiple entities in a single transaction.

        All-or-nothing: if any entity fails, no entities are updated.
        History is recorded for each successfully updated entity.

        Args:
            updates: List of (entity, current_version) tuples.

        Returns:
            BatchResult with success status and entity IDs or errors.
        """
        namespace_id = self._namespace_id
        if not updates:
            return BatchResult(
                success=True,
                total=0,
                succeeded=0,
                failed=0,
                entity_ids=[],
                errors=[],
            )

        now = datetime.now(UTC)
        updated_ids: list[UUID] = []
        errors: list[BatchItemError] = []

        for index, (entity, current_version) in enumerate(updates):
            try:
                # Check current version first
                check_query = text("""
                    SELECT version FROM do_entities WHERE id = :id AND namespace_id = :namespace_id
                """)
                check_result = await self._session.execute(
                    check_query, {"id": str(entity.id), "namespace_id": namespace_id}
                )
                check_row = check_result.fetchone()

                if check_row is None:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=entity.id,
                            message=f"Entity {entity.id} not found",
                        )
                    )
                    continue

                db_version = check_row[0]
                if db_version != current_version:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=entity.id,
                            message=f"Version conflict: expected {current_version}, got {db_version}",
                        )
                    )
                    continue

                new_version = current_version + 1

                # Perform update
                update_query = text("""
                    UPDATE do_entities
                    SET version = :new_version,
                        properties = :properties,
                        search_vector = to_tsvector('simple', COALESCE(:search_text, '')),
                        updated_at = :updated_at,
                        changed_by = :changed_by
                    WHERE id = :id AND namespace_id = :namespace_id AND version = :current_version
                    RETURNING id
                """)

                properties_json = json.dumps(entity.properties)
                result = await self._session.execute(
                    update_query,
                    {
                        "id": str(entity.id),
                        "namespace_id": namespace_id,
                        "new_version": new_version,
                        "properties": properties_json,
                        "search_text": properties_json,
                        "updated_at": now,
                        "current_version": current_version,
                        "changed_by": entity.changed_by,
                    },
                )

                row = result.fetchone()
                if row is None:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=entity.id,
                            message="Failed to update entity (concurrent modification)",
                        )
                    )
                    continue

                updated_ids.append(entity.id)

                # Close previous history record
                await self._close_history_record(str(entity.id), now)

                # Record history for UPDATE operation
                await self._record_history(
                    entity_id=str(entity.id),
                    type_id=str(entity.type_id),
                    version=new_version,
                    properties=entity.properties,
                    operation="UPDATE",
                    valid_from=now,
                    changed_by=entity.changed_by,
                )

            except Exception:
                logger.exception("Batch update entity failed at index %d (id=%s)", index, entity.id)
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=entity.id,
                        message=f"Failed to update entity at index {index}",
                    )
                )

        if errors:
            return BatchResult(
                success=False,
                total=len(updates),
                succeeded=len(updated_ids),
                failed=len(errors),
                entity_ids=[],
                errors=errors,
            )

        return BatchResult(
            success=True,
            total=len(updates),
            succeeded=len(updated_ids),
            failed=0,
            entity_ids=updated_ids,
            errors=[],
        )

    async def delete_many(self, entity_ids: list[str]) -> BatchResult:
        """Delete multiple entities in a single transaction.

        All-or-nothing: if any entity is not found, no entities are deleted.

        Args:
            entity_ids: List of entity UUID strings to delete.

        Returns:
            BatchResult with success status or errors.
        """
        namespace_id = self._namespace_id
        if not entity_ids:
            return BatchResult(
                success=True,
                total=0,
                succeeded=0,
                failed=0,
                entity_ids=[],
                errors=[],
            )

        deleted_ids: list[UUID] = []
        errors: list[BatchItemError] = []

        for index, entity_id in enumerate(entity_ids):
            try:
                # Check if entity exists
                check_query = text("""
                    SELECT id FROM do_entities WHERE id = :id AND namespace_id = :namespace_id
                """)
                check_result = await self._session.execute(check_query, {"id": entity_id, "namespace_id": namespace_id})
                if check_result.fetchone() is None:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=UUID(entity_id),
                            message=f"Entity {entity_id} not found",
                        )
                    )
                    continue

                # Delete history first
                delete_history_query = text("""
                    DELETE FROM do_entity_history WHERE entity_id = :id AND namespace_id = :namespace_id
                """)
                await self._session.execute(delete_history_query, {"id": entity_id, "namespace_id": namespace_id})

                # Delete entity
                delete_query = text("""
                    DELETE FROM do_entities WHERE id = :id AND namespace_id = :namespace_id RETURNING id
                """)
                result = await self._session.execute(delete_query, {"id": entity_id, "namespace_id": namespace_id})
                row = result.fetchone()

                if row is not None:
                    deleted_ids.append(UUID(entity_id))

            except Exception as e:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=UUID(entity_id) if entity_id else None,
                        message=str(e),
                    )
                )

        if errors:
            return BatchResult(
                success=False,
                total=len(entity_ids),
                succeeded=len(deleted_ids),
                failed=len(errors),
                entity_ids=[],
                errors=errors,
            )

        return BatchResult(
            success=True,
            total=len(entity_ids),
            succeeded=len(deleted_ids),
            failed=0,
            entity_ids=deleted_ids,
            errors=[],
        )

    async def get_by_id(self, entity_id: str, at_time: str | None = None) -> Entity | None:
        """Get entity by ID, optionally at a specific point in time.

        Supports time-travel queries.

        Args:
            entity_id: The UUID string of the entity.
            at_time: Optional ISO format timestamp for time-travel query.

        Returns:
            The entity if found, None otherwise.
        """
        if at_time is not None:
            return await self._get_entity_at_time(entity_id, at_time)

        query = text(f"""
            SELECT id, type_id, version, properties, created_at, updated_at, changed_by
            FROM do_entities
            WHERE id = :id {self._namespace_and}
        """)

        result = await self._session.execute(query, self._with_namespace({"id": entity_id}))
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_entity(row)

    async def _get_entity_at_time(self, entity_id: str, at_time: str) -> Entity | None:
        """Get entity state at a specific point in time from history.

        Args:
            entity_id: The UUID string of the entity.
            at_time: ISO format timestamp for time-travel query.

        Returns:
            The entity at that point in time, or None if not found.
        """
        # Parse the timestamp
        try:
            timestamp = datetime.fromisoformat(at_time.replace("Z", "+00:00"))
        except ValueError:
            timestamp = datetime.fromisoformat(at_time)

        query = text(f"""
            SELECT entity_id, type_id, version, properties, valid_from, valid_to
            FROM do_entity_history
            WHERE entity_id = :entity_id
              {self._namespace_and}
              AND valid_from <= :at_time
              AND (valid_to IS NULL OR valid_to > :at_time)
            ORDER BY version DESC
            LIMIT 1
        """)

        result = await self._session.execute(
            query,
            self._with_namespace({"entity_id": entity_id, "at_time": timestamp}),
        )
        row = result.fetchone()

        if row is None:
            return None

        # Convert history row to Entity
        if hasattr(row, "_mapping"):
            row_dict = dict(row._mapping)
        else:
            row_dict = {
                "entity_id": row[0],
                "type_id": row[1],
                "version": row[2],
                "properties": row[3],
                "valid_from": row[4],
                "valid_to": row[5],
            }

        properties = row_dict["properties"]
        if isinstance(properties, str):
            properties = json.loads(properties)

        entity_id_uuid = row_dict["entity_id"]
        if isinstance(entity_id_uuid, str):
            entity_id_uuid = UUID(entity_id_uuid)

        type_id_uuid = row_dict["type_id"]
        if isinstance(type_id_uuid, str):
            type_id_uuid = UUID(type_id_uuid)

        return Entity(
            id=entity_id_uuid,
            type_id=type_id_uuid,
            version=row_dict["version"],
            properties=properties,
            created_at=row_dict["valid_from"],
            updated_at=row_dict["valid_from"],
        )

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
        # 総件数を取得
        count_query = text(f"SELECT COUNT(*) FROM do_entities WHERE type_id = :type_id {self._namespace_and}")
        count_result = await self._session.execute(count_query, self._with_namespace({"type_id": type_id}))
        total = count_result.scalar() or 0

        if cursor is not None:
            from dynamic_ontology.domain.services.cursor import decode_cursor

            cursor_at, cursor_id = decode_cursor(cursor)
            query = text(f"""
                SELECT id, type_id, version, properties, created_at, updated_at, changed_by
                FROM do_entities
                WHERE type_id = :type_id
                  {self._namespace_and}
                  AND (created_at, id) < (:cursor_at, :cursor_id)
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
            """)
            result = await self._session.execute(
                query,
                self._with_namespace(
                    {
                        "type_id": type_id,
                        "cursor_at": cursor_at,
                        "cursor_id": str(cursor_id),
                        "limit": limit,
                    }
                ),
            )
        else:
            query = text(f"""
                SELECT id, type_id, version, properties, created_at, updated_at, changed_by
                FROM do_entities
                WHERE type_id = :type_id {self._namespace_and}
                ORDER BY created_at DESC, id DESC
                LIMIT :limit OFFSET :offset
            """)
            result = await self._session.execute(
                query,
                self._with_namespace({"type_id": type_id, "limit": limit, "offset": offset}),
            )

        rows = result.fetchall()
        return [self._row_to_entity(row) for row in rows], total

    async def update(self, entity: Entity, current_version: int) -> Entity:
        """Update an existing entity with optimistic locking.

        Checks current_version matches DB, raises VersionConflictError on mismatch.
        Increments version and records history.

        Args:
            entity: The entity with updated values.
            current_version: The expected current version for optimistic locking.

        Returns:
            The updated entity with incremented version.

        Raises:
            VersionConflictError: If the current version doesn't match the database.
        """
        namespace_id = self._namespace_id
        now = datetime.now(UTC)
        new_version = current_version + 1

        # First, check the current version in the database
        check_query = text("""
            SELECT version FROM do_entities WHERE id = :id AND namespace_id = :namespace_id
        """)
        check_result = await self._session.execute(check_query, {"id": str(entity.id), "namespace_id": namespace_id})
        check_row = check_result.fetchone()

        if check_row is None:
            raise VersionConflictError(str(entity.id), 0, current_version)

        db_version = check_row[0]
        if db_version != current_version:
            raise VersionConflictError(str(entity.id), db_version, current_version)

        # Update the entity first (before closing history record to prevent race condition)
        update_query = text("""
            UPDATE do_entities
            SET version = :new_version,
                properties = :properties,
                search_vector = to_tsvector('simple', COALESCE(:search_text, '')),
                updated_at = :updated_at,
                changed_by = :changed_by
            WHERE id = :id AND namespace_id = :namespace_id AND version = :current_version
            RETURNING id, type_id, version, properties, created_at, updated_at, changed_by
        """)

        properties_json = json.dumps(entity.properties)
        result = await self._session.execute(
            update_query,
            {
                "id": str(entity.id),
                "namespace_id": namespace_id,
                "new_version": new_version,
                "properties": properties_json,
                "search_text": properties_json,
                "updated_at": now,
                "current_version": current_version,
                "changed_by": entity.changed_by,
            },
        )

        row = result.fetchone()
        if row is None:
            # Race condition - someone else updated between check and update
            raise VersionConflictError(str(entity.id), current_version, current_version)

        updated_entity = self._row_to_entity(row)

        # Close the previous history record AFTER successful update
        # (prevents closing wrong record if concurrent update happens)
        await self._close_history_record(str(entity.id), now)

        # Record history for UPDATE operation
        await self._record_history(
            entity_id=str(updated_entity.id),
            type_id=str(updated_entity.type_id),
            version=updated_entity.version,
            properties=updated_entity.properties,
            operation="UPDATE",
            valid_from=now,
            changed_by=entity.changed_by,
        )

        return updated_entity

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity.

        Args:
            entity_id: The UUID string of the entity to delete.

        Returns:
            True if deleted, False if not found.
        """
        namespace_id = self._namespace_id
        # First delete history records (cascade should handle this, but explicit is safer)
        delete_history_query = text("""
            DELETE FROM do_entity_history WHERE entity_id = :id AND namespace_id = :namespace_id
        """)
        await self._session.execute(delete_history_query, {"id": entity_id, "namespace_id": namespace_id})

        # Then delete the entity
        query = text("""
            DELETE FROM do_entities
            WHERE id = :id AND namespace_id = :namespace_id
            RETURNING id
        """)

        result = await self._session.execute(query, {"id": entity_id, "namespace_id": namespace_id})
        row = result.fetchone()

        return row is not None

    async def get_history(self, entity_id: str) -> list[dict[str, Any]]:
        """Get version history for an entity.

        Args:
            entity_id: The UUID string of the entity.

        Returns:
            List of history records as dictionaries.
        """
        query = text(f"""
            SELECT id, entity_id, type_id, version, properties,
                   valid_from, valid_to, operation, changed_by, created_at
            FROM do_entity_history
            WHERE entity_id = :entity_id {self._namespace_and}
            ORDER BY version ASC
        """)

        result = await self._session.execute(query, self._with_namespace({"entity_id": entity_id}))
        rows = result.fetchall()

        history: list[dict[str, Any]] = []
        for row in rows:
            if hasattr(row, "_mapping"):
                row_dict = dict(row._mapping)
            else:
                row_dict = {
                    "id": row[0],
                    "entity_id": row[1],
                    "type_id": row[2],
                    "version": row[3],
                    "properties": row[4],
                    "valid_from": row[5],
                    "valid_to": row[6],
                    "operation": row[7],
                    "changed_by": row[8],
                    "created_at": row[9],
                }

            properties = row_dict["properties"]
            if isinstance(properties, str):
                properties = json.loads(properties)

            history.append(
                {
                    "id": str(row_dict["id"]),
                    "entity_id": str(row_dict["entity_id"]),
                    "type_id": str(row_dict["type_id"]),
                    "version": row_dict["version"],
                    "properties": properties,
                    "valid_from": row_dict["valid_from"],
                    "valid_to": row_dict["valid_to"],
                    "operation": row_dict["operation"],
                    "changed_by": row_dict["changed_by"],
                    "created_at": row_dict["created_at"],
                }
            )

        return history

    async def _record_history(
        self,
        entity_id: str,
        type_id: str,
        version: int,
        properties: dict[str, Any],
        operation: str,
        valid_from: datetime,
        changed_by: str | None = None,
    ) -> None:
        """Record a history entry for an entity.

        Args:
            entity_id: The UUID string of the entity.
            type_id: The UUID string of the entity type.
            version: The version number of this history record.
            properties: The entity properties at this point in time.
            operation: The operation type (CREATE, UPDATE, DELETE).
            valid_from: The timestamp when this version became valid.
            changed_by: Optional identifier of who made the change.
        """
        query = text("""
            INSERT INTO do_entity_history
                (entity_id, namespace_id, type_id, version, properties, valid_from, valid_to, operation, changed_by)
            VALUES
                (:entity_id, :namespace_id, :type_id, :version, :properties, :valid_from, NULL, :operation, :changed_by)
        """)

        await self._session.execute(
            query,
            {
                "entity_id": entity_id,
                "namespace_id": self._namespace_id,
                "type_id": type_id,
                "version": version,
                "properties": json.dumps(properties),
                "valid_from": valid_from,
                "operation": operation,
                "changed_by": changed_by,
            },
        )

    async def _close_history_record(self, entity_id: str, valid_to: datetime) -> None:
        """Close the current history record by setting valid_to.

        Sets valid_to on the previous history record.

        Args:
            entity_id: The UUID string of the entity.
            valid_to: The timestamp when the current version became invalid.
        """
        query = text("""
            UPDATE do_entity_history
            SET valid_to = :valid_to
            WHERE entity_id = :entity_id
              AND namespace_id = :namespace_id
              AND valid_to IS NULL
        """)

        await self._session.execute(
            query,
            {"entity_id": entity_id, "namespace_id": self._namespace_id, "valid_to": valid_to},
        )

    def _row_to_entity(self, row: Any) -> Entity:
        """Convert database row to Entity domain model.

        Args:
            row: Database row with entity data.

        Returns:
            Entity domain model.
        """
        # Handle both dict-like and tuple-like row access
        if hasattr(row, "_mapping"):
            # SQLAlchemy Row object
            row_dict = dict(row._mapping)
        else:
            # Named tuple or similar
            row_dict = {
                "id": row[0],
                "type_id": row[1],
                "version": row[2],
                "properties": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "changed_by": row[6],
            }

        properties = row_dict["properties"]
        if isinstance(properties, str):
            properties = json.loads(properties)

        # Parse UUID if it's a string
        entity_id = row_dict["id"]
        if isinstance(entity_id, str):
            entity_id = UUID(entity_id)

        type_id = row_dict["type_id"]
        if isinstance(type_id, str):
            type_id = UUID(type_id)

        return Entity(
            id=entity_id,
            type_id=type_id,
            version=row_dict["version"],
            properties=properties,
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
            changed_by=row_dict.get("changed_by"),
        )

    async def get_snapshots(self, entity_id: str) -> list[EntitySnapshot]:
        """エンティティの全履歴スナップショットを取得.

        Args:
            entity_id: エンティティのUUID文字列

        Returns:
            バージョン昇順でソートされたEntitySnapshotのリスト
        """
        query = text(f"""
            SELECT entity_id, type_id, version, properties,
                   valid_from, valid_to, operation
            FROM do_entity_history
            WHERE entity_id = :entity_id {self._namespace_and}
            ORDER BY version ASC
        """)

        result = await self._session.execute(query, self._with_namespace({"entity_id": entity_id}))
        rows = result.fetchall()

        return [self._row_to_snapshot(row) for row in rows]

    async def get_snapshot_by_version(self, entity_id: str, version: int) -> EntitySnapshot | None:
        """指定バージョンのスナップショットを取得.

        Args:
            entity_id: エンティティのUUID文字列
            version: 取得したいバージョン番号

        Returns:
            指定バージョンのEntitySnapshot、見つからなければNone
        """
        query = text(f"""
            SELECT entity_id, type_id, version, properties,
                   valid_from, valid_to, operation
            FROM do_entity_history
            WHERE entity_id = :entity_id {self._namespace_and} AND version = :version
            LIMIT 1
        """)

        result = await self._session.execute(query, self._with_namespace({"entity_id": entity_id, "version": version}))
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_snapshot(row)

    async def get_snapshot_at_time(self, entity_id: str, at_time: datetime) -> EntitySnapshot | None:
        """指定時刻に有効なスナップショットを取得.

        Args:
            entity_id: エンティティのUUID文字列
            at_time: 取得したい時点のdatetime

        Returns:
            指定時刻に有効なEntitySnapshot、見つからなければNone
        """
        query = text(f"""
            SELECT entity_id, type_id, version, properties,
                   valid_from, valid_to, operation
            FROM do_entity_history
            WHERE entity_id = :entity_id
              {self._namespace_and}
              AND valid_from <= :at_time
              AND (valid_to IS NULL OR valid_to > :at_time)
            ORDER BY version DESC
            LIMIT 1
        """)

        result = await self._session.execute(query, self._with_namespace({"entity_id": entity_id, "at_time": at_time}))
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_snapshot(row)

    def _row_to_snapshot(self, row: Any) -> EntitySnapshot:
        """データベース行をEntitySnapshotドメインモデルに変換.

        Args:
            row: entity_historyテーブルからの行データ

        Returns:
            EntitySnapshotドメインモデル
        """
        # Handle both dict-like and tuple-like row access
        if hasattr(row, "_mapping"):
            row_dict = dict(row._mapping)
        else:
            row_dict = {
                "entity_id": row[0],
                "type_id": row[1],
                "version": row[2],
                "properties": row[3],
                "valid_from": row[4],
                "valid_to": row[5],
                "operation": row[6],
            }

        properties = row_dict["properties"]
        if isinstance(properties, str):
            properties = json.loads(properties)

        # Parse UUID if it's a string
        entity_id = row_dict["entity_id"]
        if isinstance(entity_id, str):
            entity_id = UUID(entity_id)

        type_id = row_dict["type_id"]
        if isinstance(type_id, str):
            type_id = UUID(type_id)

        return EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=row_dict["version"],
            properties=properties,
            valid_from=row_dict["valid_from"],
            valid_to=row_dict["valid_to"],
            operation=row_dict["operation"],
        )
