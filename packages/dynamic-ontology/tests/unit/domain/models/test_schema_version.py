"""SchemaVersion ドメインモデルのユニットテスト。"""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dynamic_ontology.domain.models.schema_version import (
    CompatibilityLevel,
    SchemaDiff,
    SchemaVersion,
    TypeKind,
)


class TestCompatibilityLevel:
    """CompatibilityLevel enum のテスト。"""

    def test_all_values_exist(self) -> None:
        """全互換性レベルが正しい文字列値で定義されている。"""
        assert CompatibilityLevel.BACKWARD == "backward"
        assert CompatibilityLevel.FORWARD == "forward"
        assert CompatibilityLevel.FULL == "full"
        assert CompatibilityLevel.NONE == "none"

    def test_is_string_enum(self) -> None:
        """CompatibilityLevel の値は文字列として使用できる。"""
        level = CompatibilityLevel.BACKWARD
        assert isinstance(level, str)
        assert f"level={level}" == "level=backward"

    def test_member_count(self) -> None:
        """CompatibilityLevel は 4 つのメンバーを持つ。"""
        assert len(CompatibilityLevel) == 4


class TestTypeKind:
    """TypeKind enum のテスト。"""

    def test_all_values_exist(self) -> None:
        """全タイプ種別が正しい文字列値で定義されている。"""
        assert TypeKind.ENTITY_TYPE == "entity_type"
        assert TypeKind.RELATIONSHIP_TYPE == "relationship_type"

    def test_is_string_enum(self) -> None:
        """TypeKind の値は文字列として使用できる。"""
        kind = TypeKind.ENTITY_TYPE
        assert isinstance(kind, str)
        assert f"kind={kind}" == "kind=entity_type"

    def test_member_count(self) -> None:
        """TypeKind は 2 つのメンバーを持つ。"""
        assert len(TypeKind) == 2


class TestSchemaDiff:
    """SchemaDiff dataclass のテスト。"""

    def test_default_values(self) -> None:
        """SchemaDiff はデフォルトで空リスト・FULL 互換性を持つ。"""
        diff = SchemaDiff()

        assert diff.added_fields == []
        assert diff.removed_fields == []
        assert diff.modified_fields == {}
        assert diff.compatibility == CompatibilityLevel.FULL

    def test_with_added_fields(self) -> None:
        """フィールド追加のみの SchemaDiff を作成できる。"""
        diff = SchemaDiff(
            added_fields=["email", "phone"],
            compatibility=CompatibilityLevel.BACKWARD,
        )

        assert diff.added_fields == ["email", "phone"]
        assert diff.removed_fields == []
        assert diff.modified_fields == {}
        assert diff.compatibility == CompatibilityLevel.BACKWARD

    def test_with_removed_fields(self) -> None:
        """フィールド削除のみの SchemaDiff を作成できる。"""
        diff = SchemaDiff(
            removed_fields=["legacy_field"],
            compatibility=CompatibilityLevel.FORWARD,
        )

        assert diff.removed_fields == ["legacy_field"]
        assert diff.added_fields == []

    def test_with_modified_fields(self) -> None:
        """フィールド変更を含む SchemaDiff を作成できる。"""
        diff = SchemaDiff(
            modified_fields={
                "age": {"old_type": "string", "new_type": "integer"},
            },
            compatibility=CompatibilityLevel.NONE,
        )

        assert "age" in diff.modified_fields
        assert diff.modified_fields["age"]["old_type"] == "string"
        assert diff.modified_fields["age"]["new_type"] == "integer"
        assert diff.compatibility == CompatibilityLevel.NONE

    def test_is_frozen(self) -> None:
        """SchemaDiff は不変（frozen dataclass）である。"""
        diff = SchemaDiff()

        assert is_dataclass(diff)

        with pytest.raises(FrozenInstanceError):
            diff.compatibility = CompatibilityLevel.NONE  # type: ignore[misc]

    def test_complex_diff(self) -> None:
        """追加・削除・変更を同時に含む SchemaDiff を作成できる。"""
        diff = SchemaDiff(
            added_fields=["new_field"],
            removed_fields=["old_field"],
            modified_fields={
                "status": {"old_type": "string", "new_type": "enum"},
            },
            compatibility=CompatibilityLevel.NONE,
        )

        assert len(diff.added_fields) == 1
        assert len(diff.removed_fields) == 1
        assert len(diff.modified_fields) == 1


class TestSchemaVersion:
    """SchemaVersion dataclass のテスト。"""

    def test_create_with_all_fields(self) -> None:
        """全フィールドを指定して SchemaVersion を作成できる。"""
        version_id = uuid4()
        type_id = uuid4()
        prev_id = uuid4()
        namespace_id = uuid4()
        now = datetime.now(UTC)

        sv = SchemaVersion(
            id=version_id,
            type_kind=TypeKind.ENTITY_TYPE,
            type_id=type_id,
            version=2,
            schema_definition={
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
            },
            created_at=now,
            namespace_id=namespace_id,
            previous_version_id=prev_id,
            compatibility=CompatibilityLevel.BACKWARD,
            change_summary={
                "added_fields": ["age"],
                "removed_fields": [],
            },
            created_by="admin@example.com",
        )

        assert sv.id == version_id
        assert sv.type_kind == TypeKind.ENTITY_TYPE
        assert sv.type_id == type_id
        assert sv.version == 2
        assert sv.schema_definition["properties"]["name"]["type"] == "string"  # type: ignore[index]
        assert sv.created_at == now
        assert sv.namespace_id == namespace_id
        assert sv.previous_version_id == prev_id
        assert sv.compatibility == CompatibilityLevel.BACKWARD
        assert sv.change_summary == {"added_fields": ["age"], "removed_fields": []}
        assert sv.created_by == "admin@example.com"

    def test_create_first_version(self) -> None:
        """初回バージョン（optional フィールドが None）を作成できる。"""
        version_id = uuid4()
        type_id = uuid4()
        namespace_id = uuid4()
        now = datetime.now(UTC)

        sv = SchemaVersion(
            id=version_id,
            type_kind=TypeKind.ENTITY_TYPE,
            type_id=type_id,
            version=1,
            schema_definition={"properties": {"name": {"type": "string"}}},
            created_at=now,
            namespace_id=namespace_id,
        )

        assert sv.version == 1
        assert sv.previous_version_id is None
        assert sv.compatibility is None
        assert sv.change_summary is None
        assert sv.created_by is None

    def test_relationship_type_kind(self) -> None:
        """TypeKind.RELATIONSHIP_TYPE で SchemaVersion を作成できる。"""
        sv = SchemaVersion(
            id=uuid4(),
            type_kind=TypeKind.RELATIONSHIP_TYPE,
            type_id=uuid4(),
            version=1,
            schema_definition={"properties": {"weight": {"type": "float"}}},
            created_at=datetime.now(UTC),
            namespace_id=uuid4(),
        )

        assert sv.type_kind == TypeKind.RELATIONSHIP_TYPE

    def test_is_frozen(self) -> None:
        """SchemaVersion は不変（frozen dataclass）である。"""
        sv = SchemaVersion(
            id=uuid4(),
            type_kind=TypeKind.ENTITY_TYPE,
            type_id=uuid4(),
            version=1,
            schema_definition={"properties": {}},
            created_at=datetime.now(UTC),
            namespace_id=uuid4(),
        )

        assert is_dataclass(sv)

        with pytest.raises(FrozenInstanceError):
            sv.version = 2  # type: ignore[misc]

    def test_schema_definition_structure(self) -> None:
        """schema_definition に複雑な構造を格納できる。"""
        schema_def: dict[str, object] = {
            "properties": {
                "title": {"type": "string", "indexed": True},
                "count": {"type": "integer", "indexed": False},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title"],
        }

        sv = SchemaVersion(
            id=uuid4(),
            type_kind=TypeKind.ENTITY_TYPE,
            type_id=uuid4(),
            version=1,
            schema_definition=schema_def,
            created_at=datetime.now(UTC),
            namespace_id=uuid4(),
        )

        assert sv.schema_definition == schema_def

    def test_all_compatibility_levels(self) -> None:
        """全 CompatibilityLevel で SchemaVersion を作成できる。"""
        for level in CompatibilityLevel:
            sv = SchemaVersion(
                id=uuid4(),
                type_kind=TypeKind.ENTITY_TYPE,
                type_id=uuid4(),
                version=1,
                schema_definition={"properties": {}},
                created_at=datetime.now(UTC),
                namespace_id=uuid4(),
                compatibility=level,
            )
            assert sv.compatibility == level

    def test_all_type_kinds(self) -> None:
        """全 TypeKind で SchemaVersion を作成できる。"""
        for kind in TypeKind:
            sv = SchemaVersion(
                id=uuid4(),
                type_kind=kind,
                type_id=uuid4(),
                version=1,
                schema_definition={"properties": {}},
                created_at=datetime.now(UTC),
                namespace_id=uuid4(),
            )
            assert sv.type_kind == kind
