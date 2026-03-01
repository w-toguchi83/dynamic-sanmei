"""RelationshipType allowed_source_types / allowed_target_types フィールドのユニットテスト."""

from datetime import UTC, datetime
from uuid import uuid4

from dynamic_ontology.domain.models.entity_type import PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.relationship import RelationshipType


def _make_relationship_type(**kwargs: object) -> RelationshipType:
    """テスト用 RelationshipType を生成するヘルパー."""
    defaults: dict[str, object] = {
        "id": uuid4(),
        "name": "TestRelType",
        "description": "A test relationship type",
        "directional": True,
        "properties": {
            "weight": PropertyDefinition(type=PropertyType.FLOAT, required=False),
        },
        "custom_validators": [],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return RelationshipType(**defaults)  # type: ignore[arg-type]


class TestRelationshipTypeAllowedTypes:
    """RelationshipType.allowed_source_types / allowed_target_types のテスト."""

    def test_allowed_source_types_defaults_to_empty_list(self) -> None:
        """allowed_source_types を指定しない場合は空リストになる."""
        rt = _make_relationship_type()
        assert rt.allowed_source_types == []

    def test_allowed_target_types_defaults_to_empty_list(self) -> None:
        """allowed_target_types を指定しない場合は空リストになる."""
        rt = _make_relationship_type()
        assert rt.allowed_target_types == []

    def test_allowed_source_types_with_single_uuid(self) -> None:
        """allowed_source_types に UUID を 1 つ指定できる."""
        type_id = uuid4()
        rt = _make_relationship_type(allowed_source_types=[type_id])
        assert rt.allowed_source_types == [type_id]

    def test_allowed_target_types_with_single_uuid(self) -> None:
        """allowed_target_types に UUID を 1 つ指定できる."""
        type_id = uuid4()
        rt = _make_relationship_type(allowed_target_types=[type_id])
        assert rt.allowed_target_types == [type_id]

    def test_allowed_source_types_with_multiple_uuids(self) -> None:
        """allowed_source_types に複数の UUID を指定できる."""
        ids = [uuid4(), uuid4(), uuid4()]
        rt = _make_relationship_type(allowed_source_types=ids)
        assert rt.allowed_source_types == ids
        assert len(rt.allowed_source_types) == 3

    def test_allowed_target_types_with_multiple_uuids(self) -> None:
        """allowed_target_types に複数の UUID を指定できる."""
        ids = [uuid4(), uuid4()]
        rt = _make_relationship_type(allowed_target_types=ids)
        assert rt.allowed_target_types == ids
        assert len(rt.allowed_target_types) == 2

    def test_both_allowed_types_set(self) -> None:
        """allowed_source_types と allowed_target_types を両方指定できる."""
        source_ids = [uuid4()]
        target_ids = [uuid4(), uuid4()]
        rt = _make_relationship_type(
            allowed_source_types=source_ids,
            allowed_target_types=target_ids,
        )
        assert rt.allowed_source_types == source_ids
        assert rt.allowed_target_types == target_ids

    def test_default_factory_creates_independent_lists(self) -> None:
        """デフォルトの空リストが各インスタンスで独立している."""
        rt1 = _make_relationship_type()
        rt2 = _make_relationship_type()
        rt1.allowed_source_types.append(uuid4())
        assert rt2.allowed_source_types == []

    def test_existing_fields_unaffected(self) -> None:
        """allowed types 追加で既存フィールドに影響がない."""
        rt = _make_relationship_type(
            name="belongs_to",
            directional=True,
        )
        assert rt.name == "belongs_to"
        assert rt.directional is True
        assert isinstance(rt.properties, dict)
        assert rt.custom_validators == []
        assert rt.allowed_source_types == []
        assert rt.allowed_target_types == []
