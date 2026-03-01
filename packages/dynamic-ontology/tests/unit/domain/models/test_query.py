"""Test Query DSL domain models."""

from datetime import UTC, datetime

from dynamic_ontology.domain.models.query import (
    AggregateConfig,
    FilterCondition,
    FilterOperator,
    Query,
    SortDirection,
    SortField,
    TraverseConfig,
    TraverseDirection,
)


class TestFilterOperator:
    """Test FilterOperator enum."""

    def test_filter_operator_eq(self) -> None:
        """Test eq operator value."""
        assert FilterOperator.EQ == "eq"

    def test_filter_operator_ne(self) -> None:
        """Test ne operator value."""
        assert FilterOperator.NE == "ne"

    def test_filter_operator_gt(self) -> None:
        """Test gt operator value."""
        assert FilterOperator.GT == "gt"

    def test_filter_operator_gte(self) -> None:
        """Test gte operator value."""
        assert FilterOperator.GTE == "gte"

    def test_filter_operator_lt(self) -> None:
        """Test lt operator value."""
        assert FilterOperator.LT == "lt"

    def test_filter_operator_lte(self) -> None:
        """Test lte operator value."""
        assert FilterOperator.LTE == "lte"

    def test_filter_operator_in(self) -> None:
        """Test in operator value."""
        assert FilterOperator.IN == "in"

    def test_filter_operator_not_in(self) -> None:
        """Test not_in operator value."""
        assert FilterOperator.NOT_IN == "not_in"

    def test_filter_operator_contains(self) -> None:
        """Test contains operator value."""
        assert FilterOperator.CONTAINS == "contains"

    def test_filter_operator_starts_with(self) -> None:
        """Test starts_with operator value."""
        assert FilterOperator.STARTS_WITH == "starts_with"

    def test_filter_operator_ends_with(self) -> None:
        """Test ends_with operator value."""
        assert FilterOperator.ENDS_WITH == "ends_with"

    def test_filter_operator_is_null(self) -> None:
        """Test is_null operator value."""
        assert FilterOperator.IS_NULL == "is_null"

    def test_filter_operator_is_not_null(self) -> None:
        """Test is_not_null operator value."""
        assert FilterOperator.IS_NOT_NULL == "is_not_null"

    def test_filter_operator_regex(self) -> None:
        """Test regex operator value."""
        assert FilterOperator.REGEX == "regex"

    def test_filter_operator_full_text(self) -> None:
        """Test full_text operator value."""
        assert FilterOperator.FULL_TEXT == "full_text"

    def test_all_operators_are_string_enum(self) -> None:
        """All operators should be string values."""
        expected_operators = {
            "eq",
            "ne",
            "gt",
            "gte",
            "lt",
            "lte",
            "in",
            "not_in",
            "contains",
            "starts_with",
            "ends_with",
            "is_null",
            "is_not_null",
            "regex",
            "full_text",
        }
        actual_operators = {op.value for op in FilterOperator}
        assert actual_operators == expected_operators


class TestSortDirection:
    """Test SortDirection enum."""

    def test_sort_direction_asc(self) -> None:
        """Test asc direction value."""
        assert SortDirection.ASC == "asc"

    def test_sort_direction_desc(self) -> None:
        """Test desc direction value."""
        assert SortDirection.DESC == "desc"


class TestTraverseDirection:
    """Test TraverseDirection enum."""

    def test_traverse_direction_outgoing(self) -> None:
        """Test outgoing direction value."""
        assert TraverseDirection.OUTGOING == "outgoing"

    def test_traverse_direction_incoming(self) -> None:
        """Test incoming direction value."""
        assert TraverseDirection.INCOMING == "incoming"

    def test_traverse_direction_both(self) -> None:
        """Test both direction value."""
        assert TraverseDirection.BOTH == "both"


class TestFilterCondition:
    """Test FilterCondition dataclass."""

    def test_filter_condition_simple(self) -> None:
        """Test simple filter condition creation."""
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
        )
        assert condition.field == "status"
        assert condition.operator == FilterOperator.EQ
        assert condition.value == "active"
        assert condition.and_conditions is None
        assert condition.or_conditions is None

    def test_filter_condition_with_list_value(self) -> None:
        """Test filter condition with IN operator and list value."""
        condition = FilterCondition(
            field="priority",
            operator=FilterOperator.IN,
            value=[1, 2, 3],
        )
        assert condition.operator == FilterOperator.IN
        assert condition.value == [1, 2, 3]

    def test_filter_condition_is_null(self) -> None:
        """Test filter condition for null check."""
        condition = FilterCondition(
            field="deleted_at",
            operator=FilterOperator.IS_NULL,
            value=None,
        )
        assert condition.operator == FilterOperator.IS_NULL
        assert condition.value is None

    def test_filter_condition_with_and_conditions(self) -> None:
        """Test filter condition with nested AND conditions."""
        inner_condition = FilterCondition(
            field="priority",
            operator=FilterOperator.GTE,
            value=3,
        )
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
            and_conditions=[inner_condition],
        )
        assert condition.and_conditions is not None
        assert len(condition.and_conditions) == 1
        assert condition.and_conditions[0].field == "priority"

    def test_filter_condition_with_or_conditions(self) -> None:
        """Test filter condition with nested OR conditions."""
        or_condition = FilterCondition(
            field="type",
            operator=FilterOperator.EQ,
            value="urgent",
        )
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
            or_conditions=[or_condition],
        )
        assert condition.or_conditions is not None
        assert len(condition.or_conditions) == 1
        assert condition.or_conditions[0].value == "urgent"


class TestSortField:
    """Test SortField dataclass."""

    def test_sort_field_default_direction(self) -> None:
        """Test SortField with default ASC direction."""
        sort = SortField(field="created_at")
        assert sort.field == "created_at"
        assert sort.direction == SortDirection.ASC

    def test_sort_field_desc_direction(self) -> None:
        """Test SortField with DESC direction."""
        sort = SortField(field="updated_at", direction=SortDirection.DESC)
        assert sort.field == "updated_at"
        assert sort.direction == SortDirection.DESC


class TestTraverseConfig:
    """Test TraverseConfig dataclass."""

    def test_traverse_config_defaults(self) -> None:
        """Test TraverseConfig with default values."""
        config = TraverseConfig(relationship_type="owns")
        assert config.relationship_type == "owns"
        assert config.direction == TraverseDirection.OUTGOING
        assert config.depth == 1

    def test_traverse_config_custom_values(self) -> None:
        """Test TraverseConfig with custom values."""
        config = TraverseConfig(
            relationship_type="parent_of",
            direction=TraverseDirection.INCOMING,
            depth=3,
        )
        assert config.relationship_type == "parent_of"
        assert config.direction == TraverseDirection.INCOMING
        assert config.depth == 3

    def test_traverse_config_depth_clamped_to_max(self) -> None:
        """Test TraverseConfig depth is clamped to MAX_TRAVERSE_DEPTH (5)."""
        config = TraverseConfig(
            relationship_type="owns",
            depth=10,
        )
        assert config.depth == 5

    def test_traverse_config_depth_at_max(self) -> None:
        """Test TraverseConfig depth at exactly MAX_TRAVERSE_DEPTH."""
        config = TraverseConfig(
            relationship_type="owns",
            depth=5,
        )
        assert config.depth == 5

    def test_traverse_config_depth_below_max(self) -> None:
        """Test TraverseConfig depth below MAX_TRAVERSE_DEPTH is unchanged."""
        config = TraverseConfig(
            relationship_type="owns",
            depth=4,
        )
        assert config.depth == 4

    def test_traverse_config_direction_both(self) -> None:
        """Test TraverseConfig with BOTH direction."""
        config = TraverseConfig(
            relationship_type="related_to",
            direction=TraverseDirection.BOTH,
            depth=2,
        )
        assert config.direction == TraverseDirection.BOTH


class TestAggregateConfig:
    """Test AggregateConfig dataclass."""

    def test_aggregate_config_count_only(self) -> None:
        """Test AggregateConfig with count only."""
        config = AggregateConfig(count=True)
        assert config.count is True
        assert config.sum_field is None
        assert config.avg_field is None
        assert config.min_field is None
        assert config.max_field is None
        assert config.group_by is None

    def test_aggregate_config_sum_field(self) -> None:
        """Test AggregateConfig with sum field."""
        config = AggregateConfig(sum_field="amount")
        assert config.sum_field == "amount"

    def test_aggregate_config_avg_field(self) -> None:
        """Test AggregateConfig with avg field."""
        config = AggregateConfig(avg_field="rating")
        assert config.avg_field == "rating"

    def test_aggregate_config_min_max_fields(self) -> None:
        """Test AggregateConfig with min and max fields."""
        config = AggregateConfig(min_field="price", max_field="price")
        assert config.min_field == "price"
        assert config.max_field == "price"

    def test_aggregate_config_group_by(self) -> None:
        """Test AggregateConfig with group_by fields."""
        config = AggregateConfig(
            count=True,
            group_by=["category", "status"],
        )
        assert config.count is True
        assert config.group_by == ["category", "status"]

    def test_aggregate_config_all_fields(self) -> None:
        """Test AggregateConfig with all fields."""
        config = AggregateConfig(
            count=True,
            sum_field="quantity",
            avg_field="price",
            min_field="rating",
            max_field="rating",
            group_by=["category"],
        )
        assert config.count is True
        assert config.sum_field == "quantity"
        assert config.avg_field == "price"
        assert config.min_field == "rating"
        assert config.max_field == "rating"
        assert config.group_by == ["category"]


class TestQuery:
    """Test Query dataclass."""

    def test_query_minimal(self) -> None:
        """Test Query with minimal required fields."""
        query = Query(entity_type="Task")
        assert query.entity_type == "Task"
        assert query.filter is None
        assert query.sort is None
        assert query.limit == 100
        assert query.offset == 0
        assert query.traverse is None
        assert query.aggregate is None
        assert query.at_time is None

    def test_query_with_filter(self) -> None:
        """Test Query with filter condition."""
        filter_condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
        )
        query = Query(entity_type="Task", filter=filter_condition)
        assert query.filter is not None
        assert query.filter.field == "status"

    def test_query_with_sort(self) -> None:
        """Test Query with sort fields."""
        sort_fields = [
            SortField(field="priority", direction=SortDirection.DESC),
            SortField(field="created_at"),
        ]
        query = Query(entity_type="Task", sort=sort_fields)
        assert query.sort is not None
        assert len(query.sort) == 2
        assert query.sort[0].field == "priority"
        assert query.sort[0].direction == SortDirection.DESC

    def test_query_with_pagination(self) -> None:
        """Test Query with custom limit and offset."""
        query = Query(entity_type="Task", limit=50, offset=100)
        assert query.limit == 50
        assert query.offset == 100

    def test_query_with_traverse(self) -> None:
        """Test Query with traverse config."""
        traverse = TraverseConfig(
            relationship_type="assigned_to",
            direction=TraverseDirection.OUTGOING,
            depth=2,
        )
        query = Query(entity_type="Task", traverse=traverse)
        assert query.traverse is not None
        assert query.traverse.relationship_type == "assigned_to"

    def test_query_with_aggregate(self) -> None:
        """Test Query with aggregate config."""
        aggregate = AggregateConfig(count=True, group_by=["status"])
        query = Query(entity_type="Task", aggregate=aggregate)
        assert query.aggregate is not None
        assert query.aggregate.count is True

    def test_query_with_at_time(self) -> None:
        """Test Query with at_time for time travel."""
        past_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        query = Query(entity_type="Task", at_time=past_time)
        assert query.at_time == past_time

    def test_query_complex(self) -> None:
        """Test Query with multiple configurations."""
        filter_condition = FilterCondition(
            field="status",
            operator=FilterOperator.IN,
            value=["active", "pending"],
            and_conditions=[
                FilterCondition(
                    field="priority",
                    operator=FilterOperator.GTE,
                    value=3,
                ),
            ],
        )
        sort_fields = [
            SortField(field="priority", direction=SortDirection.DESC),
        ]
        traverse = TraverseConfig(
            relationship_type="assigned_to",
            direction=TraverseDirection.OUTGOING,
        )
        aggregate = AggregateConfig(count=True)
        at_time = datetime(2024, 6, 15, 10, 0, 0, tzinfo=UTC)

        query = Query(
            entity_type="Task",
            filter=filter_condition,
            sort=sort_fields,
            limit=25,
            offset=50,
            traverse=traverse,
            aggregate=aggregate,
            at_time=at_time,
        )

        assert query.entity_type == "Task"
        assert query.filter is not None
        assert query.filter.and_conditions is not None
        assert len(query.filter.and_conditions) == 1
        assert query.sort is not None
        assert len(query.sort) == 1
        assert query.limit == 25
        assert query.offset == 50
        assert query.traverse is not None
        assert query.aggregate is not None
        assert query.at_time == at_time
