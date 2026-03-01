"""リレーション走査モジュール.

QueryEngine から分離されたグラフ走査（relationship traversal）の
実行ロジックを提供する。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.query import TraverseDirection


class TraversalExecutor:
    """リレーションを辿ってエンティティを走査する.

    深さ制限とサイクル検出を備えた反復的な走査を実行する。
    """

    def __init__(self, session: AsyncSession, namespace_id: str) -> None:
        self._session = session
        self._namespace_id = namespace_id

    async def execute(
        self,
        items: list[Entity],
        traverse_config: Any,
        row_converter: Callable[[Any], Entity],
    ) -> dict[str, list[Entity]]:
        """各エンティティからリレーションを走査し、関連エンティティを返す.

        Args:
            items: 起点となるエンティティのリスト.
            traverse_config: TraverseConfig インスタンス.
            row_converter: DB 行を Entity に変換する関数.

        Returns:
            エンティティ ID → 関連エンティティリストのマッピング.

        Raises:
            ValueError: リレーションシップタイプが見つからない場合.
        """
        relationship_type_id = await self._resolve_relationship_type(traverse_config.relationship_type)
        if relationship_type_id is None:
            raise ValueError(f"Relationship type '{traverse_config.relationship_type}' not found")

        related_entities: dict[str, list[Entity]] = {}
        for entity in items:
            start_id = str(entity.id)
            seen_ids: set[str] = {start_id}
            related = await self._traverse_relationships(
                start_ids=[start_id],
                relationship_type_id=relationship_type_id,
                direction=traverse_config.direction,
                max_depth=traverse_config.depth,
                seen_ids=seen_ids,
                row_converter=row_converter,
            )
            related_entities[start_id] = related

        return related_entities

    async def _traverse_relationships(
        self,
        start_ids: list[str],
        relationship_type_id: str,
        direction: TraverseDirection,
        max_depth: int,
        seen_ids: set[str],
        row_converter: Callable[[Any], Entity],
    ) -> list[Entity]:
        """反復的にリレーションを走査する.

        深さ制限とサイクル検出により無限ループを防止する。

        Args:
            start_ids: 走査開始エンティティ ID リスト.
            relationship_type_id: 走査対象のリレーションシップタイプ ID.
            direction: 走査方向（outgoing, incoming, both）.
            max_depth: 最大走査深度.
            seen_ids: 訪問済みエンティティ ID の集合（サイクル検出用）.
            row_converter: DB 行を Entity に変換する関数.

        Returns:
            走査で見つかったエンティティのリスト.
        """
        if max_depth <= 0 or not start_ids:
            return []

        all_related: list[Entity] = []
        current_ids = start_ids

        for _depth in range(max_depth):
            if not current_ids:
                break

            next_ids = await self._get_connected_entity_ids(
                entity_ids=current_ids,
                relationship_type_id=relationship_type_id,
                direction=direction,
            )

            new_ids = [eid for eid in next_ids if eid not in seen_ids]
            if not new_ids:
                break

            seen_ids.update(new_ids)

            entities = await self._get_entities_by_ids(new_ids, row_converter)
            all_related.extend(entities)

            current_ids = new_ids

        return all_related

    async def _get_connected_entity_ids(
        self,
        entity_ids: list[str],
        relationship_type_id: str,
        direction: TraverseDirection,
    ) -> list[str]:
        """リレーションで接続されたエンティティ ID を取得する.

        Args:
            entity_ids: 起点エンティティ ID リスト.
            relationship_type_id: リレーションシップタイプ ID.
            direction: 走査方向.

        Returns:
            接続先エンティティ ID のリスト（重複排除済み）.
        """
        if not entity_ids:
            return []

        connected_ids: list[str] = []

        placeholders = ", ".join(f":id_{i}" for i in range(len(entity_ids)))
        params: dict[str, object] = {
            "type_id": relationship_type_id,
            "namespace_id": self._namespace_id,
        }
        for i, eid in enumerate(entity_ids):
            params[f"id_{i}"] = eid

        if direction in (TraverseDirection.OUTGOING, TraverseDirection.BOTH):
            query = text(f"""
                SELECT DISTINCT to_entity_id::text
                FROM do_relationships
                WHERE type_id = :type_id
                  AND namespace_id = :namespace_id
                  AND from_entity_id IN ({placeholders})
            """)
            result = await self._session.execute(query, params)
            connected_ids.extend(row[0] for row in result.fetchall())

        if direction in (TraverseDirection.INCOMING, TraverseDirection.BOTH):
            query = text(f"""
                SELECT DISTINCT from_entity_id::text
                FROM do_relationships
                WHERE type_id = :type_id
                  AND namespace_id = :namespace_id
                  AND to_entity_id IN ({placeholders})
            """)
            result = await self._session.execute(query, params)
            connected_ids.extend(row[0] for row in result.fetchall())

        # 順序を保持しつつ重複を排除
        seen: set[str] = set()
        unique_ids: list[str] = []
        for eid in connected_ids:
            if eid not in seen:
                seen.add(eid)
                unique_ids.append(eid)

        return unique_ids

    async def _get_entities_by_ids(
        self,
        entity_ids: list[str],
        row_converter: Callable[[Any], Entity],
    ) -> list[Entity]:
        """ID リストからエンティティを一括取得する.

        Args:
            entity_ids: エンティティ ID リスト.
            row_converter: DB 行を Entity に変換する関数.

        Returns:
            エンティティのリスト.
        """
        if not entity_ids:
            return []

        placeholders = ", ".join(f":id_{i}" for i in range(len(entity_ids)))
        params: dict[str, object] = {"namespace_id": self._namespace_id}
        for i, eid in enumerate(entity_ids):
            params[f"id_{i}"] = eid

        query = text(f"""
            SELECT id, type_id, version, properties, created_at, updated_at
            FROM do_entities
            WHERE namespace_id = :namespace_id AND id IN ({placeholders})
        """)

        result = await self._session.execute(query, params)
        return [row_converter(row) for row in result.fetchall()]

    async def _resolve_relationship_type(self, name: str) -> str | None:
        """リレーションシップタイプ名を UUID に解決する.

        Args:
            name: リレーションシップタイプ名.

        Returns:
            UUID 文字列、または見つからない場合は None.
        """
        query = text("""
            SELECT id FROM do_relationship_types
            WHERE name = :name AND namespace_id = :namespace_id
        """)
        result = await self._session.execute(query, {"name": name, "namespace_id": self._namespace_id})
        row = result.fetchone()
        return str(row[0]) if row is not None else None
