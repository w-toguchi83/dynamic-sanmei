"""TimeTravelService - タイムトラベル操作のためのドメインサービス.

エンティティの履歴を扱うためのサービス。
スナップショット間の差分計算と時刻指定でのスナップショット検索を提供する。
"""

from datetime import datetime

from dynamic_ontology.domain.models.history import EntityDiff, EntitySnapshot, PropertyChange


class TimeTravelService:
    """タイムトラベル操作のためのドメインサービス.

    エンティティの過去の状態を取得したり、
    2つのスナップショット間の差分を計算するための静的メソッドを提供する。
    """

    @staticmethod
    def compute_diff(
        from_snapshot: EntitySnapshot,
        to_snapshot: EntitySnapshot,
    ) -> EntityDiff:
        """2つのスナップショット間の差分を計算.

        両方のスナップショットのプロパティを比較し、
        追加・変更・削除されたプロパティをPropertyChangeとして記録する。

        Args:
            from_snapshot: 比較元のスナップショット（古い方）
            to_snapshot: 比較先のスナップショット（新しい方）

        Returns:
            EntityDiff: 2つのスナップショット間の差分情報
        """
        changes: list[PropertyChange] = []

        from_props = from_snapshot.properties
        to_props = to_snapshot.properties

        # 全てのキーを取得（両方のスナップショットから）
        all_keys = set(from_props.keys()) | set(to_props.keys())

        for key in sorted(all_keys):  # ソートして順序を安定化
            old_value = from_props.get(key)
            new_value = to_props.get(key)

            # 値が異なる場合のみ変更として記録
            if old_value != new_value:
                changes.append(
                    PropertyChange(
                        field=key,
                        old_value=old_value,
                        new_value=new_value,
                    )
                )

        return EntityDiff(
            entity_id=from_snapshot.entity_id,
            from_version=from_snapshot.version,
            to_version=to_snapshot.version,
            from_time=from_snapshot.valid_from,
            to_time=to_snapshot.valid_from,
            changes=changes,
        )

    @staticmethod
    def find_snapshot_at_time(
        snapshots: list[EntitySnapshot],
        at_time: datetime,
    ) -> EntitySnapshot | None:
        """指定時刻に有効なスナップショットを検索.

        スナップショットのリストから、指定時刻に有効だったものを返す。
        有効期間は valid_from <= at_time < valid_to で判定する。
        valid_to が None の場合は現在有効とみなし、at_time >= valid_from で判定する。

        Args:
            snapshots: 検索対象のスナップショットリスト
            at_time: 検索する時刻

        Returns:
            EntitySnapshot | None: 指定時刻に有効なスナップショット、
                                   見つからない場合はNone
        """
        for snapshot in snapshots:
            valid_from = snapshot.valid_from
            valid_to = snapshot.valid_to

            # valid_from <= at_time の条件をまず確認
            if at_time < valid_from:
                continue

            # valid_to が None の場合は現在有効（上限なし）
            if valid_to is None:
                return snapshot

            # valid_from <= at_time < valid_to
            if at_time < valid_to:
                return snapshot

        return None
