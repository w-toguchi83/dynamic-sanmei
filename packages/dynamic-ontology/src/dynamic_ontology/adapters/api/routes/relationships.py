"""Relationship CRUD API routes."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.adapters.api.dependencies import (
    UnitOfWorkDep,
    get_db_session,
    get_entity_repository,
    get_entity_type_repository,
    get_namespace_id,
    get_relationship_repository,
    get_relationship_type_repository,
)
from dynamic_ontology.adapters.api.models import (
    BatchItemErrorResponse,
    BatchRelationshipCreate,
    BatchRelationshipDelete,
    BatchRelationshipUpdateRequest,
    BatchResultResponse,
    ErrorResponse,
    RelationshipCreate,
    RelationshipListResponse,
    RelationshipResponse,
    RelationshipUpdate,
)
from dynamic_ontology.application.use_cases.batch_create_relationships import (
    BatchCreateRelationshipItem,
    BatchCreateRelationshipsUseCase,
)
from dynamic_ontology.application.use_cases.batch_delete_relationships import (
    BatchDeleteRelationshipsUseCase,
)
from dynamic_ontology.application.use_cases.batch_update_relationships import (
    BatchUpdateRelationshipItem,
    BatchUpdateRelationshipsUseCase,
)
from dynamic_ontology.application.use_cases.create_relationship import CreateRelationshipUseCase
from dynamic_ontology.application.use_cases.delete_relationship import DeleteRelationshipUseCase
from dynamic_ontology.application.use_cases.update_relationship import UpdateRelationshipUseCase
from dynamic_ontology.domain.exceptions import BatchOperationError, EntityNotFoundError
from dynamic_ontology.domain.models.batch import BatchResult
from dynamic_ontology.domain.models.relationship import Relationship
from dynamic_ontology.domain.ports.repository import (
    EntityRepository,
    EntityTypeRepository,
    RelationshipRepository,
    RelationshipTypeRepository,
)

router = APIRouter(tags=["Relationships"])

# Dependency injection type aliases
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
EntityRepoDep = Annotated[EntityRepository, Depends(get_entity_repository)]
EntityTypeRepoDep = Annotated[EntityTypeRepository, Depends(get_entity_type_repository)]
RelationshipRepoDep = Annotated[RelationshipRepository, Depends(get_relationship_repository)]
RelationshipTypeRepoDep = Annotated[RelationshipTypeRepository, Depends(get_relationship_type_repository)]
NamespaceIdDep = Annotated[str, Depends(get_namespace_id)]

# Query parameter type aliases
DirectionQuery = Annotated[
    Literal["outgoing", "incoming", "both"],
    Query(description="Direction filter: outgoing, incoming, or both"),
]
TypeIdFilterQuery = Annotated[
    UUID | None,
    Query(description="Filter by relationship type ID"),
]
LimitQuery = Annotated[int, Query(ge=1, le=1000, description="Maximum number of items")]
OffsetQuery = Annotated[int, Query(ge=0, description="Number of items to skip")]
CursorQuery = Annotated[str | None, Query(description="Cursor for pagination")]


def _to_response(
    relationship: Relationship,
    *,
    type_name: str | None = None,
    from_entity_display_name: str | None = None,
    to_entity_display_name: str | None = None,
    from_entity_type_name: str | None = None,
    to_entity_type_name: str | None = None,
) -> RelationshipResponse:
    """Convert domain Relationship to API response model.

    Args:
        relationship: The domain Relationship instance.
        type_name: リレーションシップタイプ名.
        from_entity_display_name: ソースエンティティの表示名.
        to_entity_display_name: ターゲットエンティティの表示名.
        from_entity_type_name: ソースエンティティのタイプ名.
        to_entity_type_name: ターゲットエンティティのタイプ名.

    Returns:
        API RelationshipResponse instance.
    """
    return RelationshipResponse(
        id=relationship.id,
        type_id=relationship.type_id,
        from_entity_id=relationship.from_entity_id,
        to_entity_id=relationship.to_entity_id,
        version=relationship.version,
        properties=relationship.properties,
        created_at=relationship.created_at,
        updated_at=relationship.updated_at,
        changed_by=relationship.changed_by,
        type_name=type_name,
        from_entity_display_name=from_entity_display_name,
        to_entity_display_name=to_entity_display_name,
        from_entity_type_name=from_entity_type_name,
        to_entity_type_name=to_entity_type_name,
    )


async def _resolve_display_info(
    entity_id: UUID,
    entity_repo: EntityRepository,
    entity_type_repo: EntityTypeRepository,
    *,
    et_cache: dict[UUID, tuple[str, str | None]] | None = None,
) -> tuple[str | None, str | None]:
    """エンティティの表示名とタイプ名を解決する.

    Args:
        entity_id: エンティティID.
        entity_repo: エンティティリポジトリ.
        entity_type_repo: エンティティタイプリポジトリ.
        et_cache: EntityType の (name, display_property) キャッシュ（type_id -> tuple）.

    Returns:
        (display_name, type_name) のタプル.
    """
    entity = await entity_repo.get_by_id(str(entity_id))
    if entity is None:
        return None, None

    # キャッシュからタイプ情報を取得、なければ DB から取得してキャッシュに保存
    if et_cache is not None and entity.type_id in et_cache:
        type_name, display_prop = et_cache[entity.type_id]
    else:
        et = await entity_type_repo.get_by_id(str(entity.type_id))
        if et is None:
            return None, None
        type_name = et.name
        display_prop = et.display_property
        if et_cache is not None:
            et_cache[entity.type_id] = (type_name, display_prop)

    display_name: str | None = None
    if display_prop and display_prop in entity.properties:
        val = entity.properties[display_prop]
        if val is not None:
            display_name = str(val)

    return display_name, type_name


def _batch_result_to_response(result: BatchResult) -> BatchResultResponse:
    """Convert domain BatchResult to API response."""
    return BatchResultResponse(
        success=result.success,
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
        entity_ids=result.entity_ids,
        errors=[BatchItemErrorResponse(index=e.index, entity_id=e.entity_id, message=e.message) for e in result.errors],
    )


def _batch_error_to_http_exception(
    error: BatchOperationError,
    total: int,
) -> HTTPException:
    """BatchOperationError を HTTPException に変換する."""
    failed_item_count = len({e.index for e in error.errors})
    result = BatchResult(
        success=False,
        total=total,
        succeeded=0,
        failed=failed_item_count,
        entity_ids=[],
        errors=error.errors,
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=_batch_result_to_response(result).model_dump(mode="json"),
    )


@router.post(
    "/relationships/batch",
    response_model=BatchResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch create relationships",
    description="Create multiple relationships in a single transaction. All-or-nothing semantics.",
    responses={
        400: {"model": ErrorResponse, "description": "Batch operation failed"},
    },
)
async def batch_create_relationships(
    data: BatchRelationshipCreate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    relationship_type_repo: RelationshipTypeRepoDep,
    entity_repo: EntityRepoDep,
    relationship_repo: RelationshipRepoDep,
    namespace_id: NamespaceIdDep,
) -> BatchResultResponse:
    """リレーションシップを一括作成する."""
    uc = BatchCreateRelationshipsUseCase(
        relationship_type_repo=relationship_type_repo,
        entity_repo=entity_repo,
        relationship_repo=relationship_repo,
        uow=uow,
    )

    try:
        result = await uc.execute(
            items=[
                BatchCreateRelationshipItem(
                    type_id=r.type_id,
                    from_entity_id=r.from_entity_id,
                    to_entity_id=r.to_entity_id,
                    properties=r.properties,
                )
                for r in data.relationships
            ],
            principal_id=None,
        )
    except BatchOperationError as e:
        raise _batch_error_to_http_exception(e, total=len(data.relationships)) from e

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_batch_result_to_response(result).model_dump(mode="json"),
        )

    await uow.commit()

    return _batch_result_to_response(result)


@router.patch(
    "/relationships/batch",
    response_model=BatchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch update relationships",
    description="Update multiple relationships in a single transaction. All-or-nothing semantics.",
    responses={
        400: {"model": ErrorResponse, "description": "Batch operation failed"},
    },
)
async def batch_update_relationships(
    data: BatchRelationshipUpdateRequest,
    _session: DbSession,
    uow: UnitOfWorkDep,
    relationship_repo: RelationshipRepoDep,
    namespace_id: NamespaceIdDep,
) -> BatchResultResponse:
    """リレーションシップを一括更新する."""
    uc = BatchUpdateRelationshipsUseCase(
        relationship_repo=relationship_repo,
        uow=uow,
    )

    try:
        result = await uc.execute(
            items=[
                BatchUpdateRelationshipItem(
                    id=u.id,
                    properties=u.properties,
                    version=u.version,
                )
                for u in data.updates
            ],
            principal_id=None,
        )
    except BatchOperationError as e:
        raise _batch_error_to_http_exception(e, total=len(data.updates)) from e

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_batch_result_to_response(result).model_dump(mode="json"),
        )

    await uow.commit()

    return _batch_result_to_response(result)


@router.delete(
    "/relationships/batch",
    response_model=BatchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch delete relationships",
    description="Delete multiple relationships in a single transaction. All-or-nothing semantics.",
    responses={
        400: {"model": ErrorResponse, "description": "Batch operation failed"},
    },
)
async def batch_delete_relationships(
    data: BatchRelationshipDelete,
    _session: DbSession,
    uow: UnitOfWorkDep,
    relationship_repo: RelationshipRepoDep,
    namespace_id: NamespaceIdDep,
) -> BatchResultResponse:
    """リレーションシップを一括削除する."""
    uc = BatchDeleteRelationshipsUseCase(relationship_repo=relationship_repo, uow=uow)
    result = await uc.execute(relationship_ids=data.relationship_ids)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_batch_result_to_response(result).model_dump(mode="json"),
        )

    await uow.commit()

    return _batch_result_to_response(result)


@router.get(
    "/relationships",
    response_model=RelationshipListResponse,
    summary="List relationships",
    description="List relationships with optional type filter and pagination.",
)
async def list_relationships(
    _session: DbSession,
    entity_repo: EntityRepoDep,
    entity_type_repo: EntityTypeRepoDep,
    relationship_repo: RelationshipRepoDep,
    relationship_type_repo: RelationshipTypeRepoDep,
    namespace_id: NamespaceIdDep,
    type_id: TypeIdFilterQuery = None,
    limit: LimitQuery = 100,
    offset: OffsetQuery = 0,
    cursor: CursorQuery = None,
) -> RelationshipListResponse:
    """リレーションシップを一覧取得する.

    Args:
        type_id: リレーションシップタイプ ID でフィルタ（任意）.
        limit: 最大取得件数.
        offset: スキップ件数.
        cursor: カーソルベースページネーション用カーソル.

    Returns:
        ページネーション情報付きリレーションシップ一覧.
    """
    from dynamic_ontology.domain.services.cursor import CursorValidationError, encode_cursor

    type_id_str = str(type_id) if type_id else None

    try:
        relationships, total = await relationship_repo.list_all(
            type_id=type_id_str,
            limit=limit,
            offset=offset,
            cursor=cursor,
        )
    except CursorValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    next_cursor: str | None = None
    has_more = False
    if relationships:
        if cursor is not None:
            has_more = len(relationships) == limit
        else:
            has_more = (offset + len(relationships)) < total
        if has_more:
            last = relationships[-1]
            next_cursor = encode_cursor(last.created_at, last.id)

    # 表示名を解決（キャッシュで EntityType / RelationshipType の重複取得を回避）
    et_cache: dict[UUID, tuple[str, str | None]] = {}
    rt_cache: dict[UUID, str] = {}
    enriched_items: list[RelationshipResponse] = []
    for r in relationships:
        # RelationshipType 名をキャッシュ付きで取得
        if r.type_id not in rt_cache:
            rt = await relationship_type_repo.get_by_id(str(r.type_id))
            rt_cache[r.type_id] = rt.name if rt else ""
        r_type_name = rt_cache[r.type_id] or None

        from_display, from_type_name = await _resolve_display_info(
            r.from_entity_id, entity_repo, entity_type_repo, et_cache=et_cache
        )
        to_display, to_type_name = await _resolve_display_info(
            r.to_entity_id, entity_repo, entity_type_repo, et_cache=et_cache
        )
        enriched_items.append(
            _to_response(
                r,
                type_name=r_type_name,
                from_entity_display_name=from_display,
                to_entity_display_name=to_display,
                from_entity_type_name=from_type_name,
                to_entity_type_name=to_type_name,
            )
        )

    return RelationshipListResponse(
        items=enriched_items,
        total=total,
        limit=limit,
        offset=offset,
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.post(
    "/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create relationship",
    description="Create a new relationship between two entities.",
)
async def create_relationship(
    data: RelationshipCreate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    relationship_type_repo: RelationshipTypeRepoDep,
    entity_repo: EntityRepoDep,
    entity_type_repo: EntityTypeRepoDep,
    relationship_repo: RelationshipRepoDep,
    namespace_id: NamespaceIdDep,
) -> RelationshipResponse:
    """リレーションシップを作成する."""
    uc = CreateRelationshipUseCase(
        relationship_type_repo=relationship_type_repo,
        relationship_repo=relationship_repo,
        entity_repo=entity_repo,
        uow=uow,
    )
    result = await uc.execute(
        type_id=data.type_id,
        from_entity_id=data.from_entity_id,
        to_entity_id=data.to_entity_id,
        properties=data.properties,
        principal_id=None,
    )
    created = result.relationship

    await uow.commit()

    et_cache: dict[UUID, tuple[str, str | None]] = {}
    from_display, from_type_name = await _resolve_display_info(
        created.from_entity_id,
        entity_repo,
        entity_type_repo,
        et_cache=et_cache,
    )
    to_display, to_type_name = await _resolve_display_info(
        created.to_entity_id,
        entity_repo,
        entity_type_repo,
        et_cache=et_cache,
    )

    return _to_response(
        created,
        type_name=result.type_name,
        from_entity_display_name=from_display,
        to_entity_display_name=to_display,
        from_entity_type_name=from_type_name,
        to_entity_type_name=to_type_name,
    )


@router.get(
    "/relationships/{relationship_id}",
    response_model=RelationshipResponse,
    summary="Get relationship by ID",
    description="Get a specific relationship by ID.",
)
async def get_relationship(
    relationship_id: UUID,
    _session: DbSession,
    relationship_repo: RelationshipRepoDep,
    relationship_type_repo: RelationshipTypeRepoDep,
    entity_repo: EntityRepoDep,
    entity_type_repo: EntityTypeRepoDep,
    namespace_id: NamespaceIdDep,
) -> RelationshipResponse:
    """Get relationship by ID.

    Args:
        relationship_id: The relationship UUID.

    Returns:
        The relationship if found.

    Raises:
        EntityNotFoundError: If relationship not found.
    """
    relationship = await relationship_repo.get_by_id(str(relationship_id))

    if relationship is None:
        raise EntityNotFoundError(str(relationship_id), "Relationship")

    # 表示名を解決
    rt = await relationship_type_repo.get_by_id(str(relationship.type_id))
    type_name = rt.name if rt else None

    et_cache: dict[UUID, tuple[str, str | None]] = {}
    from_display, from_type_name = await _resolve_display_info(
        relationship.from_entity_id, entity_repo, entity_type_repo, et_cache=et_cache
    )
    to_display, to_type_name = await _resolve_display_info(
        relationship.to_entity_id, entity_repo, entity_type_repo, et_cache=et_cache
    )

    return _to_response(
        relationship,
        type_name=type_name,
        from_entity_display_name=from_display,
        to_entity_display_name=to_display,
        from_entity_type_name=from_type_name,
        to_entity_type_name=to_type_name,
    )


@router.put(
    "/relationships/{relationship_id}",
    response_model=RelationshipResponse,
    summary="Update relationship",
    description="Update an existing relationship with optimistic locking.",
)
async def update_relationship(
    relationship_id: UUID,
    data: RelationshipUpdate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    relationship_repo: RelationshipRepoDep,
    relationship_type_repo: RelationshipTypeRepoDep,
    entity_repo: EntityRepoDep,
    entity_type_repo: EntityTypeRepoDep,
    namespace_id: NamespaceIdDep,
) -> RelationshipResponse:
    """リレーションシップを更新する."""
    uc = UpdateRelationshipUseCase(relationship_repo=relationship_repo, uow=uow)
    result = await uc.execute(
        relationship_id=relationship_id,
        properties=data.properties,
        current_version=data.version,
        principal_id=None,
    )
    updated = result.relationship

    await uow.commit()

    rt = await relationship_type_repo.get_by_id(str(updated.type_id))
    type_name = rt.name if rt else None

    et_cache: dict[UUID, tuple[str, str | None]] = {}
    from_display, from_type_name = await _resolve_display_info(
        updated.from_entity_id,
        entity_repo,
        entity_type_repo,
        et_cache=et_cache,
    )
    to_display, to_type_name = await _resolve_display_info(
        updated.to_entity_id,
        entity_repo,
        entity_type_repo,
        et_cache=et_cache,
    )

    return _to_response(
        updated,
        type_name=type_name,
        from_entity_display_name=from_display,
        to_entity_display_name=to_display,
        from_entity_type_name=from_type_name,
        to_entity_type_name=to_type_name,
    )


@router.delete(
    "/relationships/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete relationship",
    description="Delete a relationship by ID.",
)
async def delete_relationship(
    relationship_id: UUID,
    _session: DbSession,
    uow: UnitOfWorkDep,
    relationship_repo: RelationshipRepoDep,
    namespace_id: NamespaceIdDep,
) -> Response:
    """リレーションシップを削除する."""
    uc = DeleteRelationshipUseCase(relationship_repo=relationship_repo, uow=uow)
    await uc.execute(relationship_id=relationship_id)

    await uow.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/entities/{entity_id}/relationships",
    response_model=RelationshipListResponse,
    summary="Get entity relationships",
    description="Get all relationships for an entity with optional direction and type filters.",
)
async def get_entity_relationships(
    entity_id: UUID,
    _session: DbSession,
    entity_repo: EntityRepoDep,
    entity_type_repo: EntityTypeRepoDep,
    relationship_repo: RelationshipRepoDep,
    relationship_type_repo: RelationshipTypeRepoDep,
    namespace_id: NamespaceIdDep,
    direction: DirectionQuery = "both",
    type_id: TypeIdFilterQuery = None,
    limit: LimitQuery = 100,
    offset: OffsetQuery = 0,
    cursor: CursorQuery = None,
) -> RelationshipListResponse:
    """Get relationships for an entity with pagination.

    Args:
        entity_id: The entity UUID.
        direction: Direction filter (outgoing, incoming, or both).
        type_id: Optional relationship type ID filter.
        limit: Maximum number of relationships to return.
        offset: Number of relationships to skip.
        cursor: Cursor for cursor-based pagination.

    Returns:
        List of relationships for the entity with pagination info.

    Raises:
        EntityNotFoundError: If entity not found.
    """
    from dynamic_ontology.domain.services.cursor import CursorValidationError, encode_cursor

    # Verify entity exists
    entity = await entity_repo.get_by_id(str(entity_id))
    if entity is None:
        raise EntityNotFoundError(str(entity_id), "Entity")

    # Get relationships
    type_id_str = str(type_id) if type_id else None

    try:
        relationships, total = await relationship_repo.list_by_entity(
            entity_id=str(entity_id),
            relationship_type=type_id_str,
            direction=direction,
            limit=limit,
            offset=offset,
            cursor=cursor,
        )
    except CursorValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    next_cursor: str | None = None
    has_more = False
    if relationships:
        if cursor is not None:
            has_more = len(relationships) == limit
        else:
            has_more = (offset + len(relationships)) < total
        if has_more:
            last = relationships[-1]
            next_cursor = encode_cursor(last.created_at, last.id)

    # 表示名を解決（キャッシュで EntityType / RelationshipType の重複取得を回避）
    et_cache: dict[UUID, tuple[str, str | None]] = {}
    rt_cache: dict[UUID, str] = {}
    enriched_items: list[RelationshipResponse] = []
    for r in relationships:
        # RelationshipType 名をキャッシュ付きで取得
        if r.type_id not in rt_cache:
            rt = await relationship_type_repo.get_by_id(str(r.type_id))
            rt_cache[r.type_id] = rt.name if rt else ""
        r_type_name = rt_cache[r.type_id] or None

        from_display, from_type_name = await _resolve_display_info(
            r.from_entity_id, entity_repo, entity_type_repo, et_cache=et_cache
        )
        to_display, to_type_name = await _resolve_display_info(
            r.to_entity_id, entity_repo, entity_type_repo, et_cache=et_cache
        )
        enriched_items.append(
            _to_response(
                r,
                type_name=r_type_name,
                from_entity_display_name=from_display,
                to_entity_display_name=to_display,
                from_entity_type_name=from_type_name,
                to_entity_type_name=to_type_name,
            )
        )

    return RelationshipListResponse(
        items=enriched_items,
        total=total,
        limit=limit,
        offset=offset,
        next_cursor=next_cursor,
        has_more=has_more,
    )
