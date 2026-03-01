"""SchemaVersioningService のユニットテスト。

スキーマ定義間の差分計算、互換性レベル判定、
変更要約生成をカバーする。
"""

from dynamic_ontology.domain.models.schema_version import CompatibilityLevel, SchemaDiff
from dynamic_ontology.domain.services.schema_versioning import (
    compute_diff,
    determine_compatibility,
    generate_change_summary,
)

# ---------------------------------------------------------------------------
# compute_diff テスト
# ---------------------------------------------------------------------------


class TestComputeDiffNoChanges:
    """変更なしのケース。"""

    def test_empty_to_empty(self) -> None:
        """空スキーマ同士の比較は FULL で差分なし。"""
        diff = compute_diff({}, {})

        assert diff.added_fields == []
        assert diff.removed_fields == []
        assert diff.modified_fields == {}
        assert diff.compatibility == CompatibilityLevel.FULL

    def test_same_properties(self) -> None:
        """同一プロパティ同士の比較は FULL。"""
        schema: dict[str, object] = {
            "properties": {
                "title": {"type": "string", "required": True},
                "price": {"type": "float", "required": False},
            }
        }
        diff = compute_diff(schema, schema)

        assert diff.added_fields == []
        assert diff.removed_fields == []
        assert diff.modified_fields == {}
        assert diff.compatibility == CompatibilityLevel.FULL

    def test_no_properties_key(self) -> None:
        """properties キーが無い場合は空として扱い FULL。"""
        diff = compute_diff({"other": "value"}, {"other": "value"})

        assert diff.added_fields == []
        assert diff.removed_fields == []
        assert diff.modified_fields == {}
        assert diff.compatibility == CompatibilityLevel.FULL


class TestComputeDiffAddOnly:
    """フィールド追加のみのケース。"""

    def test_add_single_field(self) -> None:
        """1フィールド追加は BACKWARD。"""
        old: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.added_fields == ["description"]
        assert diff.removed_fields == []
        assert diff.modified_fields == {}
        assert diff.compatibility == CompatibilityLevel.BACKWARD

    def test_add_multiple_fields(self) -> None:
        """複数フィールド追加は BACKWARD（ソート順で返却）。"""
        old: dict[str, object] = {"properties": {}}
        new: dict[str, object] = {
            "properties": {
                "zebra": {"type": "string"},
                "alpha": {"type": "integer"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.added_fields == ["alpha", "zebra"]
        assert diff.removed_fields == []
        assert diff.compatibility == CompatibilityLevel.BACKWARD

    def test_add_field_from_empty_schema(self) -> None:
        """空スキーマからフィールド追加は BACKWARD。"""
        old: dict[str, object] = {}
        new: dict[str, object] = {
            "properties": {
                "name": {"type": "string"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.added_fields == ["name"]
        assert diff.compatibility == CompatibilityLevel.BACKWARD


class TestComputeDiffRemoveOnly:
    """フィールド削除のみのケース。"""

    def test_remove_single_field(self) -> None:
        """1フィールド削除は FORWARD。"""
        old: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
                "obsolete": {"type": "string"},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.added_fields == []
        assert diff.removed_fields == ["obsolete"]
        assert diff.modified_fields == {}
        assert diff.compatibility == CompatibilityLevel.FORWARD

    def test_remove_multiple_fields(self) -> None:
        """複数フィールド削除は FORWARD（ソート順で返却）。"""
        old: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
                "zebra": {"type": "string"},
                "alpha": {"type": "string"},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.removed_fields == ["alpha", "zebra"]
        assert diff.compatibility == CompatibilityLevel.FORWARD


class TestComputeDiffMixed:
    """追加と削除の混合ケース。"""

    def test_add_and_remove(self) -> None:
        """追加+削除の混合は NONE。"""
        old: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
                "old_field": {"type": "string"},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
                "new_field": {"type": "string"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.added_fields == ["new_field"]
        assert diff.removed_fields == ["old_field"]
        assert diff.modified_fields == {}
        assert diff.compatibility == CompatibilityLevel.NONE


class TestComputeDiffModified:
    """フィールド定義変更のケース。"""

    def test_modify_field_type(self) -> None:
        """型変更（string → integer）は NONE。"""
        old: dict[str, object] = {
            "properties": {
                "price": {"type": "string"},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "price": {"type": "integer"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.added_fields == []
        assert diff.removed_fields == []
        assert "price" in diff.modified_fields
        assert diff.modified_fields["price"]["old"] == {"type": "string"}
        assert diff.modified_fields["price"]["new"] == {"type": "integer"}
        assert diff.compatibility == CompatibilityLevel.NONE

    def test_modify_field_constraint(self) -> None:
        """制約変更（required True → False）は NONE。"""
        old: dict[str, object] = {
            "properties": {
                "email": {"type": "string", "required": True},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "email": {"type": "string", "required": False},
            }
        }
        diff = compute_diff(old, new)

        assert "email" in diff.modified_fields
        assert diff.compatibility == CompatibilityLevel.NONE

    def test_modify_with_add(self) -> None:
        """変更+追加は NONE。"""
        old: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "title": {"type": "integer"},
                "description": {"type": "string"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.added_fields == ["description"]
        assert "title" in diff.modified_fields
        assert diff.compatibility == CompatibilityLevel.NONE

    def test_modify_with_remove(self) -> None:
        """変更+削除は NONE。"""
        old: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
                "obsolete": {"type": "string"},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "title": {"type": "integer"},
            }
        }
        diff = compute_diff(old, new)

        assert diff.removed_fields == ["obsolete"]
        assert "title" in diff.modified_fields
        assert diff.compatibility == CompatibilityLevel.NONE

    def test_multiple_modified_fields_sorted(self) -> None:
        """複数フィールドの変更検出はキー順ソート。"""
        old: dict[str, object] = {
            "properties": {
                "zebra": {"type": "string"},
                "alpha": {"type": "string"},
                "middle": {"type": "string"},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "zebra": {"type": "integer"},
                "alpha": {"type": "integer"},
                "middle": {"type": "string"},
            }
        }
        diff = compute_diff(old, new)

        modified_keys = list(diff.modified_fields.keys())
        assert modified_keys == ["alpha", "zebra"]
        assert diff.compatibility == CompatibilityLevel.NONE


class TestComputeDiffEdgeCases:
    """エッジケース。"""

    def test_properties_key_not_dict(self) -> None:
        """properties が dict でない場合は空として扱う。"""
        old: dict[str, object] = {"properties": "not_a_dict"}
        new: dict[str, object] = {"properties": {"name": {"type": "string"}}}
        diff = compute_diff(old, new)

        assert diff.added_fields == ["name"]
        assert diff.compatibility == CompatibilityLevel.BACKWARD

    def test_one_side_missing_properties(self) -> None:
        """片方のみ properties が無い場合。"""
        old: dict[str, object] = {
            "properties": {
                "title": {"type": "string"},
            }
        }
        new: dict[str, object] = {}
        diff = compute_diff(old, new)

        assert diff.removed_fields == ["title"]
        assert diff.compatibility == CompatibilityLevel.FORWARD

    def test_add_indexed_field(self) -> None:
        """indexed プロパティ追加も BACKWARD。"""
        old: dict[str, object] = {
            "properties": {
                "title": {"type": "string", "required": True},
            }
        }
        new: dict[str, object] = {
            "properties": {
                "title": {"type": "string", "required": True},
                "price": {
                    "type": "float",
                    "indexed": True,
                    "indexed_column": "float_value",
                },
            }
        }
        diff = compute_diff(old, new)

        assert diff.added_fields == ["price"]
        assert diff.compatibility == CompatibilityLevel.BACKWARD


# ---------------------------------------------------------------------------
# determine_compatibility テスト
# ---------------------------------------------------------------------------


class TestDetermineCompatibility:
    """determine_compatibility 関数のテスト。"""

    def test_no_changes(self) -> None:
        """変更なし → FULL。"""
        result = determine_compatibility([], [], {})
        assert result == CompatibilityLevel.FULL

    def test_only_additions(self) -> None:
        """追加のみ → BACKWARD。"""
        result = determine_compatibility(["new_field"], [], {})
        assert result == CompatibilityLevel.BACKWARD

    def test_only_removals(self) -> None:
        """削除のみ → FORWARD。"""
        result = determine_compatibility([], ["old_field"], {})
        assert result == CompatibilityLevel.FORWARD

    def test_additions_and_removals(self) -> None:
        """追加+削除 → NONE。"""
        result = determine_compatibility(["new"], ["old"], {})
        assert result == CompatibilityLevel.NONE

    def test_only_modifications(self) -> None:
        """変更のみ → NONE。"""
        modified: dict[str, dict[str, object]] = {
            "title": {"old": {"type": "string"}, "new": {"type": "integer"}}
        }
        result = determine_compatibility([], [], modified)
        assert result == CompatibilityLevel.NONE

    def test_modifications_with_additions(self) -> None:
        """変更+追加 → NONE。"""
        modified: dict[str, dict[str, object]] = {
            "title": {"old": {"type": "string"}, "new": {"type": "integer"}}
        }
        result = determine_compatibility(["new_field"], [], modified)
        assert result == CompatibilityLevel.NONE

    def test_modifications_with_removals(self) -> None:
        """変更+削除 → NONE。"""
        modified: dict[str, dict[str, object]] = {
            "title": {"old": {"type": "string"}, "new": {"type": "integer"}}
        }
        result = determine_compatibility([], ["old_field"], modified)
        assert result == CompatibilityLevel.NONE

    def test_all_three_changes(self) -> None:
        """追加+削除+変更 → NONE。"""
        modified: dict[str, dict[str, object]] = {
            "title": {"old": {"type": "string"}, "new": {"type": "integer"}}
        }
        result = determine_compatibility(["new"], ["old"], modified)
        assert result == CompatibilityLevel.NONE


# ---------------------------------------------------------------------------
# generate_change_summary テスト
# ---------------------------------------------------------------------------


class TestGenerateChangeSummary:
    """generate_change_summary 関数のテスト。"""

    def test_full_compatibility_no_changes(self) -> None:
        """FULL 互換（変更なし）のサマリー。"""
        diff = SchemaDiff(
            added_fields=[],
            removed_fields=[],
            modified_fields={},
            compatibility=CompatibilityLevel.FULL,
        )
        summary = generate_change_summary(diff)

        assert summary == {"compatibility": "full"}
        assert "added_fields" not in summary
        assert "removed_fields" not in summary
        assert "modified_fields" not in summary

    def test_backward_compatibility_with_additions(self) -> None:
        """BACKWARD 互換（フィールド追加）のサマリー。"""
        diff = SchemaDiff(
            added_fields=["description", "tags"],
            removed_fields=[],
            modified_fields={},
            compatibility=CompatibilityLevel.BACKWARD,
        )
        summary = generate_change_summary(diff)

        assert summary["compatibility"] == "backward"
        assert summary["added_fields"] == ["description", "tags"]
        assert "removed_fields" not in summary
        assert "modified_fields" not in summary

    def test_forward_compatibility_with_removals(self) -> None:
        """FORWARD 互換（フィールド削除）のサマリー。"""
        diff = SchemaDiff(
            added_fields=[],
            removed_fields=["obsolete_field"],
            modified_fields={},
            compatibility=CompatibilityLevel.FORWARD,
        )
        summary = generate_change_summary(diff)

        assert summary["compatibility"] == "forward"
        assert "added_fields" not in summary
        assert summary["removed_fields"] == ["obsolete_field"]
        assert "modified_fields" not in summary

    def test_none_compatibility_with_modifications(self) -> None:
        """NONE 互換（フィールド変更）のサマリーはフィールド名のみ。"""
        diff = SchemaDiff(
            added_fields=[],
            removed_fields=[],
            modified_fields={
                "price": {
                    "old": {"type": "string"},
                    "new": {"type": "integer"},
                }
            },
            compatibility=CompatibilityLevel.NONE,
        )
        summary = generate_change_summary(diff)

        assert summary["compatibility"] == "none"
        assert "added_fields" not in summary
        assert "removed_fields" not in summary
        # modified_fields にはフィールド名のみ（差分詳細は含まない）
        assert summary["modified_fields"] == ["price"]

    def test_none_compatibility_mixed_changes(self) -> None:
        """NONE 互換（追加+削除+変更混合）のサマリー。"""
        diff = SchemaDiff(
            added_fields=["new_field"],
            removed_fields=["old_field"],
            modified_fields={
                "title": {
                    "old": {"type": "string"},
                    "new": {"type": "integer"},
                }
            },
            compatibility=CompatibilityLevel.NONE,
        )
        summary = generate_change_summary(diff)

        assert summary["compatibility"] == "none"
        assert summary["added_fields"] == ["new_field"]
        assert summary["removed_fields"] == ["old_field"]
        assert summary["modified_fields"] == ["title"]

    def test_summary_values_are_json_serializable(self) -> None:
        """サマリーの値は JSON シリアライズ可能。"""
        import json

        diff = SchemaDiff(
            added_fields=["a", "b"],
            removed_fields=["c"],
            modified_fields={"d": {"old": {"type": "string"}, "new": {"type": "int"}}},
            compatibility=CompatibilityLevel.NONE,
        )
        summary = generate_change_summary(diff)

        # json.dumps が例外を投げないことを確認
        serialized = json.dumps(summary)
        assert isinstance(serialized, str)
