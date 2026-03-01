"""QueryBuilder — FilterCondition DSL から SQLAlchemy フィルタを構築する.

FilterCondition ドメインモデルを SQLAlchemy の WHERE 句に変換する。
ソート・ページネーションの適用も提供。
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, Table, and_, asc, cast, desc, false, func, or_, text, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.elements import ColumnElement

from dynamic_ontology.domain.models.query import (
    FilterCondition,
    FilterOperator,
    SortDirection,
    SortField,
)

# フィルタ値の型エイリアス
FilterValue = str | int | float | bool | list[str] | list[int] | list[float] | None


def _get_numeric_type(value: int | float) -> type:
    """数値に対応する SQLAlchemy 型を返す."""
    from sqlalchemy import Float, Integer

    if isinstance(value, bool):
        raise ValueError("Boolean values should not use numeric type")
    return Float if isinstance(value, float) else Integer


def _build_typed_comparison(
    jsonb_field: ColumnElement[JSONB],
    value: FilterValue,
    op: str,
) -> ColumnElement[bool]:
    """型に応じた比較式を構築する（gt/gte/lt/lte 共通）.

    Args:
        jsonb_field: JSONB フィールドアクセサ.
        value: 比較値.
        op: Python 比較演算子名（"__gt__", "__ge__", "__lt__", "__le__"）.
    """
    if isinstance(value, (int, float)):
        lhs: Any = cast(jsonb_field.astext, type_=_get_numeric_type(value))
    else:
        lhs = jsonb_field.astext
        value = str(value)
    return getattr(lhs, op)(value)


def _normalize_list_value(value: FilterValue) -> list[str | int | float]:
    """値をリストに正規化する."""
    if isinstance(value, list):
        return list(value)
    if value is not None:
        return [str(value)] if isinstance(value, bool) else [value]
    return []


class QueryBuilder:
    """FilterCondition DSL から SQLAlchemy フィルタを構築する.

    JSONB properties カラムに対するフィルタ、ソート、ページネーションを提供。
    """

    def apply_sort(
        self,
        stmt: Select[tuple[Any, ...]],
        sorts: list[SortField],
        table: Table,
    ) -> Select[tuple[Any, ...]]:
        """ソート ORDER BY を適用する."""
        if not sorts:
            return stmt

        properties_col = table.c.properties
        order_clauses = []
        for sort_field in sorts:
            jsonb_field = properties_col[sort_field.field].astext
            direction_fn = desc if sort_field.direction == SortDirection.DESC else asc
            order_clauses.append(direction_fn(jsonb_field))

        return stmt.order_by(*order_clauses)

    def apply_pagination(
        self,
        stmt: Select[tuple[Any, ...]],
        limit: int = 100,
        offset: int = 0,
    ) -> Select[tuple[Any, ...]]:
        """LIMIT / OFFSET ページネーションを適用する."""
        stmt = stmt.limit(limit)
        if offset > 0:
            stmt = stmt.offset(offset)
        return stmt

    def apply_cursor_pagination(
        self,
        stmt: Select[tuple[Any, ...]],
        table: Table,
        cursor_created_at: datetime,
        cursor_id: UUID,
        limit: int = 100,
    ) -> Select[tuple[Any, ...]]:
        """カーソルベースのページネーションを適用する."""
        from sqlalchemy import literal, tuple_

        cursor_condition = tuple_(table.c.created_at, table.c.id) < tuple_(
            literal(cursor_created_at), literal(cursor_id)
        )
        return stmt.where(cursor_condition).limit(limit)

    def build_filter(self, condition: FilterCondition, table: Table) -> ColumnElement[bool]:
        """FilterCondition から SQLAlchemy フィルタ式を構築する.

        Raises:
            ValueError: フィールドが空、またはオペレータが未対応の場合.
        """
        if not condition.field or condition.field.strip() == "":
            raise ValueError("field cannot be empty")

        base_filter = self._build_comparison_filter(condition, table)
        return self._apply_composite_conditions(base_filter, condition, table)

    # ------------------------------------------------------------------
    # 複合条件
    # ------------------------------------------------------------------

    def _apply_composite_conditions(
        self,
        base_filter: ColumnElement[bool],
        condition: FilterCondition,
        table: Table,
    ) -> ColumnElement[bool]:
        """AND/OR 複合条件を適用する."""
        result = base_filter

        if condition.and_conditions:
            and_filters = [result] + [self.build_filter(c, table) for c in condition.and_conditions]
            result = and_(*and_filters)

        if condition.or_conditions:
            or_filters = [result] + [self.build_filter(c, table) for c in condition.or_conditions]
            result = or_(*or_filters)

        return result

    # ------------------------------------------------------------------
    # 比較フィルタ構築
    # ------------------------------------------------------------------

    def _build_comparison_filter(
        self, condition: FilterCondition, table: Table
    ) -> ColumnElement[bool]:
        """単一条件の比較フィルタを構築する."""
        jsonb_field = table.c.properties[condition.field]
        return self._apply_operator(jsonb_field, condition.operator, condition.value)

    # ------------------------------------------------------------------
    # オペレータディスパッチ
    # ------------------------------------------------------------------

    def _apply_operator(
        self,
        jsonb_field: ColumnElement[JSONB],
        operator: FilterOperator,
        value: FilterValue,
    ) -> ColumnElement[bool]:
        """オペレータに応じたフィルタ式を返す.

        Raises:
            ValueError: 未対応のオペレータの場合.
        """
        builder = _OPERATOR_DISPATCH.get(operator)
        if builder is None:
            raise ValueError(f"Unsupported operator: {operator}")
        return builder(jsonb_field, value)


# ------------------------------------------------------------------
# オペレータ実装（モジュールレベル関数）
# ------------------------------------------------------------------


def _build_eq(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """EQ（等号）フィルタ."""
    if isinstance(value, str):
        return jsonb_field.astext == value
    if isinstance(value, bool):
        return jsonb_field.astext == str(value).lower()
    if isinstance(value, (int, float)):
        return cast(jsonb_field.astext, type_=_get_numeric_type(value)) == value
    return jsonb_field == cast(value, JSONB)


def _build_ne(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """NE（不等号）フィルタ."""
    if isinstance(value, str):
        return jsonb_field.astext != value
    if isinstance(value, bool):
        return jsonb_field.astext != str(value).lower()
    if isinstance(value, (int, float)):
        return cast(jsonb_field.astext, type_=_get_numeric_type(value)) != value
    return jsonb_field != cast(value, JSONB)


def _build_gt(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """GT（より大きい）フィルタ."""
    return _build_typed_comparison(jsonb_field, value, "__gt__")


def _build_gte(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """GTE（以上）フィルタ."""
    return _build_typed_comparison(jsonb_field, value, "__ge__")


def _build_lt(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """LT（より小さい）フィルタ."""
    return _build_typed_comparison(jsonb_field, value, "__lt__")


def _build_lte(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """LTE（以下）フィルタ."""
    return _build_typed_comparison(jsonb_field, value, "__le__")


def _build_in(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """IN フィルタ."""
    values_list = _normalize_list_value(value)
    if not values_list:
        return false()
    return jsonb_field.astext.in_([str(v) for v in values_list])


def _build_not_in(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """NOT IN フィルタ."""
    values_list = _normalize_list_value(value)
    if not values_list:
        return true()
    return jsonb_field.astext.notin_([str(v) for v in values_list])


def _build_contains(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """CONTAINS（部分一致）フィルタ."""
    return jsonb_field.astext.like(f"%{str(value) if value is not None else ''}%")


def _build_starts_with(
    jsonb_field: ColumnElement[JSONB], value: FilterValue
) -> ColumnElement[bool]:
    """STARTS_WITH（前方一致）フィルタ."""
    return jsonb_field.astext.like(f"{str(value) if value is not None else ''}%")


def _build_ends_with(
    jsonb_field: ColumnElement[JSONB], value: FilterValue
) -> ColumnElement[bool]:
    """ENDS_WITH（後方一致）フィルタ."""
    return jsonb_field.astext.like(f"%{str(value) if value is not None else ''}")


def _build_is_null(jsonb_field: ColumnElement[JSONB], _value: FilterValue) -> ColumnElement[bool]:
    """IS_NULL フィルタ."""
    return jsonb_field.is_(None)


def _build_is_not_null(
    jsonb_field: ColumnElement[JSONB], _value: FilterValue
) -> ColumnElement[bool]:
    """IS_NOT_NULL フィルタ."""
    return jsonb_field.isnot(None)


def _build_regex(jsonb_field: ColumnElement[JSONB], value: FilterValue) -> ColumnElement[bool]:
    """REGEX（正規表現）フィルタ."""
    return jsonb_field.astext.op("~")(str(value) if value is not None else "")


def _build_full_text(
    jsonb_field: ColumnElement[JSONB], value: FilterValue
) -> ColumnElement[bool]:
    """FULL_TEXT（全文検索）フィルタ."""
    search_text = str(value) if value is not None else ""
    words = search_text.split()
    if not words:
        return false()
    tsquery_text = " & ".join(words)
    return func.to_tsvector(text("'simple'"), jsonb_field.astext).op("@@")(
        func.to_tsquery(text("'simple'"), tsquery_text)
    )


# オペレータ → ビルダー関数のディスパッチテーブル
_OPERATOR_DISPATCH: dict[
    FilterOperator,
    Any,
] = {
    FilterOperator.EQ: _build_eq,
    FilterOperator.NE: _build_ne,
    FilterOperator.GT: _build_gt,
    FilterOperator.GTE: _build_gte,
    FilterOperator.LT: _build_lt,
    FilterOperator.LTE: _build_lte,
    FilterOperator.IN: _build_in,
    FilterOperator.NOT_IN: _build_not_in,
    FilterOperator.CONTAINS: _build_contains,
    FilterOperator.STARTS_WITH: _build_starts_with,
    FilterOperator.ENDS_WITH: _build_ends_with,
    FilterOperator.IS_NULL: _build_is_null,
    FilterOperator.IS_NOT_NULL: _build_is_not_null,
    FilterOperator.REGEX: _build_regex,
    FilterOperator.FULL_TEXT: _build_full_text,
}
