"""集約クエリ実行モジュール.

QueryEngine から分離された集約（count, sum, avg, min, max, group_by）の
実行ロジックを提供する。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Numeric, Table, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class AggregationExecutor:
    """集約クエリを実行する.

    count, sum, avg, min, max の各集約操作と GROUP BY をサポートする。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        table: Table,
        where_clause: Any,
        aggregate_config: Any,
    ) -> dict[str, Any]:
        """集約クエリを実行し、結果を辞書で返す.

        Args:
            table: do_entities テーブル.
            where_clause: WHERE 条件式.
            aggregate_config: AggregateConfig インスタンス.

        Returns:
            集約結果の辞書. group_by の場合は {"groups": [...]} 形式.
        """
        if aggregate_config.group_by:
            return await self._execute_grouped(table, where_clause, aggregate_config)
        return await self._execute_simple(table, where_clause, aggregate_config)

    def _build_aggregation_columns(
        self,
        properties_col: Any,
        aggregate_config: Any,
        *,
        include_count_by_default: bool = False,
    ) -> list[Any]:
        """集約カラムのリストを構築する（simple/grouped 共通）.

        Args:
            properties_col: JSONB properties カラム.
            aggregate_config: AggregateConfig インスタンス.
            include_count_by_default: 他の集約がない場合にデフォルトで count を含めるか.

        Returns:
            SELECT に渡す集約カラム式のリスト.
        """
        columns: list[Any] = []

        should_count = aggregate_config.count
        if include_count_by_default and not any(
            [
                aggregate_config.sum_field,
                aggregate_config.avg_field,
                aggregate_config.min_field,
                aggregate_config.max_field,
            ]
        ):
            should_count = True

        if should_count:
            columns.append(func.count().label("count"))

        if aggregate_config.sum_field:
            columns.append(func.sum(cast(properties_col[aggregate_config.sum_field].astext, Numeric)).label("sum"))

        if aggregate_config.avg_field:
            columns.append(func.avg(cast(properties_col[aggregate_config.avg_field].astext, Numeric)).label("avg"))

        if aggregate_config.min_field:
            columns.append(func.min(properties_col[aggregate_config.min_field].astext).label("min"))

        if aggregate_config.max_field:
            columns.append(func.max(properties_col[aggregate_config.max_field].astext).label("max"))

        return columns

    @staticmethod
    def _convert_row_values(row_dict: dict[str, Any]) -> dict[str, Any]:
        """行の値を JSON シリアライズ可能な型に変換する.

        Decimal → float への変換を行う。

        Args:
            row_dict: DB 行の辞書表現.

        Returns:
            変換後の辞書.
        """
        converted: dict[str, Any] = {}
        for key, value in row_dict.items():
            if value is not None and hasattr(value, "__float__"):
                converted[key] = float(value)
            else:
                converted[key] = value
        return converted

    async def _execute_simple(
        self,
        table: Table,
        where_clause: Any,
        aggregate_config: Any,
    ) -> dict[str, Any]:
        """グルーピングなしの単純集約を実行する.

        Args:
            table: do_entities テーブル.
            where_clause: WHERE 条件式.
            aggregate_config: AggregateConfig インスタンス.

        Returns:
            集約結果の辞書（例: {"count": 5, "sum": 100.0}）.
        """
        properties_col = table.c.properties
        select_columns = self._build_aggregation_columns(properties_col, aggregate_config)

        if not select_columns:
            return {}

        agg_stmt = select(*select_columns).select_from(table).where(where_clause)
        result = await self._session.execute(agg_stmt)
        row = result.fetchone()

        if row is None:
            return {}

        return self._convert_row_values(dict(row._mapping))

    async def _execute_grouped(
        self,
        table: Table,
        where_clause: Any,
        aggregate_config: Any,
    ) -> dict[str, Any]:
        """GROUP BY 付き集約を実行する.

        Args:
            table: do_entities テーブル.
            where_clause: WHERE 条件式.
            aggregate_config: AggregateConfig インスタンス.

        Returns:
            {"groups": [{"field": "value", "count": N}, ...]} 形式の辞書.
        """
        group_by_fields = aggregate_config.group_by
        if not group_by_fields:
            return {"groups": []}

        # サブクエリで WHERE を適用してから GROUP BY する
        base_stmt = select(table).where(where_clause)
        subq = base_stmt.subquery()
        properties_col = subq.c.properties

        # GROUP BY カラムの構築
        group_by_columns: list[Any] = []
        select_columns: list[Any] = []
        for group_field in group_by_fields:
            field_expr = properties_col[group_field].astext.label(group_field)
            select_columns.append(field_expr)
            group_by_columns.append(field_expr)

        # 集約カラムの追加（group_by 時はデフォルトで count を含める）
        agg_columns = self._build_aggregation_columns(properties_col, aggregate_config, include_count_by_default=True)
        select_columns.extend(agg_columns)

        agg_stmt = select(*select_columns).select_from(subq).group_by(*group_by_columns).order_by(*group_by_columns)

        result = await self._session.execute(agg_stmt)
        rows = result.fetchall()

        groups = [self._convert_row_values(dict(row._mapping)) for row in rows]

        return {"groups": groups}
