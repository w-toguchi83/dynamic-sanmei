"""PostgreSQL repository implementation for Relationship."""

import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.domain.exceptions import VersionConflictError
from dynamic_ontology.domain.models.batch import BatchItemError, BatchResult
from dynamic_ontology.domain.models.relationship import Relationship

logger = logging.getLogger(__name__)


class PostgresRelationshipRepository:
    """PostgreSQL implementation of RelationshipRepository with history tracking."""

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

    async def create(self, relationship: Relationship) -> Relationship:
        """Create a new relationship.

        Also records history with operation="CREATE".

        Args:
            relationship: The relationship domain model to persist.

        Returns:
            The created relationship with timestamps from the database.
        """
        namespace_id = self._namespace_id
        now = datetime.now(UTC)

        query = text("""
            INSERT INTO do_relationships
                (id, namespace_id, type_id, from_entity_id, to_entity_id,
                 version, properties, created_at, updated_at, changed_by)
            VALUES
                (:id, :namespace_id, :type_id, :from_entity_id, :to_entity_id,
                 :version, :properties, :created_at, :updated_at, :changed_by)
            RETURNING id, type_id, from_entity_id, to_entity_id, version, properties, created_at, updated_at, changed_by
        """)

        result = await self._session.execute(
            query,
            {
                "id": str(relationship.id),
                "namespace_id": namespace_id,
                "type_id": str(relationship.type_id),
                "from_entity_id": str(relationship.from_entity_id),
                "to_entity_id": str(relationship.to_entity_id),
                "version": 1,
                "properties": json.dumps(relationship.properties),
                "created_at": now,
                "updated_at": now,
                "changed_by": relationship.changed_by,
            },
        )

        row = result.fetchone()
        if row is None:
            raise RuntimeError("Failed to create relationship")

        created_relationship = self._row_to_relationship(row)

        # Record history for CREATE operation
        await self._record_history(
            relationship_id=str(created_relationship.id),
            type_id=str(created_relationship.type_id),
            from_entity_id=str(created_relationship.from_entity_id),
            to_entity_id=str(created_relationship.to_entity_id),
            version=created_relationship.version,
            properties=created_relationship.properties,
            operation="CREATE",
            valid_from=now,
            changed_by=relationship.changed_by,
        )

        return created_relationship

    async def create_many(self, relationships: list[Relationship]) -> BatchResult:
        """Create multiple relationships in a single transaction."""
        namespace_id = self._namespace_id
        if not relationships:
            return BatchResult(success=True, total=0, succeeded=0, failed=0, entity_ids=[], errors=[])

        now = datetime.now(UTC)
        created_ids: list[UUID] = []
        errors: list[BatchItemError] = []

        for index, relationship in enumerate(relationships):
            try:
                query = text("""
                    INSERT INTO do_relationships
                        (id, namespace_id, type_id, from_entity_id, to_entity_id, version, properties,
                         created_at, updated_at, changed_by)
                    VALUES
                        (:id, :namespace_id, :type_id, :from_entity_id, :to_entity_id, :version, :properties,
                         :created_at, :updated_at, :changed_by)
                    RETURNING id
                """)

                result = await self._session.execute(
                    query,
                    {
                        "id": str(relationship.id),
                        "namespace_id": namespace_id,
                        "type_id": str(relationship.type_id),
                        "from_entity_id": str(relationship.from_entity_id),
                        "to_entity_id": str(relationship.to_entity_id),
                        "version": 1,
                        "properties": json.dumps(relationship.properties),
                        "created_at": now,
                        "updated_at": now,
                        "changed_by": relationship.changed_by,
                    },
                )

                row = result.fetchone()
                if row is None:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=relationship.id,
                            message="Failed to create relationship",
                        )
                    )
                    continue

                created_ids.append(relationship.id)

                await self._record_history(
                    relationship_id=str(relationship.id),
                    type_id=str(relationship.type_id),
                    from_entity_id=str(relationship.from_entity_id),
                    to_entity_id=str(relationship.to_entity_id),
                    version=1,
                    properties=relationship.properties,
                    operation="CREATE",
                    valid_from=now,
                    changed_by=relationship.changed_by,
                )

            except Exception:
                logger.exception("Batch create relationship failed at index %d (id=%s)", index, relationship.id)
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=relationship.id,
                        message=f"Failed to create relationship at index {index}",
                    )
                )

        if errors:
            return BatchResult(
                success=False,
                total=len(relationships),
                succeeded=len(created_ids),
                failed=len(errors),
                entity_ids=[],
                errors=errors,
            )

        return BatchResult(
            success=True,
            total=len(relationships),
            succeeded=len(created_ids),
            failed=0,
            entity_ids=created_ids,
            errors=[],
        )

    async def update_many(self, updates: list[tuple[Relationship, int]]) -> BatchResult:
        """Update multiple relationships in a single transaction."""
        namespace_id = self._namespace_id
        if not updates:
            return BatchResult(success=True, total=0, succeeded=0, failed=0, entity_ids=[], errors=[])

        now = datetime.now(UTC)
        updated_ids: list[UUID] = []
        errors: list[BatchItemError] = []

        for index, (relationship, current_version) in enumerate(updates):
            try:
                check_query = text(
                    "SELECT version FROM do_relationships WHERE id = :id AND namespace_id = :namespace_id"
                )
                check_result = await self._session.execute(
                    check_query, {"id": str(relationship.id), "namespace_id": namespace_id}
                )
                check_row = check_result.fetchone()

                if check_row is None:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=relationship.id,
                            message=f"Relationship {relationship.id} not found",
                        )
                    )
                    continue

                db_version = check_row[0]
                if db_version != current_version:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=relationship.id,
                            message=f"Version conflict: expected {current_version}, got {db_version}",
                        )
                    )
                    continue

                new_version = current_version + 1

                update_query = text("""
                    UPDATE do_relationships
                    SET version = :new_version,
                        properties = :properties,
                        updated_at = :updated_at,
                        changed_by = :changed_by
                    WHERE id = :id AND namespace_id = :namespace_id AND version = :current_version
                    RETURNING id
                """)
                result = await self._session.execute(
                    update_query,
                    {
                        "id": str(relationship.id),
                        "namespace_id": namespace_id,
                        "new_version": new_version,
                        "properties": json.dumps(relationship.properties),
                        "updated_at": now,
                        "changed_by": relationship.changed_by,
                        "current_version": current_version,
                    },
                )
                row = result.fetchone()

                if row is None:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=relationship.id,
                            message="Race condition during update",
                        )
                    )
                    continue

                updated_ids.append(relationship.id)

                await self._close_history_record(str(relationship.id), now)
                await self._record_history(
                    relationship_id=str(relationship.id),
                    type_id=str(relationship.type_id),
                    from_entity_id=str(relationship.from_entity_id),
                    to_entity_id=str(relationship.to_entity_id),
                    version=new_version,
                    properties=relationship.properties,
                    operation="UPDATE",
                    valid_from=now,
                    changed_by=relationship.changed_by,
                )

            except Exception:
                logger.exception("Batch update relationship failed at index %d (id=%s)", index, relationship.id)
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=relationship.id,
                        message=f"Failed to update relationship at index {index}",
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

    async def delete_many(self, relationship_ids: list[str]) -> BatchResult:
        """Delete multiple relationships in a single transaction."""
        namespace_id = self._namespace_id
        if not relationship_ids:
            return BatchResult(success=True, total=0, succeeded=0, failed=0, entity_ids=[], errors=[])

        deleted_ids: list[UUID] = []
        errors: list[BatchItemError] = []

        for index, relationship_id in enumerate(relationship_ids):
            try:
                check_query = text("SELECT id FROM do_relationships WHERE id = :id AND namespace_id = :namespace_id")
                check_result = await self._session.execute(
                    check_query, {"id": relationship_id, "namespace_id": namespace_id}
                )
                if check_result.fetchone() is None:
                    errors.append(
                        BatchItemError(
                            index=index,
                            entity_id=UUID(relationship_id),
                            message=f"Relationship {relationship_id} not found",
                        )
                    )
                    continue

                delete_history_query = text(
                    "DELETE FROM do_relationship_history WHERE relationship_id = :id AND namespace_id = :namespace_id"
                )
                await self._session.execute(delete_history_query, {"id": relationship_id, "namespace_id": namespace_id})

                delete_query = text(
                    "DELETE FROM do_relationships WHERE id = :id AND namespace_id = :namespace_id RETURNING id"
                )
                result = await self._session.execute(
                    delete_query, {"id": relationship_id, "namespace_id": namespace_id}
                )
                row = result.fetchone()

                if row is not None:
                    deleted_ids.append(UUID(relationship_id))

            except Exception as e:
                errors.append(
                    BatchItemError(
                        index=index,
                        entity_id=UUID(relationship_id) if relationship_id else None,
                        message=str(e),
                    )
                )

        if errors:
            return BatchResult(
                success=False,
                total=len(relationship_ids),
                succeeded=len(deleted_ids),
                failed=len(errors),
                entity_ids=[],
                errors=errors,
            )

        return BatchResult(
            success=True,
            total=len(relationship_ids),
            succeeded=len(deleted_ids),
            failed=0,
            entity_ids=deleted_ids,
            errors=[],
        )

    async def get_by_id(self, relationship_id: str, at_time: str | None = None) -> Relationship | None:
        """Get relationship by ID, optionally at a specific point in time."""
        if at_time is not None:
            return await self._get_relationship_at_time(relationship_id, at_time)

        query = text(f"""
            SELECT id, type_id, from_entity_id, to_entity_id, version, properties, created_at, updated_at, changed_by
            FROM do_relationships
            WHERE id = :id {self._namespace_and}
        """)

        result = await self._session.execute(query, self._with_namespace({"id": relationship_id}))
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_relationship(row)

    async def _get_relationship_at_time(self, relationship_id: str, at_time: str) -> Relationship | None:
        """Get relationship state at a specific point in time from history."""
        try:
            timestamp = datetime.fromisoformat(at_time.replace("Z", "+00:00"))
        except ValueError:
            timestamp = datetime.fromisoformat(at_time)

        query = text(f"""
            SELECT relationship_id, type_id, from_entity_id, to_entity_id, version, properties, valid_from, valid_to
            FROM do_relationship_history
            WHERE relationship_id = :relationship_id
              {self._namespace_and}
              AND valid_from <= :at_time
              AND (valid_to IS NULL OR valid_to > :at_time)
            ORDER BY version DESC
            LIMIT 1
        """)

        result = await self._session.execute(
            query,
            self._with_namespace({"relationship_id": relationship_id, "at_time": timestamp}),
        )
        row = result.fetchone()

        if row is None:
            return None

        if hasattr(row, "_mapping"):
            row_dict = dict(row._mapping)
        else:
            row_dict = {
                "relationship_id": row[0],
                "type_id": row[1],
                "from_entity_id": row[2],
                "to_entity_id": row[3],
                "version": row[4],
                "properties": row[5],
                "valid_from": row[6],
                "valid_to": row[7],
            }

        properties = row_dict["properties"]
        if isinstance(properties, str):
            properties = json.loads(properties)

        relationship_id_uuid = row_dict["relationship_id"]
        if isinstance(relationship_id_uuid, str):
            relationship_id_uuid = UUID(relationship_id_uuid)

        type_id_uuid = row_dict["type_id"]
        if isinstance(type_id_uuid, str):
            type_id_uuid = UUID(type_id_uuid)

        from_entity_id_uuid = row_dict["from_entity_id"]
        if isinstance(from_entity_id_uuid, str):
            from_entity_id_uuid = UUID(from_entity_id_uuid)

        to_entity_id_uuid = row_dict["to_entity_id"]
        if isinstance(to_entity_id_uuid, str):
            to_entity_id_uuid = UUID(to_entity_id_uuid)

        return Relationship(
            id=relationship_id_uuid,
            type_id=type_id_uuid,
            from_entity_id=from_entity_id_uuid,
            to_entity_id=to_entity_id_uuid,
            version=row_dict["version"],
            properties=properties,
            created_at=row_dict["valid_from"],
            updated_at=row_dict["valid_from"],
        )

    async def list_by_entity(
        self,
        entity_id: str,
        relationship_type: str | None = None,
        direction: str = "both",
        limit: int = 100,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[Relationship], int]:
        """List relationships by entity with total count."""
        if direction == "outgoing":
            direction_condition = "from_entity_id = :entity_id"
        elif direction == "incoming":
            direction_condition = "to_entity_id = :entity_id"
        else:
            direction_condition = "(from_entity_id = :entity_id OR to_entity_id = :entity_id)"

        conditions = [direction_condition, "namespace_id = :namespace_id"]
        params: dict[str, str | int | datetime] = {
            "entity_id": entity_id,
            "namespace_id": self._namespace_id,
        }

        if relationship_type is not None:
            conditions.append("type_id = :type_id")
            params["type_id"] = relationship_type

        where_clause = " AND ".join(conditions)

        count_query = text(f"SELECT COUNT(*) FROM do_relationships WHERE {where_clause}")
        count_result = await self._session.execute(count_query, params)
        count_row = count_result.fetchone()
        total = count_row[0] if count_row else 0

        data_conditions = list(conditions)
        data_params = dict(params)

        if cursor is not None:
            from dynamic_ontology.domain.services.cursor import decode_cursor

            cursor_created_at, cursor_id = decode_cursor(cursor)
            data_conditions.append("(created_at, id) < (:cursor_at, :cursor_id)")
            data_params["cursor_at"] = cursor_created_at
            data_params["cursor_id"] = str(cursor_id)

        data_where = " AND ".join(data_conditions)

        if cursor is not None:
            data_query = text(f"""
                SELECT id, type_id, from_entity_id, to_entity_id, version, properties,
                       created_at, updated_at, changed_by
                FROM do_relationships
                WHERE {data_where}
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
            """)
            data_params["limit"] = limit
        else:
            data_query = text(f"""
                SELECT id, type_id, from_entity_id, to_entity_id, version, properties,
                       created_at, updated_at, changed_by
                FROM do_relationships
                WHERE {data_where}
                ORDER BY created_at DESC, id DESC
                LIMIT :limit OFFSET :offset
            """)
            data_params["limit"] = limit
            data_params["offset"] = offset

        result = await self._session.execute(data_query, data_params)
        rows = result.fetchall()

        return [self._row_to_relationship(row) for row in rows], total

    async def list_all(
        self,
        type_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[Relationship], int]:
        """リレーションシップを一覧取得する（オプションでタイプフィルタ・カーソルページネーション対応）."""
        conditions = ["namespace_id = :namespace_id"]
        params: dict[str, str | int | datetime] = {"namespace_id": self._namespace_id}

        if type_id is not None:
            conditions.append("type_id = :type_id")
            params["type_id"] = type_id

        where_clause = " AND ".join(conditions)

        # 総件数を取得
        count_query = text(f"SELECT COUNT(*) FROM do_relationships WHERE {where_clause}")
        count_result = await self._session.execute(count_query, params)
        count_row = count_result.fetchone()
        total = count_row[0] if count_row else 0

        # データ取得用の条件とパラメータ
        data_conditions = list(conditions)
        data_params = dict(params)

        if cursor is not None:
            from dynamic_ontology.domain.services.cursor import decode_cursor

            cursor_created_at, cursor_id = decode_cursor(cursor)
            data_conditions.append("(created_at, id) < (:cursor_at, :cursor_id)")
            data_params["cursor_at"] = cursor_created_at
            data_params["cursor_id"] = str(cursor_id)

        data_where = " AND ".join(data_conditions)

        if cursor is not None:
            data_query = text(f"""
                SELECT id, type_id, from_entity_id, to_entity_id, version, properties,
                       created_at, updated_at, changed_by
                FROM do_relationships
                WHERE {data_where}
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
            """)
            data_params["limit"] = limit
        else:
            data_query = text(f"""
                SELECT id, type_id, from_entity_id, to_entity_id, version, properties,
                       created_at, updated_at, changed_by
                FROM do_relationships
                WHERE {data_where}
                ORDER BY created_at DESC, id DESC
                LIMIT :limit OFFSET :offset
            """)
            data_params["limit"] = limit
            data_params["offset"] = offset

        result = await self._session.execute(data_query, data_params)
        rows = result.fetchall()

        return [self._row_to_relationship(row) for row in rows], total

    async def list_by_type(self, type_id: str, limit: int = 100, offset: int = 0) -> tuple[list[Relationship], int]:
        """List relationships by type with total count."""
        count_query = text(f"SELECT COUNT(*) FROM do_relationships WHERE type_id = :type_id {self._namespace_and}")
        count_result = await self._session.execute(count_query, self._with_namespace({"type_id": type_id}))
        count_row = count_result.fetchone()
        total = count_row[0] if count_row else 0

        data_query = text(f"""
            SELECT id, type_id, from_entity_id, to_entity_id, version, properties, created_at, updated_at, changed_by
            FROM do_relationships
            WHERE type_id = :type_id {self._namespace_and}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await self._session.execute(
            data_query, self._with_namespace({"type_id": type_id, "limit": limit, "offset": offset})
        )
        rows = result.fetchall()

        return [self._row_to_relationship(row) for row in rows], total

    async def exists_by_pair(
        self,
        type_id: str,
        from_entity_id: str,
        to_entity_id: str,
    ) -> bool:
        """Check if a relationship with the same type and entity pair exists."""
        query = text("""
            SELECT EXISTS(
                SELECT 1 FROM do_relationships
                WHERE type_id = :type_id
                  AND from_entity_id = :from_entity_id
                  AND to_entity_id = :to_entity_id
                  AND namespace_id = :namespace_id
            )
        """)
        result = await self._session.execute(
            query,
            {
                "type_id": type_id,
                "from_entity_id": from_entity_id,
                "to_entity_id": to_entity_id,
                "namespace_id": self._namespace_id,
            },
        )
        row = result.scalar()
        return bool(row)

    async def update(self, relationship: Relationship, current_version: int) -> Relationship:
        """Update an existing relationship with optimistic locking."""
        namespace_id = self._namespace_id
        now = datetime.now(UTC)
        new_version = current_version + 1

        check_query = text("SELECT version FROM do_relationships WHERE id = :id AND namespace_id = :namespace_id")
        check_result = await self._session.execute(
            check_query, {"id": str(relationship.id), "namespace_id": namespace_id}
        )
        check_row = check_result.fetchone()

        if check_row is None:
            raise VersionConflictError(str(relationship.id), 0, current_version)

        db_version = check_row[0]
        if db_version != current_version:
            raise VersionConflictError(str(relationship.id), db_version, current_version)

        update_query = text("""
            UPDATE do_relationships
            SET version = :new_version,
                properties = :properties,
                updated_at = :updated_at,
                changed_by = :changed_by
            WHERE id = :id AND namespace_id = :namespace_id AND version = :current_version
            RETURNING id, type_id, from_entity_id, to_entity_id, version, properties, created_at, updated_at, changed_by
        """)

        result = await self._session.execute(
            update_query,
            {
                "id": str(relationship.id),
                "namespace_id": namespace_id,
                "new_version": new_version,
                "properties": json.dumps(relationship.properties),
                "updated_at": now,
                "changed_by": relationship.changed_by,
                "current_version": current_version,
            },
        )

        row = result.fetchone()
        if row is None:
            raise VersionConflictError(str(relationship.id), current_version, current_version)

        updated_relationship = self._row_to_relationship(row)

        await self._close_history_record(str(relationship.id), now)

        await self._record_history(
            relationship_id=str(updated_relationship.id),
            type_id=str(updated_relationship.type_id),
            from_entity_id=str(updated_relationship.from_entity_id),
            to_entity_id=str(updated_relationship.to_entity_id),
            version=updated_relationship.version,
            properties=updated_relationship.properties,
            operation="UPDATE",
            valid_from=now,
            changed_by=relationship.changed_by,
        )

        return updated_relationship

    async def delete(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        namespace_id = self._namespace_id
        delete_history_query = text(
            "DELETE FROM do_relationship_history WHERE relationship_id = :id AND namespace_id = :namespace_id"
        )
        await self._session.execute(delete_history_query, {"id": relationship_id, "namespace_id": namespace_id})

        query = text("DELETE FROM do_relationships WHERE id = :id AND namespace_id = :namespace_id RETURNING id")
        result = await self._session.execute(query, {"id": relationship_id, "namespace_id": namespace_id})
        row = result.fetchone()

        return row is not None

    async def get_history(self, relationship_id: str) -> list[dict[str, Any]]:
        """Get version history for a relationship."""
        query = text(f"""
            SELECT id, relationship_id, type_id, from_entity_id, to_entity_id, version, properties,
                   valid_from, valid_to, operation, changed_by, created_at
            FROM do_relationship_history
            WHERE relationship_id = :relationship_id {self._namespace_and}
            ORDER BY version ASC
        """)

        result = await self._session.execute(query, self._with_namespace({"relationship_id": relationship_id}))
        rows = result.fetchall()

        history: list[dict[str, Any]] = []
        for row in rows:
            if hasattr(row, "_mapping"):
                row_dict = dict(row._mapping)
            else:
                row_dict = {
                    "id": row[0],
                    "relationship_id": row[1],
                    "type_id": row[2],
                    "from_entity_id": row[3],
                    "to_entity_id": row[4],
                    "version": row[5],
                    "properties": row[6],
                    "valid_from": row[7],
                    "valid_to": row[8],
                    "operation": row[9],
                    "changed_by": row[10],
                    "created_at": row[11],
                }

            properties = row_dict["properties"]
            if isinstance(properties, str):
                properties = json.loads(properties)

            history.append(
                {
                    "id": str(row_dict["id"]),
                    "relationship_id": str(row_dict["relationship_id"]),
                    "type_id": str(row_dict["type_id"]),
                    "from_entity_id": str(row_dict["from_entity_id"]),
                    "to_entity_id": str(row_dict["to_entity_id"]),
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
        relationship_id: str,
        type_id: str,
        from_entity_id: str,
        to_entity_id: str,
        version: int,
        properties: dict[str, Any],
        operation: str,
        valid_from: datetime,
        changed_by: str | None = None,
    ) -> None:
        """Record a history entry for a relationship."""
        query = text("""
            INSERT INTO do_relationship_history
                (relationship_id, namespace_id, type_id, from_entity_id, to_entity_id,
                 version, properties, valid_from, valid_to, operation, changed_by)
            VALUES
                (:relationship_id, :namespace_id, :type_id, :from_entity_id, :to_entity_id,
                 :version, :properties, :valid_from, NULL, :operation, :changed_by)
        """)

        await self._session.execute(
            query,
            {
                "relationship_id": relationship_id,
                "namespace_id": self._namespace_id,
                "type_id": type_id,
                "from_entity_id": from_entity_id,
                "to_entity_id": to_entity_id,
                "version": version,
                "properties": json.dumps(properties),
                "valid_from": valid_from,
                "operation": operation,
                "changed_by": changed_by,
            },
        )

    async def _close_history_record(self, relationship_id: str, valid_to: datetime) -> None:
        """Close the current history record by setting valid_to."""
        query = text("""
            UPDATE do_relationship_history
            SET valid_to = :valid_to
            WHERE relationship_id = :relationship_id
              AND namespace_id = :namespace_id
              AND valid_to IS NULL
        """)

        await self._session.execute(
            query,
            {
                "relationship_id": relationship_id,
                "namespace_id": self._namespace_id,
                "valid_to": valid_to,
            },
        )

    def _row_to_relationship(self, row: Any) -> Relationship:
        """Convert database row to Relationship domain model."""
        if hasattr(row, "_mapping"):
            row_dict = dict(row._mapping)
        else:
            row_dict = {
                "id": row[0],
                "type_id": row[1],
                "from_entity_id": row[2],
                "to_entity_id": row[3],
                "version": row[4],
                "properties": row[5],
                "created_at": row[6],
                "updated_at": row[7],
                "changed_by": row[8] if len(row) > 8 else None,
            }

        properties = row_dict["properties"]
        if isinstance(properties, str):
            properties = json.loads(properties)

        relationship_id = row_dict["id"]
        if isinstance(relationship_id, str):
            relationship_id = UUID(relationship_id)

        type_id = row_dict["type_id"]
        if isinstance(type_id, str):
            type_id = UUID(type_id)

        from_entity_id = row_dict["from_entity_id"]
        if isinstance(from_entity_id, str):
            from_entity_id = UUID(from_entity_id)

        to_entity_id = row_dict["to_entity_id"]
        if isinstance(to_entity_id, str):
            to_entity_id = UUID(to_entity_id)

        return Relationship(
            id=relationship_id,
            type_id=type_id,
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            version=row_dict["version"],
            properties=properties,
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
            changed_by=row_dict.get("changed_by"),
        )
