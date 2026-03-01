"""Query DSL domain models for complex query engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

# 最大トラバース深度
MAX_TRAVERSE_DEPTH = 5


class FilterOperator(StrEnum):
    """Filter operators for query conditions."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    REGEX = "regex"
    FULL_TEXT = "full_text"


class SortDirection(StrEnum):
    """Sort direction for query results."""

    ASC = "asc"
    DESC = "desc"


class TraverseDirection(StrEnum):
    """Direction for relationship traversal."""

    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BOTH = "both"


@dataclass
class FilterCondition:
    """Filter condition for query DSL.

    Supports nested AND/OR conditions for complex filtering.
    """

    field: str
    operator: FilterOperator
    value: str | int | float | bool | list[str] | list[int] | list[float] | None
    and_conditions: list[FilterCondition] | None = None
    or_conditions: list[FilterCondition] | None = None


@dataclass
class SortField:
    """Sort field configuration."""

    field: str
    direction: SortDirection = SortDirection.ASC


@dataclass
class TraverseConfig:
    """Configuration for relationship traversal.

    depth is clamped to MAX_TRAVERSE_DEPTH (5) in __post_init__.
    """

    relationship_type: str
    direction: TraverseDirection = TraverseDirection.OUTGOING
    depth: int = 1

    def __post_init__(self) -> None:
        """Clamp depth to MAX_TRAVERSE_DEPTH."""
        if self.depth > MAX_TRAVERSE_DEPTH:
            object.__setattr__(self, "depth", MAX_TRAVERSE_DEPTH)


@dataclass
class AggregateConfig:
    """Configuration for aggregate operations."""

    count: bool = False
    sum_field: str | None = None
    avg_field: str | None = None
    min_field: str | None = None
    max_field: str | None = None
    group_by: list[str] | None = None


@dataclass
class Query:
    """Query DSL root model.

    Supports filtering, sorting, pagination, traversal, aggregation,
    and time travel queries.
    """

    entity_type: str
    filter: FilterCondition | None = None
    sort: list[SortField] | None = None
    limit: int = field(default=100)
    offset: int = field(default=0)
    traverse: TraverseConfig | None = None
    aggregate: AggregateConfig | None = None
    at_time: datetime | None = None
    cursor: str | None = None
