"""Test Relationship domain models."""

from datetime import UTC, datetime
from uuid import uuid4

from dynamic_ontology.domain.models.entity_type import PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.relationship import Relationship, RelationshipType


def test_relationship_type_creation() -> None:
    """Test RelationshipType creation."""
    rel_type_id = uuid4()
    now = datetime.now(UTC)

    rel_type = RelationshipType(
        id=rel_type_id,
        name="assigned_to",
        description="Task assigned to User",
        directional=True,
        properties={
            "assigned_at": PropertyDefinition(
                type=PropertyType.DATE,
                required=True,
            ),
        },
        custom_validators=[],
        created_at=now,
        updated_at=now,
    )

    assert rel_type.id == rel_type_id
    assert rel_type.name == "assigned_to"
    assert rel_type.directional is True
    assert "assigned_at" in rel_type.properties


def test_relationship_type_bidirectional() -> None:
    """Test bidirectional RelationshipType."""
    rel_type = RelationshipType(
        id=uuid4(),
        name="related_to",
        description="Generic relation",
        directional=False,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert rel_type.directional is False


def test_relationship_creation() -> None:
    """Test Relationship creation."""
    relationship_id = uuid4()
    type_id = uuid4()
    from_entity_id = uuid4()
    to_entity_id = uuid4()
    now = datetime.now(UTC)

    relationship = Relationship(
        id=relationship_id,
        type_id=type_id,
        from_entity_id=from_entity_id,
        to_entity_id=to_entity_id,
        version=1,
        properties={"assigned_at": "2024-01-01T10:00:00Z"},
        created_at=now,
        updated_at=now,
    )

    assert relationship.id == relationship_id
    assert relationship.type_id == type_id
    assert relationship.from_entity_id == from_entity_id
    assert relationship.to_entity_id == to_entity_id
    assert relationship.version == 1


def test_relationship_empty_properties() -> None:
    """Test Relationship with empty properties."""
    relationship = Relationship(
        id=uuid4(),
        type_id=uuid4(),
        from_entity_id=uuid4(),
        to_entity_id=uuid4(),
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert relationship.properties == {}


def test_relationship_version_tracking() -> None:
    """Test Relationship version tracking."""
    relationship = Relationship(
        id=uuid4(),
        type_id=uuid4(),
        from_entity_id=uuid4(),
        to_entity_id=uuid4(),
        version=1,
        properties={"weight": 1.0},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # Simulate update
    relationship.version = 2
    relationship.properties["weight"] = 2.0

    assert relationship.version == 2
    assert relationship.properties["weight"] == 2.0


def test_relationship_changed_by_default_none() -> None:
    """Test Relationship changed_by defaults to None when not provided."""
    relationship = Relationship(
        id=uuid4(),
        type_id=uuid4(),
        from_entity_id=uuid4(),
        to_entity_id=uuid4(),
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert relationship.changed_by is None


def test_relationship_changed_by_set() -> None:
    """Test Relationship changed_by can be set to a specific user identifier."""
    relationship = Relationship(
        id=uuid4(),
        type_id=uuid4(),
        from_entity_id=uuid4(),
        to_entity_id=uuid4(),
        version=1,
        properties={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        changed_by="user-123",
    )

    assert relationship.changed_by == "user-123"


def test_relationship_type_allow_duplicates_default_true() -> None:
    """allow_duplicates はデフォルトで True（後方互換）。"""
    rt = RelationshipType(
        id=uuid4(),
        name="test_type",
        description="",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert rt.allow_duplicates is True


def test_relationship_type_allow_duplicates_false() -> None:
    """allow_duplicates=False を明示的に設定できる。"""
    rt = RelationshipType(
        id=uuid4(),
        name="test_type",
        description="",
        directional=True,
        properties={},
        custom_validators=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        allow_duplicates=False,
    )
    assert rt.allow_duplicates is False
