"""EntityType display_property フィールドのユニットテスト."""

from datetime import UTC, datetime
from uuid import uuid4

from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType


def _make_entity_type(**kwargs: object) -> EntityType:
    """テスト用 EntityType を生成するヘルパー."""
    defaults: dict[str, object] = {
        "id": uuid4(),
        "name": "TestType",
        "description": "A test entity type",
        "properties": {
            "title": PropertyDefinition(type=PropertyType.STRING, required=True),
        },
        "custom_validators": [],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return EntityType(**defaults)  # type: ignore[arg-type]


class TestEntityTypeDisplayProperty:
    """EntityType.display_property のテスト."""

    def test_display_property_defaults_to_none(self) -> None:
        """display_property を指定しない場合は None になる."""
        et = _make_entity_type()
        assert et.display_property is None

    def test_display_property_set_to_existing_property(self) -> None:
        """display_property に既存プロパティ名を指定できる."""
        et = _make_entity_type(display_property="title")
        assert et.display_property == "title"

    def test_display_property_set_to_arbitrary_string(self) -> None:
        """display_property に任意の文字列を設定できる（ドメインモデルレベルではバリデーションなし）."""
        et = _make_entity_type(display_property="non_existent_prop")
        assert et.display_property == "non_existent_prop"

    def test_display_property_explicitly_none(self) -> None:
        """display_property に明示的に None を指定できる."""
        et = _make_entity_type(display_property=None)
        assert et.display_property is None

    def test_existing_fields_unaffected(self) -> None:
        """display_property 追加で既存フィールドに影響がない."""
        et = _make_entity_type(name="Product", description="A product type")
        assert et.name == "Product"
        assert et.description == "A product type"
        assert isinstance(et.properties, dict)
        assert et.custom_validators == []
        assert et.display_property is None
