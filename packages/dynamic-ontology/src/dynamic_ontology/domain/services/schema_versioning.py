"""スキーマバージョニングサービス。

EntityType / RelationshipType のスキーマ定義間の差分計算と
互換性レベル判定を提供する。
"""

from dynamic_ontology.domain.models.schema_version import CompatibilityLevel, SchemaDiff


def compute_diff(
    old_schema: dict[str, object],
    new_schema: dict[str, object],
) -> SchemaDiff:
    """2つのスキーマ定義間の差分を計算する。

    schema_definition の "properties" キーの中身を比較する。

    Args:
        old_schema: 変更前のスキーマ定義（schema_definition JSONB の中身）
        new_schema: 変更後のスキーマ定義

    Returns:
        差分情報と互換性レベルを含む SchemaDiff
    """
    old_props_raw = old_schema.get("properties", {})
    new_props_raw = new_schema.get("properties", {})

    old_props: dict[str, object] = old_props_raw if isinstance(old_props_raw, dict) else {}
    new_props: dict[str, object] = new_props_raw if isinstance(new_props_raw, dict) else {}

    old_keys = set(old_props.keys())
    new_keys = set(new_props.keys())

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)

    # 両方に存在するフィールドの定義変更を検出
    modified: dict[str, dict[str, object]] = {}
    for key in sorted(old_keys & new_keys):
        old_val = old_props[key]
        new_val = new_props[key]
        if old_val != new_val:
            modified[key] = {"old": old_val, "new": new_val}

    compatibility = determine_compatibility(added, removed, modified)

    return SchemaDiff(
        added_fields=added,
        removed_fields=removed,
        modified_fields=modified,
        compatibility=compatibility,
    )


def determine_compatibility(
    added: list[str],
    removed: list[str],
    modified: dict[str, dict[str, object]],
) -> CompatibilityLevel:
    """差分から互換性レベルを判定する。

    - FULL: 変更なし
    - BACKWARD: フィールド追加のみ（既存データは壊れない）
    - FORWARD: フィールド削除のみ（新データは古いスキーマでも読める）
    - NONE: フィールド変更、または追加+削除の混合

    Args:
        added: 追加されたフィールド名のリスト
        removed: 削除されたフィールド名のリスト
        modified: 変更されたフィールドの詳細

    Returns:
        判定された互換性レベル
    """
    has_added = len(added) > 0
    has_removed = len(removed) > 0
    has_modified = len(modified) > 0

    if has_modified:
        return CompatibilityLevel.NONE

    if has_added and has_removed:
        return CompatibilityLevel.NONE

    if not has_added and not has_removed:
        return CompatibilityLevel.FULL

    if has_added and not has_removed:
        return CompatibilityLevel.BACKWARD

    # has_removed and not has_added
    return CompatibilityLevel.FORWARD


def generate_change_summary(diff: SchemaDiff) -> dict[str, object]:
    """SchemaDiff から JSONB 保存用の変更要約を生成する。

    Args:
        diff: スキーマ差分

    Returns:
        JSONB に保存可能な dict
    """
    summary: dict[str, object] = {
        "compatibility": diff.compatibility.value,
    }
    if diff.added_fields:
        summary["added_fields"] = diff.added_fields
    if diff.removed_fields:
        summary["removed_fields"] = diff.removed_fields
    if diff.modified_fields:
        summary["modified_fields"] = list(diff.modified_fields.keys())
    return summary
