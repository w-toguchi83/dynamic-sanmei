"""Query API routes for executing complex queries."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dynamic_ontology.adapters.api.dependencies import get_namespace_id, get_query_engine
from dynamic_ontology.adapters.api.models import (
    AggregateConfigRequest,
    EntityResponse,
    FilterConditionRequest,
    QueryRequest,
    QueryResultResponse,
    RelatedEntitiesResponse,
    SortFieldRequest,
    TraverseConfigRequest,
)
from dynamic_ontology.domain.models.entity import Entity
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
from dynamic_ontology.domain.services.query_engine import QueryEngine, QueryResult

router = APIRouter(prefix="/query", tags=["Query"])

# Dependency injection type alias
Engine = Annotated[QueryEngine, Depends(get_query_engine)]
NamespaceIdDep = Annotated[str, Depends(get_namespace_id)]


def _convert_filter(request: FilterConditionRequest | None) -> FilterCondition | None:
    """Convert API filter request to domain FilterCondition.

    Handles nested AND/OR conditions recursively.

    Args:
        request: The API filter condition request, or None.

    Returns:
        Domain FilterCondition, or None if request is None.

    Raises:
        HTTPException: If operator is invalid.
    """
    if request is None:
        return None

    # Handle nested AND conditions (composite filter)
    if request.and_ is not None and len(request.and_) > 0:
        and_conditions = [_convert_filter(c) for c in request.and_]
        valid_conditions = [c for c in and_conditions if c is not None]
        if not valid_conditions:
            return None
        base = valid_conditions[0]
        if len(valid_conditions) > 1:
            base.and_conditions = valid_conditions[1:]
        return base

    # Handle nested OR conditions (composite filter)
    if request.or_ is not None and len(request.or_) > 0:
        or_conditions = [_convert_filter(c) for c in request.or_]
        valid_conditions = [c for c in or_conditions if c is not None]
        if not valid_conditions:
            return None
        base = valid_conditions[0]
        if len(valid_conditions) > 1:
            base.or_conditions = valid_conditions[1:]
        return base

    # Simple condition - must have field and op
    if request.field is None or request.op is None:
        return None

    # Convert operator string to FilterOperator enum
    try:
        operator = FilterOperator(request.op)
    except ValueError as err:
        valid_ops = [op.value for op in FilterOperator]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid filter operator '{request.op}'. Valid operators: {valid_ops}",
        ) from err

    return FilterCondition(
        field=request.field,
        operator=operator,
        value=request.value,
    )


def _convert_sort(sorts: list[SortFieldRequest]) -> list[SortField]:
    """Convert API sort request to domain SortField list.

    Args:
        sorts: List of API sort field requests.

    Returns:
        List of domain SortField objects.

    Raises:
        HTTPException: If sort direction is invalid.
    """
    result: list[SortField] = []
    for sort_req in sorts:
        try:
            direction = SortDirection(sort_req.order.lower())
        except ValueError as err:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort order '{sort_req.order}'. Valid orders: asc, desc",
            ) from err
        result.append(SortField(field=sort_req.field, direction=direction))
    return result


def _convert_traverse(
    traverse: TraverseConfigRequest | None,
) -> TraverseConfig | None:
    """Convert API traverse request to domain TraverseConfig.

    Args:
        traverse: The API traverse config request, or None.

    Returns:
        Domain TraverseConfig, or None if request is None.

    Raises:
        HTTPException: If direction is invalid.
    """
    if traverse is None:
        return None

    try:
        direction = TraverseDirection(traverse.direction.lower())
    except ValueError as err:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid traverse direction '{traverse.direction}'. Valid directions: outgoing, incoming, both",
        ) from err

    return TraverseConfig(
        relationship_type=traverse.type,
        direction=direction,
        depth=traverse.depth,
    )


def _convert_aggregate(
    aggregate: AggregateConfigRequest | None,
) -> AggregateConfig | None:
    """Convert API aggregate request to domain AggregateConfig.

    Args:
        aggregate: The API aggregate config request, or None.

    Returns:
        Domain AggregateConfig, or None if request is None.
    """
    if aggregate is None:
        return None

    return AggregateConfig(
        count=aggregate.count,
        sum_field=aggregate.sum,
        avg_field=aggregate.avg,
        min_field=aggregate.min,
        max_field=aggregate.max,
        group_by=aggregate.group_by if aggregate.group_by else None,
    )


def _entity_to_response(entity: Entity) -> EntityResponse:
    """Convert domain Entity to API response model.

    Args:
        entity: The domain Entity instance.

    Returns:
        API EntityResponse instance.
    """
    return EntityResponse(
        id=entity.id,
        type_id=entity.type_id,
        type_name=None,
        version=entity.version,
        properties=entity.properties,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _convert_result(result: QueryResult) -> QueryResultResponse:
    """Convert QueryEngine result to API response.

    Args:
        result: The QueryResult from QueryEngine.

    Returns:
        API QueryResultResponse.
    """
    items = [_entity_to_response(entity) for entity in result.items]

    # Convert related_entities if present
    related_entities_response: list[RelatedEntitiesResponse] | None = None
    if result.related_entities:
        related_entities_response = [
            RelatedEntitiesResponse(
                entity_id=entity_id,
                related=[_entity_to_response(e) for e in related],
            )
            for entity_id, related in result.related_entities.items()
        ]

    return QueryResultResponse(
        items=items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        aggregations=result.aggregations,
        related_entities=related_entities_response,
        next_cursor=result.next_cursor,
        has_more=result.has_more,
    )


@router.post(
    "",
    response_model=QueryResultResponse,
    summary="Execute query",
    description="Execute a complex query with filters, sorting, pagination, traversal, and aggregation.",
)
async def execute_query(
    request: QueryRequest,
    engine: Engine,
    namespace_id: NamespaceIdDep,
) -> QueryResultResponse:
    """Execute a query against the entity database.

    Supports:
    - Filtering with nested AND/OR conditions
    - Sorting by multiple fields
    - Pagination with limit/offset
    - Relationship traversal
    - Aggregation (count, sum, avg, min, max, group_by)
    - Time-travel queries with at_time

    Args:
        request: The query request specification.
        engine: QueryEngine from dependency injection.

    Returns:
        Query results with matching entities and metadata.

    Raises:
        HTTPException: If entity type not found or invalid parameters.
    """
    # Convert request to domain Query
    try:
        domain_filter = _convert_filter(request.filter)
        domain_sort = _convert_sort(request.sort) if request.sort else None
        domain_traverse = _convert_traverse(request.traverse)
        domain_aggregate = _convert_aggregate(request.aggregate)
    except HTTPException:
        raise

    # Parse at_time string to datetime if provided
    at_time: datetime | None = None
    if request.at_time is not None:
        try:
            # Handle ISO 8601 format with optional Z suffix
            at_time_str = request.at_time.replace("Z", "+00:00")
            at_time = datetime.fromisoformat(at_time_str)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid at_time format: {e}. Use ISO 8601 format (e.g., 2026-02-05T10:30:00Z).",
            ) from e

    query = Query(
        entity_type=request.entity_type,
        filter=domain_filter,
        sort=domain_sort,
        limit=request.limit,
        offset=request.offset,
        traverse=domain_traverse,
        aggregate=domain_aggregate,
        at_time=at_time,
        cursor=request.cursor,
    )

    # Execute query
    try:
        result = await engine.execute(query)
    except ValueError as e:
        # Entity type not found - return empty result instead of error
        if "not found" in str(e):
            return QueryResultResponse(
                items=[],
                total=0,
                limit=request.limit,
                offset=request.offset,
                aggregations=None,
                related_entities=None,
            )
        raise HTTPException(status_code=400, detail=str(e)) from e

    return _convert_result(result)
