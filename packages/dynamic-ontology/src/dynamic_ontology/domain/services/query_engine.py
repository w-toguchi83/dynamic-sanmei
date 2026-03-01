"""QueryEngine — Query DSL の実行エントリーポイント.

クエリの解析・ルーティングを行い、通常クエリ・集約・走査・タイムトラベルの
各実行パスに委譲する。集約とリレーション走査のロジックは専用モジュールに分離。
"""

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    Select,
    String,
    Table,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.models.query import Query, SortField
from dynamic_ontology.domain.services.query_aggregation import AggregationExecutor
from dynamic_ontology.domain.services.query_builder import QueryBuilder
from dynamic_ontology.domain.services.query_traversal import TraversalExecutor


@dataclass
class QueryResult:
    """クエリ実行結果とページネーションメタデータ.

    Attributes:
        items: クエリに一致する Entity のリスト.
        total: ページネーション前の全件数.
        limit: 取得件数上限.
        offset: スキップ件数.
        related_entities: 走査で見つかった関連エンティティ.
        aggregations: 集約結果.
        next_cursor: 次ページのカーソル.
        has_more: 次ページが存在するか.
    """

    items: list[Entity] = field(default_factory=list)
    total: int = 0
    limit: int = 100
    offset: int = 0
    related_entities: dict[str, list[Entity]] = field(default_factory=dict)
    aggregations: dict[str, Any] | None = None
    next_cursor: str | None = None
    has_more: bool = False


class QueryEngine:
    """Query DSL を実行し、Entity ドメインオブジェクトを返す."""

    def __init__(self, session: AsyncSession, namespace_id: str) -> None:
        self._session = session
        self._namespace_id = namespace_id
        self._builder = QueryBuilder()
        self._aggregation = AggregationExecutor(session)
        self._traversal = TraversalExecutor(session, namespace_id)
        self._entities_table: Table | None = None

    # ------------------------------------------------------------------
    # パブリック API
    # ------------------------------------------------------------------

    async def execute(self, query: Query) -> QueryResult:
        """Query DSL を実行して結果を返す.

        実行パス:
        1. at_time 指定 → タイムトラベルクエリ
        2. aggregate 指定 → 集約クエリ
        3. それ以外 → 通常クエリ（+ オプションの走査）

        Args:
            query: Query DSL オブジェクト.

        Returns:
            QueryResult.

        Raises:
            ValueError: エンティティタイプが見つからない場合、
                        またはカーソルとカスタムソートを併用した場合.
        """
        type_id = await self._resolve_entity_type(query.entity_type)
        if type_id is None:
            raise ValueError(f"Entity type '{query.entity_type}' not found")

        if query.cursor is not None and query.sort:
            raise ValueError(
                "Cannot use cursor with custom sort. "
                "Use offset-based pagination for custom sort queries."
            )

        # タイムトラベル
        if query.at_time is not None:
            return await self._execute_at_time(query, type_id)

        # 集約
        if query.aggregate is not None:
            return await self._execute_with_aggregation(query, type_id)

        # 通常クエリ（+ オプション走査）
        items, total, next_cursor, has_more = await self._execute_base_query(query, type_id)

        related_entities: dict[str, list[Entity]] = {}
        if query.traverse is not None and items:
            related_entities = await self._traversal.execute(
                items=items,
                traverse_config=query.traverse,
                row_converter=self._row_to_entity,
            )

        return QueryResult(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
            related_entities=related_entities,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    # ------------------------------------------------------------------
    # ベースクエリ実行（通常パス・走査パス共通）
    # ------------------------------------------------------------------

    async def _execute_base_query(
        self,
        query: Query,
        type_id: str,
    ) -> tuple[list[Entity], int, str | None, bool]:
        """フィルタ・カウント・ソート・ページネーション・行変換を実行する.

        通常クエリと走査クエリで共通の基本処理。

        Args:
            query: Query DSL オブジェクト.
            type_id: 解決済みエンティティタイプ ID.

        Returns:
            (items, total, next_cursor, has_more) のタプル.
        """
        table = self._get_entities_table()

        stmt = select(table).where(
            table.c.type_id == type_id,
            table.c.namespace_id == self._namespace_id,
        )

        if query.filter is not None:
            stmt = stmt.where(self._builder.build_filter(query.filter, table))

        total = await self._count(stmt)

        stmt = self._apply_sort_and_pagination(
            stmt, table, query.sort, query.cursor, query.limit, query.offset
        )

        result = await self._session.execute(stmt)
        items = [self._row_to_entity(row) for row in result.fetchall()]

        next_cursor, has_more = self._compute_cursor_metadata(
            items, query.cursor, query.offset, query.limit, total
        )

        return items, total, next_cursor, has_more

    async def _count(self, stmt: Select[tuple[Any, ...]]) -> int:
        """SELECT 文の件数を取得する."""
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self._session.execute(count_stmt)
        return result.scalar() or 0

    # ------------------------------------------------------------------
    # 集約クエリ
    # ------------------------------------------------------------------

    async def _execute_with_aggregation(
        self,
        query: Query,
        type_id: str,
    ) -> QueryResult:
        """集約クエリを実行する.

        AggregationExecutor に委譲し、結果を QueryResult に変換する。
        """
        aggregate_config = query.aggregate
        if aggregate_config is None:
            return QueryResult(
                items=[], total=0, limit=query.limit, offset=query.offset, aggregations=None
            )

        table = self._get_entities_table()

        where_clause = (table.c.type_id == type_id) & (
            table.c.namespace_id == self._namespace_id
        )
        if query.filter is not None:
            where_clause = where_clause & self._builder.build_filter(query.filter, table)

        aggregations = await self._aggregation.execute(table, where_clause, aggregate_config)

        return QueryResult(
            items=[],
            total=0,
            limit=query.limit,
            offset=query.offset,
            aggregations=aggregations,
        )

    # ------------------------------------------------------------------
    # タイムトラベルクエリ
    # ------------------------------------------------------------------

    async def _execute_at_time(
        self,
        query: Query,
        type_id: str,
    ) -> QueryResult:
        """指定時刻時点のエンティティ状態を取得する.

        do_entity_history テーブルから DISTINCT ON で各エンティティの
        最新有効バージョンを取得する。
        """
        at_time = query.at_time
        if at_time is None:
            return QueryResult(items=[], total=0, limit=query.limit, offset=query.offset)

        stmt = text("""
            SELECT DISTINCT ON (entity_id)
                entity_id, type_id, version, properties, valid_from, valid_to
            FROM do_entity_history
            WHERE type_id = :type_id
              AND namespace_id = :namespace_id
              AND valid_from <= :at_time
              AND (valid_to IS NULL OR valid_to > :at_time)
            ORDER BY entity_id, version DESC
        """)

        result = await self._session.execute(
            stmt,
            {"type_id": type_id, "at_time": at_time, "namespace_id": self._namespace_id},
        )
        items = [self._history_row_to_entity(row) for row in result.fetchall()]
        total = len(items)

        paginated_items = items[query.offset : query.offset + query.limit]

        return QueryResult(
            items=paginated_items,
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    # ------------------------------------------------------------------
    # ソート・ページネーション
    # ------------------------------------------------------------------

    def _apply_sort_and_pagination(
        self,
        stmt: Select[tuple[Any, ...]],
        table: Table,
        sort: list[SortField] | None,
        cursor: str | None,
        limit: int,
        offset: int,
    ) -> Select[tuple[Any, ...]]:
        """ソートとページネーション（カーソルまたはオフセット）を適用する."""
        if sort:
            stmt = self._builder.apply_sort(stmt, sort, table)
        else:
            stmt = stmt.order_by(table.c.created_at.desc(), table.c.id.desc())

        if cursor is not None:
            from dynamic_ontology.domain.services.cursor import CursorValidationError, decode_cursor

            try:
                cursor_at, cursor_id = decode_cursor(cursor)
            except CursorValidationError as e:
                raise ValueError(str(e)) from e
            stmt = self._builder.apply_cursor_pagination(
                stmt, table, cursor_at, cursor_id, limit=limit
            )
        else:
            stmt = self._builder.apply_pagination(stmt, limit, offset)

        return stmt

    @staticmethod
    def _compute_cursor_metadata(
        items: list[Entity],
        cursor: str | None,
        offset: int,
        limit: int,
        total: int,
    ) -> tuple[str | None, bool]:
        """next_cursor と has_more を計算する."""
        if not items:
            return None, False

        has_more = len(items) == limit if cursor is not None else (offset + len(items)) < total

        next_cursor: str | None = None
        if has_more:
            from dynamic_ontology.domain.services.cursor import encode_cursor

            last = items[-1]
            next_cursor = encode_cursor(last.created_at, last.id)

        return next_cursor, has_more

    # ------------------------------------------------------------------
    # テーブル定義
    # ------------------------------------------------------------------

    def _get_entities_table(self) -> Table:
        """do_entities テーブルの SQLAlchemy Table を取得（遅延生成）."""
        if self._entities_table is None:
            metadata = MetaData()
            self._entities_table = Table(
                "do_entities",
                metadata,
                Column("id", PG_UUID, primary_key=True),
                Column("namespace_id", PG_UUID, nullable=False),
                Column("type_id", PG_UUID, nullable=False),
                Column("version", Integer, nullable=False),
                Column("properties", JSONB, nullable=False),
                Column("created_at", DateTime(timezone=True), nullable=False),
                Column("updated_at", DateTime(timezone=True), nullable=False),
                Column("changed_by", String(255), nullable=True),
            )
        return self._entities_table

    @staticmethod
    def _get_entity_history_table() -> Table:
        """do_entity_history テーブルの SQLAlchemy Table を取得."""
        metadata = MetaData()
        return Table(
            "do_entity_history",
            metadata,
            Column("id", PG_UUID, primary_key=True),
            Column("entity_id", PG_UUID, nullable=False),
            Column("type_id", PG_UUID, nullable=False),
            Column("version", Integer, nullable=False),
            Column("properties", JSONB, nullable=False),
            Column("valid_from", DateTime(timezone=True), nullable=False),
            Column("valid_to", DateTime(timezone=True)),
            Column("operation", String(20), nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )

    # ------------------------------------------------------------------
    # 行変換
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_uuid(value: object) -> UUID:
        """文字列または UUID をパースして UUID を返す."""
        return UUID(value) if isinstance(value, str) else value  # type: ignore[return-value]

    @staticmethod
    def _parse_properties(value: object) -> dict[str, Any]:
        """JSON 文字列または dict をパースして dict を返す."""
        return json.loads(value) if isinstance(value, str) else value  # type: ignore[return-value]

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        """DB 行を辞書に変換する."""
        if hasattr(row, "_mapping"):
            return dict(row._mapping)
        return {
            "id": row[0],
            "type_id": row[1],
            "version": row[2],
            "properties": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "changed_by": row[6] if len(row) > 6 else None,
        }

    @classmethod
    def _row_to_entity(cls, row: Any) -> Entity:
        """do_entities テーブルの行を Entity ドメインモデルに変換する."""
        row_dict = cls._row_to_dict(row)

        return Entity(
            id=cls._parse_uuid(row_dict["id"]),
            type_id=cls._parse_uuid(row_dict["type_id"]),
            version=row_dict["version"],
            properties=cls._parse_properties(row_dict["properties"]),
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
            changed_by=row_dict.get("changed_by"),
        )

    @classmethod
    def _history_row_to_entity(cls, row: Any) -> Entity:
        """do_entity_history テーブルの行を Entity ドメインモデルに変換する."""
        if hasattr(row, "_mapping"):
            row_dict = dict(row._mapping)
        else:
            row_dict = {
                "entity_id": row[0],
                "type_id": row[1],
                "version": row[2],
                "properties": row[3],
                "valid_from": row[4],
                "valid_to": row[5],
            }

        valid_from = row_dict["valid_from"]
        valid_to = row_dict.get("valid_to")

        return Entity(
            id=cls._parse_uuid(row_dict["entity_id"]),
            type_id=cls._parse_uuid(row_dict["type_id"]),
            version=row_dict["version"],
            properties=cls._parse_properties(row_dict["properties"]),
            created_at=valid_from,
            updated_at=valid_to if valid_to else valid_from,
        )

    # ------------------------------------------------------------------
    # 名前解決
    # ------------------------------------------------------------------

    async def _resolve_entity_type(self, name: str) -> str | None:
        """エンティティタイプ名を UUID に解決する."""
        query = text("""
            SELECT id FROM do_entity_types
            WHERE name = :name AND namespace_id = :namespace_id
        """)
        result = await self._session.execute(
            query, {"name": name, "namespace_id": self._namespace_id}
        )
        row = result.fetchone()
        return str(row[0]) if row is not None else None
