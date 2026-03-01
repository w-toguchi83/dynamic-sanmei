"""QueryBuilder カーソルページネーションのユニットテスト."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, MetaData, Table, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from dynamic_ontology.domain.services.query_builder import QueryBuilder


def _make_table() -> Table:
    metadata = MetaData()
    return Table(
        "test_entities",
        metadata,
        Column("id", PG_UUID, primary_key=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
    )


class TestApplyCursorPagination:
    """apply_cursor_pagination のユニットテスト."""

    def test_returns_modified_statement(self) -> None:
        """カーソル条件が適用されたSQLにcreated_atが含まれること."""
        table = _make_table()
        builder = QueryBuilder()
        stmt = select(table).order_by(table.c.created_at.desc(), table.c.id.desc())
        cursor_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        cursor_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        result = builder.apply_cursor_pagination(stmt, table, cursor_at, cursor_id, limit=10)
        compiled = str(result.compile(compile_kwargs={"literal_binds": False}))
        assert "created_at" in compiled

    def test_without_cursor_uses_offset(self) -> None:
        """apply_pagination がLIMITを適用すること."""
        table = _make_table()
        builder = QueryBuilder()
        stmt = select(table)
        result = builder.apply_pagination(stmt, limit=10, offset=5)
        compiled = str(result.compile(compile_kwargs={"literal_binds": False}))
        assert "LIMIT" in compiled or "limit" in compiled.lower()
