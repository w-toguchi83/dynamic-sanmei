"""スキーマバージョンのドメインモデル。

EntityType / RelationshipType のスキーマ変更履歴を追跡する。
各バージョンはスキーマ定義のスナップショット、前バージョンへのリンク、
互換性レベル、変更サマリーを保持する。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class CompatibilityLevel(StrEnum):
    """互換性レベル。"""

    BACKWARD = "backward"  # フィールド追加のみ（既存データは壊れない）
    FORWARD = "forward"  # フィールド削除のみ（新しいデータは古いスキーマでも読める）
    FULL = "full"  # 変更なし or 両方互換
    NONE = "none"  # 破壊的変更


class TypeKind(StrEnum):
    """スキーマタイプの種類。"""

    ENTITY_TYPE = "entity_type"
    RELATIONSHIP_TYPE = "relationship_type"


@dataclass(frozen=True)
class SchemaDiff:
    """2つのスキーマ定義間の差分。

    Attributes:
        added_fields: 追加されたフィールド名のリスト。
        removed_fields: 削除されたフィールド名のリスト。
        modified_fields: 変更されたフィールドの詳細（フィールド名 → 変更内容）。
        compatibility: 差分から判定された互換性レベル。
    """

    added_fields: list[str] = field(default_factory=list)
    removed_fields: list[str] = field(default_factory=list)
    modified_fields: dict[str, dict[str, object]] = field(default_factory=dict)
    compatibility: CompatibilityLevel = CompatibilityLevel.FULL


@dataclass(frozen=True)
class SchemaVersion:
    """スキーマバージョン（EntityType/RelationshipType の変更履歴）。

    Attributes:
        id: ユニークなバージョン識別子。
        type_kind: スキーマタイプの種類（entity_type / relationship_type）。
        type_id: 対象タイプの ID。
        version: バージョン番号（1始まり、昇順）。
        schema_definition: バージョン時点のスキーマ定義スナップショット。
        created_at: バージョン作成時刻。
        namespace_id: ネームスペース ID。
        previous_version_id: 前バージョンの ID（初回は None）。
        compatibility: 前バージョンとの互換性レベル。
        change_summary: 変更サマリー（差分情報）。
        created_by: 作成者の識別子。
    """

    id: UUID
    type_kind: TypeKind
    type_id: UUID
    version: int
    schema_definition: dict[str, object]
    created_at: datetime
    namespace_id: UUID
    previous_version_id: UUID | None = None
    compatibility: CompatibilityLevel | None = None
    change_summary: dict[str, object] | None = None
    created_by: str | None = None
