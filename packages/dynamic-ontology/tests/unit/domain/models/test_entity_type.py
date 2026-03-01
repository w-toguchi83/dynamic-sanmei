"""Test EntityType domain model."""

from datetime import UTC, datetime
from uuid import uuid4

from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType


def test_property_type_enum() -> None:
    """Test PropertyType enum values."""
    assert PropertyType.STRING == "string"
    assert PropertyType.INTEGER == "integer"
    assert PropertyType.FLOAT == "float"
    assert PropertyType.BOOLEAN == "boolean"
    assert PropertyType.DATE == "date"


def test_property_definition_minimal() -> None:
    """Test PropertyDefinition with minimal required fields."""
    prop_def = PropertyDefinition(
        type=PropertyType.STRING,
        required=False,
    )
    assert prop_def.type == PropertyType.STRING
    assert prop_def.required is False
    assert prop_def.indexed is False
    assert prop_def.default is None


def test_property_definition_with_constraints() -> None:
    """Test PropertyDefinition with validation constraints."""
    prop_def = PropertyDefinition(
        type=PropertyType.STRING,
        required=True,
        indexed=True,
        min_length=1,
        max_length=200,
    )
    assert prop_def.min_length == 1
    assert prop_def.max_length == 200
    assert prop_def.indexed is True


def test_property_definition_with_enum() -> None:
    """Test PropertyDefinition with enum constraint."""
    prop_def = PropertyDefinition(
        type=PropertyType.STRING,
        required=True,
        enum=["open", "in_progress", "completed"],
    )
    assert prop_def.enum == ["open", "in_progress", "completed"]


def test_entity_type_creation() -> None:
    """Test EntityType creation with valid data."""
    entity_id = uuid4()
    now = datetime.now(UTC)

    entity_type = EntityType(
        id=entity_id,
        name="Task",
        description="A task entity",
        properties={
            "title": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                indexed=True,
                min_length=1,
                max_length=200,
            ),
            "priority": PropertyDefinition(
                type=PropertyType.INTEGER,
                required=True,
                min_value=1,
                max_value=5,
                default=3,
            ),
        },
        custom_validators=[],
        created_at=now,
        updated_at=now,
    )

    assert entity_type.id == entity_id
    assert entity_type.name == "Task"
    assert entity_type.description == "A task entity"
    assert len(entity_type.properties) == 2
    assert "title" in entity_type.properties
    assert "priority" in entity_type.properties


def test_entity_type_property_access() -> None:
    """Test accessing properties from EntityType."""
    entity_type = EntityType(
        id=uuid4(),
        name="Task",
        description="A task entity",
        properties={
            "title": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
            ),
        },
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    title_prop = entity_type.properties["title"]
    assert title_prop.type == PropertyType.STRING
    assert title_prop.required is True


def test_entity_type_with_custom_validators() -> None:
    """Test EntityType with custom validator names."""
    entity_type = EntityType(
        id=uuid4(),
        name="Task",
        description="A task entity",
        properties={},
        custom_validators=["validate_due_date_after_start"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert len(entity_type.custom_validators) == 1
    assert entity_type.custom_validators[0] == "validate_due_date_after_start"
