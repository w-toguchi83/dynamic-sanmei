"""Test QueryBuilder for building SQL filters from FilterCondition."""

import pytest
from sqlalchemy import Column, MetaData, Table, select
from sqlalchemy.dialects.postgresql import JSONB

from dynamic_ontology.domain.models.query import (
    FilterCondition,
    FilterOperator,
    SortDirection,
    SortField,
)
from dynamic_ontology.domain.services.query_builder import QueryBuilder


@pytest.fixture
def metadata() -> MetaData:
    """Create SQLAlchemy metadata for test tables."""
    return MetaData()


@pytest.fixture
def entities_table(metadata: MetaData) -> Table:
    """Create a mock entities table with JSONB properties column."""
    return Table(
        "entities",
        metadata,
        Column("properties", JSONB),
    )


@pytest.fixture
def query_builder() -> QueryBuilder:
    """Create QueryBuilder instance."""
    return QueryBuilder()


class TestBuildFilterValidation:
    """Test input validation for build_filter method."""

    def test_build_filter_raises_for_empty_field(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test that empty field raises ValueError."""
        condition = FilterCondition(
            field="",
            operator=FilterOperator.EQ,
            value="test",
        )

        with pytest.raises(ValueError, match="field cannot be empty"):
            query_builder.build_filter(condition, entities_table)


class TestBuildFilterEqOperator:
    """Test EQ (equals) operator."""

    def test_build_filter_eq_string(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test EQ operator with string value."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
        )

        result = query_builder.build_filter(condition, entities_table)

        # Compile to PostgreSQL dialect to verify SQL
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "status" in sql
        assert "active" in sql
        assert "=" in sql

    def test_build_filter_eq_integer(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test EQ operator with integer value."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.EQ,
            value=5,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "priority" in sql
        assert "5" in sql

    def test_build_filter_eq_float(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test EQ operator with float value."""
        condition = FilterCondition(
            field="score",
            operator=FilterOperator.EQ,
            value=3.14,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "score" in sql

    def test_build_filter_eq_boolean(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test EQ operator with boolean value."""
        condition = FilterCondition(
            field="is_active",
            operator=FilterOperator.EQ,
            value=True,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "is_active" in sql


class TestBuildFilterNeOperator:
    """Test NE (not equals) operator."""

    def test_build_filter_ne_string(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test NE operator with string value."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.NE,
            value="deleted",
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "status" in sql
        assert "deleted" in sql
        # Should use != or <> operator
        assert "!=" in sql or "<>" in sql

    def test_build_filter_ne_integer(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test NE operator with integer value."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.NE,
            value=0,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "!=" in sql or "<>" in sql


class TestBuildFilterGtOperator:
    """Test GT (greater than) operator."""

    def test_build_filter_gt_integer(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test GT operator with integer value."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.GT,
            value=3,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "priority" in sql
        assert ">" in sql
        # Should NOT be >=
        assert ">=" not in sql

    def test_build_filter_gt_float(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test GT operator with float value."""
        condition = FilterCondition(
            field="score",
            operator=FilterOperator.GT,
            value=2.5,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert ">" in sql
        assert ">=" not in sql


class TestBuildFilterGteOperator:
    """Test GTE (greater than or equal) operator."""

    def test_build_filter_gte_integer(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test GTE operator with integer value."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.GTE,
            value=3,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "priority" in sql
        assert ">=" in sql

    def test_build_filter_gte_float(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test GTE operator with float value."""
        condition = FilterCondition(
            field="score",
            operator=FilterOperator.GTE,
            value=2.5,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert ">=" in sql


class TestBuildFilterLtOperator:
    """Test LT (less than) operator."""

    def test_build_filter_lt_integer(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test LT operator with integer value."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.LT,
            value=5,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "priority" in sql
        assert "<" in sql
        # Should NOT be <=
        assert "<=" not in sql and ">=" not in sql

    def test_build_filter_lt_float(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test LT operator with float value."""
        condition = FilterCondition(
            field="score",
            operator=FilterOperator.LT,
            value=7.5,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "<" in sql


class TestBuildFilterLteOperator:
    """Test LTE (less than or equal) operator."""

    def test_build_filter_lte_integer(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test LTE operator with integer value."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.LTE,
            value=5,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "priority" in sql
        assert "<=" in sql

    def test_build_filter_lte_float(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test LTE operator with float value."""
        condition = FilterCondition(
            field="score",
            operator=FilterOperator.LTE,
            value=7.5,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "<=" in sql


class TestBuildFilterJsonbAccess:
    """Test JSONB property access in generated SQL."""

    def test_build_filter_uses_jsonb_arrow_operator(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test that filter uses JSONB arrow operators for property access."""
        condition = FilterCondition(
            field="nested_field",
            operator=FilterOperator.EQ,
            value="test_value",
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        # Should use -> or ->> operator for JSONB access
        assert "->" in sql or "->>" in sql


class TestBuildFilterReturnType:
    """Test return type of build_filter method."""

    def test_build_filter_returns_column_element(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test that build_filter returns a ColumnElement[bool]."""
        from sqlalchemy.sql.elements import ColumnElement

        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
        )

        result = query_builder.build_filter(condition, entities_table)

        assert isinstance(result, ColumnElement)


class TestBuildFilterInOperator:
    """Test IN operator."""

    def test_build_filter_in_string_list(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test IN operator with list of strings."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.IN,
            value=["active", "pending", "review"],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "status" in sql
        assert "IN" in sql.upper()
        assert "active" in sql
        assert "pending" in sql
        assert "review" in sql

    def test_build_filter_in_integer_list(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test IN operator with list of integers."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.IN,
            value=[1, 2, 3],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "priority" in sql
        assert "IN" in sql.upper()

    def test_build_filter_in_empty_list(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test IN operator with empty list returns false condition."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.IN,
            value=[],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        # Empty IN should generate a false-like condition
        assert "false" in sql.lower() or "1 = 0" in sql or "1 != 1" in sql


class TestBuildFilterNotInOperator:
    """Test NOT_IN operator."""

    def test_build_filter_not_in_string_list(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test NOT_IN operator with list of strings."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.NOT_IN,
            value=["deleted", "archived"],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "status" in sql
        assert "NOT IN" in sql.upper()
        assert "deleted" in sql
        assert "archived" in sql

    def test_build_filter_not_in_integer_list(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test NOT_IN operator with list of integers."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.NOT_IN,
            value=[0, -1],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "NOT IN" in sql.upper()

    def test_build_filter_not_in_empty_list(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test NOT_IN operator with empty list returns true condition."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.NOT_IN,
            value=[],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        # Empty NOT IN should generate a true-like condition
        assert "true" in sql.lower() or "1 = 1" in sql


class TestBuildFilterContainsOperator:
    """Test CONTAINS operator (substring match)."""

    def test_build_filter_contains_string(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test CONTAINS operator for substring matching."""
        condition = FilterCondition(
            field="name",
            operator=FilterOperator.CONTAINS,
            value="test",
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "name" in sql
        assert "LIKE" in sql.upper()
        assert "%test%" in sql


class TestBuildFilterStartsWithOperator:
    """Test STARTS_WITH operator (prefix match)."""

    def test_build_filter_starts_with_string(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test STARTS_WITH operator for prefix matching."""
        condition = FilterCondition(
            field="name",
            operator=FilterOperator.STARTS_WITH,
            value="prefix",
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "name" in sql
        assert "LIKE" in sql.upper()
        # Should be prefix% not %prefix%
        assert "prefix%" in sql
        # Should not have leading %
        assert "%prefix" not in sql or "%prefix%" not in sql


class TestBuildFilterEndsWithOperator:
    """Test ENDS_WITH operator (suffix match)."""

    def test_build_filter_ends_with_string(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test ENDS_WITH operator for suffix matching."""
        condition = FilterCondition(
            field="name",
            operator=FilterOperator.ENDS_WITH,
            value="suffix",
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "name" in sql
        assert "LIKE" in sql.upper()
        # Should be %suffix not %suffix% or suffix%
        assert "%suffix" in sql
        # The pattern should end at suffix, not have trailing %
        # However we need to be careful about E'%suffix' format
        assert "suffix%" not in sql or "'%suffix'" in sql


class TestBuildFilterIsNullOperator:
    """Test IS_NULL operator."""

    def test_build_filter_is_null(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test IS_NULL operator checks for null field."""
        condition = FilterCondition(
            field="optional_field",
            operator=FilterOperator.IS_NULL,
            value=None,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "optional_field" in sql
        # Should check IS NULL
        assert "IS NULL" in sql.upper()


class TestBuildFilterIsNotNullOperator:
    """Test IS_NOT_NULL operator."""

    def test_build_filter_is_not_null(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test IS_NOT_NULL operator checks for non-null field."""
        condition = FilterCondition(
            field="required_field",
            operator=FilterOperator.IS_NOT_NULL,
            value=None,
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "required_field" in sql
        # Should check IS NOT NULL
        assert "IS NOT NULL" in sql.upper()


class TestBuildFilterAndConditions:
    """Test AND composite conditions."""

    def test_build_filter_with_and_conditions(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test filter with AND conditions."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
            and_conditions=[
                FilterCondition(
                    field="priority",
                    operator=FilterOperator.GT,
                    value=3,
                ),
                FilterCondition(
                    field="is_verified",
                    operator=FilterOperator.EQ,
                    value=True,
                ),
            ],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "status" in sql
        assert "priority" in sql
        assert "is_verified" in sql
        assert "AND" in sql.upper()

    def test_build_filter_with_multiple_and_conditions(
        self, query_builder: QueryBuilder, entities_table: Table
    ) -> None:
        """Test filter with multiple AND conditions."""
        condition = FilterCondition(
            field="a",
            operator=FilterOperator.EQ,
            value="1",
            and_conditions=[
                FilterCondition(field="b", operator=FilterOperator.EQ, value="2"),
                FilterCondition(field="c", operator=FilterOperator.EQ, value="3"),
                FilterCondition(field="d", operator=FilterOperator.EQ, value="4"),
            ],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        # All fields should be present
        for f in ["a", "b", "c", "d"]:
            assert f"'{f}'" in sql


class TestBuildFilterOrConditions:
    """Test OR composite conditions."""

    def test_build_filter_with_or_conditions(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test filter with OR conditions."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
            or_conditions=[
                FilterCondition(
                    field="status",
                    operator=FilterOperator.EQ,
                    value="pending",
                ),
                FilterCondition(
                    field="status",
                    operator=FilterOperator.EQ,
                    value="review",
                ),
            ],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "status" in sql
        assert "OR" in sql.upper()
        assert "active" in sql
        assert "pending" in sql
        assert "review" in sql


class TestBuildFilterNestedConditions:
    """Test nested AND/OR composite conditions."""

    def test_build_filter_with_nested_and_in_or(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test OR condition containing AND conditions."""
        # (status = 'active' AND priority > 3) OR (status = 'pending' AND priority = 1)
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
            and_conditions=[
                FilterCondition(
                    field="priority",
                    operator=FilterOperator.GT,
                    value=3,
                ),
            ],
            or_conditions=[
                FilterCondition(
                    field="status",
                    operator=FilterOperator.EQ,
                    value="pending",
                    and_conditions=[
                        FilterCondition(
                            field="priority",
                            operator=FilterOperator.EQ,
                            value=1,
                        ),
                    ],
                ),
            ],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "AND" in sql.upper()
        assert "OR" in sql.upper()

    def test_build_filter_with_nested_or_in_and(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test AND condition containing OR conditions."""
        # status = 'active' AND (priority = 1 OR priority = 2)
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
            and_conditions=[
                FilterCondition(
                    field="priority",
                    operator=FilterOperator.EQ,
                    value=1,
                    or_conditions=[
                        FilterCondition(
                            field="priority",
                            operator=FilterOperator.EQ,
                            value=2,
                        ),
                    ],
                ),
            ],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "properties" in sql
        assert "AND" in sql.upper()
        assert "OR" in sql.upper()

    def test_build_filter_deeply_nested_conditions(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test deeply nested composite conditions."""
        # a = 1 AND (b = 2 OR (c = 3 AND d = 4))
        condition = FilterCondition(
            field="a",
            operator=FilterOperator.EQ,
            value=1,
            and_conditions=[
                FilterCondition(
                    field="b",
                    operator=FilterOperator.EQ,
                    value=2,
                    or_conditions=[
                        FilterCondition(
                            field="c",
                            operator=FilterOperator.EQ,
                            value=3,
                            and_conditions=[
                                FilterCondition(
                                    field="d",
                                    operator=FilterOperator.EQ,
                                    value=4,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        # Should handle deep nesting without error
        assert "properties" in sql


class TestBuildFilterMixedOperators:
    """Test combination of advanced operators with composites."""

    def test_build_filter_in_with_and_conditions(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test IN operator combined with AND conditions."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.IN,
            value=["active", "pending"],
            and_conditions=[
                FilterCondition(
                    field="name",
                    operator=FilterOperator.CONTAINS,
                    value="test",
                ),
            ],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "IN" in sql.upper()
        assert "LIKE" in sql.upper()
        assert "AND" in sql.upper()

    def test_build_filter_null_checks_with_or(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test IS_NULL/IS_NOT_NULL combined with OR conditions."""
        condition = FilterCondition(
            field="optional",
            operator=FilterOperator.IS_NULL,
            value=None,
            or_conditions=[
                FilterCondition(
                    field="optional",
                    operator=FilterOperator.EQ,
                    value="default",
                ),
            ],
        )

        result = query_builder.build_filter(condition, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "IS NULL" in sql.upper()
        assert "OR" in sql.upper()


def _get_postgresql_dialect():
    """Get PostgreSQL dialect for SQL compilation."""
    from sqlalchemy.dialects import postgresql

    return postgresql.dialect()


class TestApplySortSingleField:
    """Test apply_sort with single sort field."""

    def test_apply_sort_asc(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_sort with ascending direction."""
        stmt = select(entities_table)
        sorts = [SortField(field="name", direction=SortDirection.ASC)]

        result = query_builder.apply_sort(stmt, sorts, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "ORDER BY" in sql.upper()
        assert "properties" in sql
        assert "name" in sql
        assert "ASC" in sql.upper()

    def test_apply_sort_desc(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_sort with descending direction."""
        stmt = select(entities_table)
        sorts = [SortField(field="created_at", direction=SortDirection.DESC)]

        result = query_builder.apply_sort(stmt, sorts, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "ORDER BY" in sql.upper()
        assert "properties" in sql
        assert "created_at" in sql
        assert "DESC" in sql.upper()


class TestApplySortMultipleFields:
    """Test apply_sort with multiple sort fields."""

    def test_apply_sort_multiple_fields(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_sort with multiple sort fields."""
        stmt = select(entities_table)
        sorts = [
            SortField(field="priority", direction=SortDirection.DESC),
            SortField(field="name", direction=SortDirection.ASC),
        ]

        result = query_builder.apply_sort(stmt, sorts, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "ORDER BY" in sql.upper()
        assert "priority" in sql
        assert "name" in sql
        # priority should come before name in ORDER BY
        priority_pos = sql.find("priority")
        name_pos = sql.find("name")
        assert priority_pos < name_pos

    def test_apply_sort_three_fields(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_sort with three sort fields."""
        stmt = select(entities_table)
        sorts = [
            SortField(field="a", direction=SortDirection.ASC),
            SortField(field="b", direction=SortDirection.DESC),
            SortField(field="c", direction=SortDirection.ASC),
        ]

        result = query_builder.apply_sort(stmt, sorts, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "ORDER BY" in sql.upper()
        # Check order: a, b, c
        a_pos = sql.find("'a'")
        b_pos = sql.find("'b'")
        c_pos = sql.find("'c'")
        assert a_pos < b_pos < c_pos


class TestApplySortEmptyList:
    """Test apply_sort with empty sort list."""

    def test_apply_sort_empty_list(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_sort with empty sort list returns unchanged statement."""
        stmt = select(entities_table)
        sorts: list[SortField] = []

        result = query_builder.apply_sort(stmt, sorts, entities_table)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        # No ORDER BY should be added
        assert "ORDER BY" not in sql.upper()


class TestApplyPaginationLimit:
    """Test apply_pagination with limit only."""

    def test_apply_pagination_limit_only(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_pagination with limit only."""
        stmt = select(entities_table)

        result = query_builder.apply_pagination(stmt, limit=50)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "LIMIT" in sql.upper()
        assert "50" in sql
        # No OFFSET should be added when offset is 0
        assert "OFFSET" not in sql.upper()

    def test_apply_pagination_default_limit(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_pagination with default limit."""
        stmt = select(entities_table)

        result = query_builder.apply_pagination(stmt)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "LIMIT" in sql.upper()
        assert "100" in sql


class TestBuildFilterRegexOperator:
    """Tests for REGEX filter operator."""

    def test_build_filter_regex_string(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """REGEX filter should use PostgreSQL ~ operator."""
        condition = FilterCondition(
            field="email",
            operator=FilterOperator.REGEX,
            value=r"^[a-z]+@example\.com$",
        )

        result = query_builder.build_filter(condition, entities_table)

        compiled = result.compile(dialect=_get_postgresql_dialect(), compile_kwargs={"literal_binds": True})
        sql = str(compiled)

        # PostgreSQL regex match operator
        assert "~" in sql
        assert "properties" in sql
        assert "email" in sql
        # Pattern should be present (escaped for SQL)
        assert "^[a-z]+@example" in sql
        assert "com$" in sql


class TestBuildFilterFullTextOperator:
    """Tests for FULL_TEXT filter operator."""

    def test_build_filter_full_text_single_word(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """FULL_TEXT filter should use PostgreSQL @@ operator with to_tsvector/to_tsquery."""
        condition = FilterCondition(
            field="description",
            operator=FilterOperator.FULL_TEXT,
            value="python",
        )

        result = query_builder.build_filter(condition, entities_table)

        compiled = result.compile(dialect=_get_postgresql_dialect(), compile_kwargs={"literal_binds": True})
        sql = str(compiled)

        # PostgreSQL full-text search
        assert "to_tsvector" in sql
        assert "to_tsquery" in sql
        assert "@@" in sql
        assert "simple" in sql  # Language-independent config

    def test_build_filter_full_text_multiple_words(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """FULL_TEXT filter with multiple words should use & (AND) operator."""
        condition = FilterCondition(
            field="content",
            operator=FilterOperator.FULL_TEXT,
            value="python web framework",
        )

        result = query_builder.build_filter(condition, entities_table)

        compiled = result.compile(dialect=_get_postgresql_dialect(), compile_kwargs={"literal_binds": True})
        sql = str(compiled)

        # Multiple words joined with &
        assert "python" in sql.lower()
        assert "web" in sql.lower()
        assert "framework" in sql.lower()

    def test_build_filter_full_text_empty_value(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """FULL_TEXT filter with empty value should return false condition."""
        condition = FilterCondition(
            field="content",
            operator=FilterOperator.FULL_TEXT,
            value="",
        )

        result = query_builder.build_filter(condition, entities_table)

        compiled = result.compile(dialect=_get_postgresql_dialect(), compile_kwargs={"literal_binds": True})
        sql = str(compiled)

        # Empty search should return false
        assert "false" in sql.lower()


class TestApplyPaginationLimitAndOffset:
    """Test apply_pagination with limit and offset."""

    def test_apply_pagination_with_offset(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_pagination with limit and positive offset."""
        stmt = select(entities_table)

        result = query_builder.apply_pagination(stmt, limit=20, offset=40)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "LIMIT" in sql.upper()
        assert "20" in sql
        assert "OFFSET" in sql.upper()
        assert "40" in sql

    def test_apply_pagination_zero_offset(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_pagination with zero offset does not add OFFSET clause."""
        stmt = select(entities_table)

        result = query_builder.apply_pagination(stmt, limit=25, offset=0)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "LIMIT" in sql.upper()
        assert "25" in sql
        # Zero offset should NOT add OFFSET clause
        assert "OFFSET" not in sql.upper()

    def test_apply_pagination_large_offset(self, query_builder: QueryBuilder, entities_table: Table) -> None:
        """Test apply_pagination with large offset."""
        stmt = select(entities_table)

        result = query_builder.apply_pagination(stmt, limit=10, offset=1000)
        compiled = result.compile(
            dialect=_get_postgresql_dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sql = str(compiled)

        assert "LIMIT" in sql.upper()
        assert "10" in sql
        assert "OFFSET" in sql.upper()
        assert "1000" in sql
