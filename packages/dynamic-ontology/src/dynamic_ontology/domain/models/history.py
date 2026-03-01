"""History domain models for time travel functionality.

エンティティの履歴管理とタイムトラベル機能のためのドメインモデル。
スナップショット、差分、プロパティ変更を表現する。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class EntitySnapshot:
    """エンティティの特定時点のスナップショット.

    タイムトラベル機能で過去の状態を表現するために使用。
    valid_from/valid_to で有効期間を管理する。

    Attributes:
        entity_id: エンティティのUUID
        type_id: エンティティタイプのUUID
        version: スナップショット時点のバージョン番号
        properties: プロパティの辞書（JSONB形式）
        valid_from: 有効期間の開始時刻
        valid_to: 有効期間の終了時刻（Noneの場合は現在有効）
        operation: 操作タイプ（CREATE, UPDATE, DELETE）
    """

    entity_id: UUID
    type_id: UUID
    version: int
    properties: dict[str, Any]
    valid_from: datetime
    valid_to: datetime | None
    operation: str

    @property
    def is_current(self) -> bool:
        """現在有効なスナップショットかどうかを判定.

        Returns:
            valid_to が None の場合 True
        """
        return self.valid_to is None


@dataclass
class PropertyChange:
    """プロパティの変更を表現.

    2つのスナップショット間での単一プロパティの変更を記録する。

    Attributes:
        field: 変更されたプロパティ名
        old_value: 変更前の値（追加の場合はNone）
        new_value: 変更後の値（削除の場合はNone）
    """

    field: str
    old_value: Any
    new_value: Any

    @property
    def change_type(self) -> str:
        """変更タイプを判定.

        Returns:
            "added": old_value が None の場合（新規追加）
            "removed": new_value が None の場合（削除）
            "modified": 両方に値がある場合（変更）
        """
        if self.old_value is None:
            return "added"
        if self.new_value is None:
            return "removed"
        return "modified"


@dataclass
class EntityDiff:
    """2つのスナップショット間の差分を表現.

    エンティティの2つのバージョン間での全ての変更をまとめて保持する。

    Attributes:
        entity_id: エンティティのUUID
        from_version: 比較元のバージョン番号
        to_version: 比較先のバージョン番号
        from_time: 比較元の時刻
        to_time: 比較先の時刻
        changes: プロパティ変更のリスト
    """

    entity_id: UUID
    from_version: int
    to_version: int
    from_time: datetime
    to_time: datetime
    changes: list[PropertyChange]

    @property
    def has_changes(self) -> bool:
        """変更があるかどうかを判定.

        Returns:
            changes リストが空でない場合 True
        """
        return len(self.changes) > 0
