"""Test Entity domain model."""

from datetime import UTC, datetime
from uuid import uuid4

from dynamic_ontology.domain.models.entity import Entity


def test_entity_creation() -> None:
    """Test Entity creation with valid data."""
    entity_id = uuid4()
    type_id = uuid4()
    now = datetime.now(UTC)

    entity = Entity(
        id=entity_id,
        type_id=type_id,
        version=1,
        properties={"title": "Fix bug", "priority": 5},
        created_at=now,
        updated_at=now,
    )

    assert entity.id == entity_id
    assert entity.type_id == type_id
    assert entity.version == 1
    assert entity.properties["title"] == "Fix bug"
    assert entity.properties["priority"] == 5


def test_entity_empty_properties() -> None:
    """Test Entity with empty properties."""
    entity = Entity(
        id=uuid4(),
        type_id=uuid4(),
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert entity.properties == {}
    assert len(entity.properties) == 0


def test_entity_version_increments() -> None:
    """Test Entity version tracking."""
    entity = Entity(
        id=uuid4(),
        type_id=uuid4(),
        version=1,
        properties={"title": "Original"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # Simulate update
    entity.version = 2
    entity.properties["title"] = "Updated"

    assert entity.version == 2
    assert entity.properties["title"] == "Updated"


def test_entity_complex_properties() -> None:
    """Test Entity with various property types."""
    entity = Entity(
        id=uuid4(),
        type_id=uuid4(),
        version=1,
        properties={
            "title": "Complex task",
            "priority": 3,
            "completed": False,
            "score": 85.5,
            "tags": ["important", "urgent"],
            "metadata": {"source": "api", "user_id": 123},
        },
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert entity.properties["title"] == "Complex task"
    assert entity.properties["priority"] == 3
    assert entity.properties["completed"] is False
    assert entity.properties["score"] == 85.5
    assert isinstance(entity.properties["tags"], list)
    assert isinstance(entity.properties["metadata"], dict)
