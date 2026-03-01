"""SchemaVersionRepository ポートの定義（スキーマバージョン管理の抽象インターフェース）。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from dynamic_ontology.domain.models.schema_version import SchemaVersion, TypeKind


@runtime_checkable
class SchemaVersionRepository(Protocol):
    """スキーマバージョンリポジトリの共通インターフェース。

    EntityType / RelationshipType のスキーマ変更履歴を永続化・取得する。
    """

    async def create(self, schema_version: SchemaVersion) -> SchemaVersion:
        """スキーマバージョンを作成する。

        Args:
            schema_version: 作成するスキーマバージョン。

        Returns:
            永続化された SchemaVersion。
        """
        ...

    async def list_by_type_id(self, type_id: str, type_kind: TypeKind) -> list[SchemaVersion]:
        """指定タイプの全バージョンをバージョン昇順で取得する。

        Args:
            type_id: 対象タイプの UUID 文字列。
            type_kind: スキーマタイプの種類。

        Returns:
            バージョン昇順でソートされた SchemaVersion のリスト。
        """
        ...

    async def get_by_version(self, type_id: str, version: int) -> SchemaVersion | None:
        """指定タイプの特定バージョンを取得する。

        Args:
            type_id: 対象タイプの UUID 文字列。
            version: 取得するバージョン番号。

        Returns:
            該当する SchemaVersion、見つからなければ None。
        """
        ...

    async def get_latest_version(self, type_id: str) -> SchemaVersion | None:
        """指定タイプの最新バージョンを取得する。

        Args:
            type_id: 対象タイプの UUID 文字列。

        Returns:
            最新の SchemaVersion、見つからなければ None。
        """
        ...
