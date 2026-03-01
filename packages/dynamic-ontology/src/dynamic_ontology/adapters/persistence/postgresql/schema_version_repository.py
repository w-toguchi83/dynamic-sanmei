"""スキーマバージョンの PostgreSQL リポジトリ実装."""

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.domain.models.schema_version import (
    CompatibilityLevel,
    SchemaVersion,
    TypeKind,
)


class PostgresSchemaVersionRepository:
    """PostgreSQL を使ったスキーマバージョンリポジトリ."""

    def __init__(self, session: AsyncSession, namespace_id: str) -> None:
        """Initialize with database session and namespace ID.

        Args:
            session: SQLAlchemy async session for database operations.
            namespace_id: ネームスペース識別子.
        """
        self._session = session
        self._namespace_id = namespace_id

    _COLUMNS = """
        id, type_kind, type_id, version, schema_definition,
        previous_version_id, compatibility, change_summary,
        created_at, created_by, namespace_id
    """

    async def create(self, schema_version: SchemaVersion) -> SchemaVersion:
        """新しいスキーマバージョンを作成する。

        Args:
            schema_version: 作成するスキーマバージョン。

        Returns:
            永続化された SchemaVersion。
        """
        query = text(f"""
            INSERT INTO do_schema_versions (
                id, type_kind, type_id, version, schema_definition,
                previous_version_id, compatibility, change_summary,
                created_at, created_by, namespace_id
            ) VALUES (
                :id, :type_kind, :type_id, :version, :schema_definition,
                :previous_version_id, :compatibility, :change_summary,
                :created_at, :created_by, :namespace_id
            )
            RETURNING {self._COLUMNS}
        """)

        params: dict[str, object] = {
            "id": str(schema_version.id),
            "type_kind": schema_version.type_kind.value,
            "type_id": str(schema_version.type_id),
            "version": schema_version.version,
            "schema_definition": json.dumps(schema_version.schema_definition),
            "previous_version_id": str(schema_version.previous_version_id)
            if schema_version.previous_version_id
            else None,
            "compatibility": schema_version.compatibility.value
            if schema_version.compatibility
            else None,
            "change_summary": json.dumps(schema_version.change_summary)
            if schema_version.change_summary
            else None,
            "created_at": schema_version.created_at,
            "created_by": schema_version.created_by,
            "namespace_id": self._namespace_id,
        }

        result = await self._session.execute(query, params)
        row = result.mappings().one()
        return self._row_to_schema_version(row)

    async def list_by_type_id(self, type_id: str, type_kind: TypeKind) -> list[SchemaVersion]:
        """指定タイプの全バージョンをバージョン番号昇順で取得する。

        Args:
            type_id: 対象タイプの UUID 文字列。
            type_kind: スキーマタイプの種類。

        Returns:
            バージョン昇順でソートされた SchemaVersion のリスト。
        """
        query = text(f"""
            SELECT {self._COLUMNS}
            FROM do_schema_versions
            WHERE type_id = :type_id
              AND type_kind = :type_kind
              AND namespace_id = :namespace_id
            ORDER BY version ASC
        """)

        result = await self._session.execute(
            query,
            {
                "type_id": type_id,
                "type_kind": type_kind.value,
                "namespace_id": self._namespace_id,
            },
        )

        return [self._row_to_schema_version(row) for row in result.mappings().all()]

    async def get_by_version(self, type_id: str, version: int) -> SchemaVersion | None:
        """指定タイプの特定バージョンを取得する。

        Args:
            type_id: 対象タイプの UUID 文字列。
            version: 取得するバージョン番号。

        Returns:
            該当する SchemaVersion、見つからなければ None。
        """
        query = text(f"""
            SELECT {self._COLUMNS}
            FROM do_schema_versions
            WHERE type_id = :type_id
              AND version = :version
              AND namespace_id = :namespace_id
        """)

        result = await self._session.execute(
            query,
            {
                "type_id": type_id,
                "version": version,
                "namespace_id": self._namespace_id,
            },
        )

        row = result.mappings().first()
        if row is None:
            return None
        return self._row_to_schema_version(row)

    async def get_latest_version(self, type_id: str) -> SchemaVersion | None:
        """指定タイプの最新バージョンを取得する。

        Args:
            type_id: 対象タイプの UUID 文字列。

        Returns:
            最新の SchemaVersion、見つからなければ None。
        """
        query = text(f"""
            SELECT {self._COLUMNS}
            FROM do_schema_versions
            WHERE type_id = :type_id
              AND namespace_id = :namespace_id
            ORDER BY version DESC
            LIMIT 1
        """)

        result = await self._session.execute(
            query,
            {
                "type_id": type_id,
                "namespace_id": self._namespace_id,
            },
        )

        row = result.mappings().first()
        if row is None:
            return None
        return self._row_to_schema_version(row)

    @staticmethod
    def _row_to_schema_version(row: RowMapping) -> SchemaVersion:
        """DB の行を SchemaVersion ドメインモデルに変換する。

        Args:
            row: SQLAlchemy の RowMapping オブジェクト。

        Returns:
            SchemaVersion ドメインモデル。
        """
        schema_def = row["schema_definition"]
        if isinstance(schema_def, str):
            schema_def = json.loads(schema_def)

        change_summary = row["change_summary"]
        if isinstance(change_summary, str):
            change_summary = json.loads(change_summary)

        created_at_value: datetime = row["created_at"]

        return SchemaVersion(
            id=UUID(str(row["id"])),
            type_kind=TypeKind(str(row["type_kind"])),
            type_id=UUID(str(row["type_id"])),
            version=int(row["version"]),
            schema_definition=dict(schema_def) if schema_def else {},
            previous_version_id=UUID(str(row["previous_version_id"]))
            if row["previous_version_id"]
            else None,
            compatibility=CompatibilityLevel(str(row["compatibility"]))
            if row["compatibility"]
            else None,
            change_summary=dict(change_summary) if change_summary else None,
            created_at=created_at_value,
            created_by=str(row["created_by"]) if row["created_by"] else None,
            namespace_id=UUID(str(row["namespace_id"])),
        )
