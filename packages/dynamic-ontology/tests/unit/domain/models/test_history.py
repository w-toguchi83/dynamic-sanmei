"""Test history domain models for time travel functionality."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from dynamic_ontology.domain.models.history import EntityDiff, EntitySnapshot, PropertyChange


class TestEntitySnapshot:
    """EntitySnapshotドメインモデルのテスト."""

    def test_create_entity_snapshot(self) -> None:
        """Test EntitySnapshot creation with all fields."""
        entity_id = uuid4()
        type_id = uuid4()
        valid_from = datetime.now(UTC)

        snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=1,
            properties={"title": "Test Task", "priority": 5},
            valid_from=valid_from,
            valid_to=None,
            operation="CREATE",
        )

        assert snapshot.entity_id == entity_id
        assert snapshot.type_id == type_id
        assert snapshot.version == 1
        assert snapshot.properties["title"] == "Test Task"
        assert snapshot.properties["priority"] == 5
        assert snapshot.valid_from == valid_from
        assert snapshot.valid_to is None
        assert snapshot.operation == "CREATE"

    def test_entity_snapshot_is_current(self) -> None:
        """Test is_current returns True when valid_to is None."""
        snapshot = EntitySnapshot(
            entity_id=uuid4(),
            type_id=uuid4(),
            version=1,
            properties={},
            valid_from=datetime.now(UTC),
            valid_to=None,
            operation="CREATE",
        )

        assert snapshot.is_current is True

    def test_entity_snapshot_is_not_current(self) -> None:
        """Test is_current returns False when valid_to is set."""
        now = datetime.now(UTC)
        snapshot = EntitySnapshot(
            entity_id=uuid4(),
            type_id=uuid4(),
            version=1,
            properties={},
            valid_from=now,
            valid_to=now + timedelta(hours=1),
            operation="UPDATE",
        )

        assert snapshot.is_current is False


class TestPropertyChange:
    """PropertyChangeドメインモデルのテスト."""

    def test_property_change_added(self) -> None:
        """Test change_type returns 'added' when old_value is None."""
        change = PropertyChange(
            field="title",
            old_value=None,
            new_value="New Title",
        )

        assert change.change_type == "added"
        assert change.field == "title"
        assert change.old_value is None
        assert change.new_value == "New Title"

    def test_property_change_removed(self) -> None:
        """Test change_type returns 'removed' when new_value is None."""
        change = PropertyChange(
            field="description",
            old_value="Old Description",
            new_value=None,
        )

        assert change.change_type == "removed"
        assert change.field == "description"
        assert change.old_value == "Old Description"
        assert change.new_value is None

    def test_property_change_modified(self) -> None:
        """Test change_type returns 'modified' when both values are present."""
        change = PropertyChange(
            field="priority",
            old_value=1,
            new_value=5,
        )

        assert change.change_type == "modified"
        assert change.field == "priority"
        assert change.old_value == 1
        assert change.new_value == 5


class TestEntityDiff:
    """EntityDiffドメインモデルのテスト."""

    def test_create_entity_diff(self) -> None:
        """Test EntityDiff creation and has_changes property."""
        entity_id = uuid4()
        from_time = datetime.now(UTC)
        to_time = from_time + timedelta(hours=1)

        changes = [
            PropertyChange(field="title", old_value="Old", new_value="New"),
            PropertyChange(field="status", old_value=None, new_value="active"),
        ]

        diff = EntityDiff(
            entity_id=entity_id,
            from_version=1,
            to_version=2,
            from_time=from_time,
            to_time=to_time,
            changes=changes,
        )

        assert diff.entity_id == entity_id
        assert diff.from_version == 1
        assert diff.to_version == 2
        assert diff.from_time == from_time
        assert diff.to_time == to_time
        assert len(diff.changes) == 2
        assert diff.has_changes is True

    def test_entity_diff_no_changes(self) -> None:
        """Test has_changes returns False when changes list is empty."""
        diff = EntityDiff(
            entity_id=uuid4(),
            from_version=1,
            to_version=1,
            from_time=datetime.now(UTC),
            to_time=datetime.now(UTC),
            changes=[],
        )

        assert diff.has_changes is False
