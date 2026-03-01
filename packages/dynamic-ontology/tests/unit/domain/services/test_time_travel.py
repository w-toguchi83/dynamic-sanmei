"""TimeTravelService のユニットテスト.

タイムトラベル操作のためのドメインサービスをテストする。
スナップショット間の差分計算と時刻指定でのスナップショット検索をカバー。
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from dynamic_ontology.domain.models.history import EntityDiff, EntitySnapshot
from dynamic_ontology.domain.services.time_travel import TimeTravelService


class TestComputeDiff:
    """compute_diff メソッドのテスト."""

    def test_compute_diff_with_changes(self) -> None:
        """プロパティ変更がある差分計算."""
        entity_id = uuid4()
        type_id = uuid4()
        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        from_snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=1,
            properties={"title": "Old Title", "status": "draft"},
            valid_from=base_time,
            valid_to=base_time + timedelta(hours=1),
            operation="CREATE",
        )

        to_snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=2,
            properties={"title": "New Title", "status": "draft"},
            valid_from=base_time + timedelta(hours=1),
            valid_to=None,
            operation="UPDATE",
        )

        diff = TimeTravelService.compute_diff(from_snapshot, to_snapshot)

        assert isinstance(diff, EntityDiff)
        assert diff.entity_id == entity_id
        assert diff.from_version == 1
        assert diff.to_version == 2
        assert diff.from_time == from_snapshot.valid_from
        assert diff.to_time == to_snapshot.valid_from
        assert diff.has_changes is True
        assert len(diff.changes) == 1

        title_change = diff.changes[0]
        assert title_change.field == "title"
        assert title_change.old_value == "Old Title"
        assert title_change.new_value == "New Title"
        assert title_change.change_type == "modified"

    def test_compute_diff_with_removed_property(self) -> None:
        """プロパティ削除の差分."""
        entity_id = uuid4()
        type_id = uuid4()
        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        from_snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=1,
            properties={"title": "Title", "description": "Some description"},
            valid_from=base_time,
            valid_to=base_time + timedelta(hours=1),
            operation="CREATE",
        )

        to_snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=2,
            properties={"title": "Title"},
            valid_from=base_time + timedelta(hours=1),
            valid_to=None,
            operation="UPDATE",
        )

        diff = TimeTravelService.compute_diff(from_snapshot, to_snapshot)

        assert diff.has_changes is True
        assert len(diff.changes) == 1

        removed_change = diff.changes[0]
        assert removed_change.field == "description"
        assert removed_change.old_value == "Some description"
        assert removed_change.new_value is None
        assert removed_change.change_type == "removed"

    def test_compute_diff_with_added_property(self) -> None:
        """プロパティ追加の差分."""
        entity_id = uuid4()
        type_id = uuid4()
        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        from_snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=1,
            properties={"title": "Title"},
            valid_from=base_time,
            valid_to=base_time + timedelta(hours=1),
            operation="CREATE",
        )

        to_snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=2,
            properties={"title": "Title", "tags": ["new", "important"]},
            valid_from=base_time + timedelta(hours=1),
            valid_to=None,
            operation="UPDATE",
        )

        diff = TimeTravelService.compute_diff(from_snapshot, to_snapshot)

        assert diff.has_changes is True
        assert len(diff.changes) == 1

        added_change = diff.changes[0]
        assert added_change.field == "tags"
        assert added_change.old_value is None
        assert added_change.new_value == ["new", "important"]
        assert added_change.change_type == "added"

    def test_compute_diff_no_changes(self) -> None:
        """変更なしの差分."""
        entity_id = uuid4()
        type_id = uuid4()
        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        from_snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=1,
            properties={"title": "Same Title", "status": "active"},
            valid_from=base_time,
            valid_to=base_time + timedelta(hours=1),
            operation="CREATE",
        )

        to_snapshot = EntitySnapshot(
            entity_id=entity_id,
            type_id=type_id,
            version=2,
            properties={"title": "Same Title", "status": "active"},
            valid_from=base_time + timedelta(hours=1),
            valid_to=None,
            operation="UPDATE",
        )

        diff = TimeTravelService.compute_diff(from_snapshot, to_snapshot)

        assert isinstance(diff, EntityDiff)
        assert diff.entity_id == entity_id
        assert diff.has_changes is False
        assert len(diff.changes) == 0


class TestFindSnapshotAtTime:
    """find_snapshot_at_time メソッドのテスト."""

    def _create_snapshots(self) -> tuple[list[EntitySnapshot], uuid4, uuid4]:
        """テスト用のスナップショットリストを作成."""
        entity_id = uuid4()
        type_id = uuid4()

        # 3つのスナップショット: 10:00-11:00, 11:00-12:00, 12:00-現在
        snapshots = [
            EntitySnapshot(
                entity_id=entity_id,
                type_id=type_id,
                version=1,
                properties={"title": "Version 1"},
                valid_from=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
                valid_to=datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC),
                operation="CREATE",
            ),
            EntitySnapshot(
                entity_id=entity_id,
                type_id=type_id,
                version=2,
                properties={"title": "Version 2"},
                valid_from=datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC),
                valid_to=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
                operation="UPDATE",
            ),
            EntitySnapshot(
                entity_id=entity_id,
                type_id=type_id,
                version=3,
                properties={"title": "Version 3"},
                valid_from=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
                valid_to=None,  # 現在有効
                operation="UPDATE",
            ),
        ]
        return snapshots, entity_id, type_id

    def test_find_snapshot_at_time_exact_match(self) -> None:
        """正確な時刻でのスナップショット検索."""
        snapshots, entity_id, _ = self._create_snapshots()

        # valid_from と完全に一致する時刻
        at_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC)
        result = TimeTravelService.find_snapshot_at_time(snapshots, at_time)

        assert result is not None
        assert result.version == 2
        assert result.properties["title"] == "Version 2"

    def test_find_snapshot_at_time_within_range(self) -> None:
        """有効期間内での検索."""
        snapshots, entity_id, _ = self._create_snapshots()

        # 10:30 は version 1 の有効期間内
        at_time = datetime(2024, 1, 1, 10, 30, 0, tzinfo=UTC)
        result = TimeTravelService.find_snapshot_at_time(snapshots, at_time)

        assert result is not None
        assert result.version == 1
        assert result.properties["title"] == "Version 1"

    def test_find_snapshot_at_time_current(self) -> None:
        """valid_to=None (現在有効) のスナップショット検索."""
        snapshots, entity_id, _ = self._create_snapshots()

        # 13:00 は version 3 (valid_to=None) の有効期間内
        at_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=UTC)
        result = TimeTravelService.find_snapshot_at_time(snapshots, at_time)

        assert result is not None
        assert result.version == 3
        assert result.is_current is True
        assert result.properties["title"] == "Version 3"

    def test_find_snapshot_at_time_before_any_record(self) -> None:
        """エンティティ作成前の時刻でNone返却."""
        snapshots, entity_id, _ = self._create_snapshots()

        # 09:00 は最初のスナップショット作成前
        at_time = datetime(2024, 1, 1, 9, 0, 0, tzinfo=UTC)
        result = TimeTravelService.find_snapshot_at_time(snapshots, at_time)

        assert result is None

    def test_find_snapshot_at_time_empty_list(self) -> None:
        """空のスナップショットリストでNone返却."""
        at_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = TimeTravelService.find_snapshot_at_time([], at_time)

        assert result is None

    def test_find_snapshot_at_time_at_boundary(self) -> None:
        """有効期間の境界値（valid_to と一致）での検索."""
        snapshots, entity_id, _ = self._create_snapshots()

        # 11:00 は version 1 の valid_to と一致
        # valid_from <= at_time < valid_to なので、version 2 が返される
        at_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC)
        result = TimeTravelService.find_snapshot_at_time(snapshots, at_time)

        assert result is not None
        # 11:00 は version 2 の valid_from なので version 2
        assert result.version == 2
