"""Query/QueryResult のカーソルフィールドのユニットテスト."""

from __future__ import annotations

from dynamic_ontology.domain.models.query import Query
from dynamic_ontology.domain.services.query_engine import QueryResult


class TestQueryCursorField:
    def test_default_cursor_is_none(self) -> None:
        q = Query(entity_type="test")
        assert q.cursor is None

    def test_cursor_can_be_set(self) -> None:
        q = Query(entity_type="test", cursor="abc123")
        assert q.cursor == "abc123"


class TestQueryResultCursorFields:
    def test_default_next_cursor_is_none(self) -> None:
        r = QueryResult()
        assert r.next_cursor is None

    def test_default_has_more_is_false(self) -> None:
        r = QueryResult()
        assert r.has_more is False

    def test_fields_can_be_set(self) -> None:
        r = QueryResult(next_cursor="xyz", has_more=True)
        assert r.next_cursor == "xyz"
        assert r.has_more is True
