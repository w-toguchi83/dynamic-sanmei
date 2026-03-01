"""エンティティバージョンロールバック用ドメインサービス.

エンティティのバージョンロールバック操作のためのドメインサービス。
ロールバックの妥当性検証と、ロールバック用 Entity の準備を担当する。
"""

from dynamic_ontology.domain.exceptions import InvalidRollbackError
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.history import EntitySnapshot


class RollbackService:
    """ロールバック操作のためのドメインサービス.

    エンティティを過去のバージョンに戻すための検証と準備を行う。
    実際の永続化は呼び出し元（ユースケース層）が担当する。
    """

    @staticmethod
    def validate_rollback(
        current_entity: Entity,
        target_snapshot: EntitySnapshot,
    ) -> None:
        """ロールバックの妥当性を検証.

        entity_id と type_id が一致することを確認する。
        不一致の場合は InvalidRollbackError を発生させる。

        Args:
            current_entity: 現在のエンティティ
            target_snapshot: ロールバック先のスナップショット

        Raises:
            InvalidRollbackError: entity_id または type_id が不一致の場合
        """
        if current_entity.id != target_snapshot.entity_id:
            raise InvalidRollbackError(
                f"entity_id mismatch: current={current_entity.id}, "
                f"target={target_snapshot.entity_id}"
            )

        if current_entity.type_id != target_snapshot.type_id:
            raise InvalidRollbackError(
                f"type_id mismatch: current={current_entity.type_id}, "
                f"target={target_snapshot.type_id}"
            )

    @staticmethod
    def prepare_rollback_entity(
        current_entity: Entity,
        target_snapshot: EntitySnapshot,
    ) -> Entity:
        """ロールバック用の Entity を準備.

        current_entity のメタデータ（id, type_id, version, created_at, updated_at）を保持し、
        target_snapshot の properties を適用した新しい Entity を返す。

        Args:
            current_entity: 現在のエンティティ
            target_snapshot: ロールバック先のスナップショット

        Returns:
            ロールバック用の新しい Entity インスタンス
        """
        return Entity(
            id=current_entity.id,
            type_id=current_entity.type_id,
            version=current_entity.version,
            properties=dict(target_snapshot.properties),
            created_at=current_entity.created_at,
            updated_at=current_entity.updated_at,
        )

    @staticmethod
    def find_target_snapshot(
        snapshots: list[EntitySnapshot],
        version: int | None = None,
    ) -> EntitySnapshot | None:
        """指定バージョンのスナップショットを検索.

        version に一致するスナップショットを返す。見つからなければ None を返す。

        Args:
            snapshots: スナップショットのリスト
            version: 検索対象のバージョン番号

        Returns:
            一致するスナップショット、見つからなければ None
        """
        if version is None:
            return None

        for snapshot in snapshots:
            if snapshot.version == version:
                return snapshot

        return None
