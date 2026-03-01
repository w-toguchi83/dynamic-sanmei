"""Entity CRUD API routes."""

from datetime import UTC, datetime
from typing import Annotated, Any
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
    get_validation_engine,
)
from dynamic_ontology.adapters.api.models import (
    BatchEntityCreate,
    BatchEntityDelete,
    BatchEntityUpdateRequest,
    BatchItemErrorResponse,
    BatchResultResponse,
    EntityCreate,
    EntityDiffResponse,
    EntityListResponse,
    EntityResponse,
    EntityRollbackRequest,
    EntitySnapshotResponse,
    EntityUpdate,
    ErrorResponse,
    PropertyChangeResponse,
)
from dynamic_ontology.application.use_cases.batch_create_entities import (
    BatchCreateEntitiesUseCase,
    BatchCreateItem,
)
from dynamic_ontology.application.use_cases.batch_delete_entities import BatchDeleteEntitiesUseCase
from dynamic_ontology.application.use_cases.batch_update_entities import (
    BatchUpdateEntitiesUseCase,
    BatchUpdateItem,
)
from dynamic_ontology.application.use_cases.create_entity import CreateEntityUseCase
from dynamic_ontology.application.use_cases.delete_entity import DeleteEntityUseCase
from dynamic_ontology.application.use_cases.update_entity import UpdateEntityUseCase
from dynamic_ontology.domain.exceptions import BatchOperationError, EntityNotFoundError
from dynamic_ontology.domain.models.batch import BatchResult
from dynamic_ontology.domain.models.entity import Entity
from dynamic_ontology.domain.ports.repository import EntityRepository, EntityTypeRepository
from dynamic_ontology.domain.services.rollback import RollbackService
from dynamic_ontology.domain.services.time_travel import TimeTravelService
from dynamic_ontology.domain.services.validation import ValidationEngine

router = APIRouter(prefix="/entities", tags=["Entities"])

# Dependency injection type aliases
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
ValidationEngineDep = Annotated[ValidationEngine, Depends(get_validation_engine)]
EntityRepoDep = Annotated[EntityRepository, Depends(get_entity_repository)]
EntityTypeRepoDep = Annotated[EntityTypeRepository, Depends(get_entity_type_repository)]
NamespaceIdDep = Annotated[str, Depends(get_namespace_id)]

# Query parameter type aliases
TypeIdQuery = Annotated[UUID, Query(description="Filter by entity type ID")]
LimitQuery = Annotated[int, Query(ge=1, le=1000, description="Maximum number of items")]
OffsetQuery = Annotated[int, Query(ge=0, description="Number of items to skip")]
AtTimeQuery = Annotated[str | None, Query(description="ISO timestamp for time-travel query")]
CursorQuery = Annotated[str | None, Query(description="Cursor for pagination")]


def _to_response(entity: Entity, type_name: str | None = None) -> EntityResponse:
    """Convert domain Entity to API response model.

    Args:
        entity: The domain Entity instance.
        type_name: Optional name of the entity type.

    Returns:
        API EntityResponse instance.
    """
    return EntityResponse(
        id=entity.id,
        type_id=entity.type_id,
        type_name=type_name,
        version=entity.version,
        properties=entity.properties,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        changed_by=entity.changed_by,
    )


@router.post(
    "",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create entity",
    description="Create a new entity instance with validation against its type schema.",
)
async def create_entity(
    data: EntityCreate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    validation_engine: ValidationEngineDep,
    entity_type_repo: EntityTypeRepoDep,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> EntityResponse:
    """エンティティを作成する."""
    uc = CreateEntityUseCase(
        entity_type_repo=entity_type_repo,
        entity_repo=entity_repo,
        validation_engine=validation_engine,
        uow=uow,
    )
    result = await uc.execute(
        type_id=data.type_id,
        properties=data.properties,
        principal_id=None,
    )

    await uow.commit()

    return _to_response(result.entity, type_name=result.entity_type_name)


@router.get(
    "",
    response_model=EntityListResponse,
    summary="List entities by type",
    description="Get all entities of a specific type with pagination.",
)
async def list_entities(
    _session: DbSession,
    type_id: TypeIdQuery,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
    limit: LimitQuery = 100,
    offset: OffsetQuery = 0,
    cursor: CursorQuery = None,
) -> EntityListResponse:
    """List entities by type with cursor or offset pagination.

    Args:
        type_id: The entity type UUID to filter by (required).
        limit: Maximum number of entities to return.
        offset: Number of entities to skip.
        cursor: Cursor for cursor-based pagination.

    Returns:
        List of entities with pagination info.
    """
    from dynamic_ontology.domain.services.cursor import CursorValidationError, encode_cursor

    try:
        entities, total = await entity_repo.list_by_type(str(type_id), limit=limit, offset=offset, cursor=cursor)
    except CursorValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    next_cursor: str | None = None
    has_more = False
    if entities:
        has_more = len(entities) == limit if cursor is not None else (offset + len(entities)) < total
        if has_more:
            last = entities[-1]
            next_cursor = encode_cursor(last.created_at, last.id)

    return EntityListResponse(
        items=[_to_response(e) for e in entities],
        total=total,
        limit=limit,
        offset=offset,
        next_cursor=next_cursor,
        has_more=has_more,
    )


# =============================================================================
# Batch Operations - MUST be defined before /{entity_id} routes
# =============================================================================


def _batch_result_to_response(result: BatchResult) -> BatchResultResponse:
    """Convert domain BatchResult to API response.

    Args:
        result: The domain BatchResult instance.

    Returns:
        API BatchResultResponse instance.
    """
    return BatchResultResponse(
        success=result.success,
        total=result.total,
        succeeded=result.succeeded,
        failed=result.failed,
        entity_ids=result.entity_ids,
        errors=[
            BatchItemErrorResponse(
                index=e.index,
                entity_id=e.entity_id,
                message=e.message,
            )
            for e in result.errors
        ],
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
    "/batch",
    response_model=BatchResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch create entities",
    description="Create multiple entities in a single transaction. All-or-nothing semantics.",
    responses={
        400: {"model": ErrorResponse, "description": "Batch operation failed"},
    },
)
async def batch_create_entities(
    data: BatchEntityCreate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    validation_engine: ValidationEngineDep,
    entity_type_repo: EntityTypeRepoDep,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> BatchResultResponse:
    """エンティティを一括作成する."""
    uc = BatchCreateEntitiesUseCase(
        entity_type_repo=entity_type_repo,
        entity_repo=entity_repo,
        validation_engine=validation_engine,
        uow=uow,
    )

    try:
        result = await uc.execute(
            items=[BatchCreateItem(type_id=e.type_id, properties=e.properties) for e in data.entities],
            principal_id=None,
        )
    except BatchOperationError as e:
        raise _batch_error_to_http_exception(e, total=len(data.entities)) from e

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_batch_result_to_response(result).model_dump(mode="json"),
        )

    await uow.commit()

    return _batch_result_to_response(result)


@router.patch(
    "/batch",
    response_model=BatchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch update entities",
    description="Update multiple entities in a single transaction. All-or-nothing semantics.",
    responses={
        400: {"model": ErrorResponse, "description": "Batch operation failed"},
    },
)
async def batch_update_entities(
    data: BatchEntityUpdateRequest,
    _session: DbSession,
    uow: UnitOfWorkDep,
    validation_engine: ValidationEngineDep,
    entity_type_repo: EntityTypeRepoDep,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> BatchResultResponse:
    """エンティティを一括更新する."""
    uc = BatchUpdateEntitiesUseCase(
        entity_type_repo=entity_type_repo,
        entity_repo=entity_repo,
        validation_engine=validation_engine,
        uow=uow,
    )

    try:
        result = await uc.execute(
            items=[BatchUpdateItem(id=u.id, properties=u.properties, version=u.version) for u in data.updates],
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
    "/batch",
    response_model=BatchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch delete entities",
    description="Delete multiple entities in a single transaction. All-or-nothing semantics.",
    responses={
        400: {"model": ErrorResponse, "description": "Batch operation failed"},
    },
)
async def batch_delete_entities(
    data: BatchEntityDelete,
    _session: DbSession,
    uow: UnitOfWorkDep,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> BatchResultResponse:
    """エンティティを一括削除する."""
    uc = BatchDeleteEntitiesUseCase(entity_repo=entity_repo, uow=uow)
    result = await uc.execute(entity_ids=data.entity_ids)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_batch_result_to_response(result).model_dump(mode="json"),
        )

    await uow.commit()

    return _batch_result_to_response(result)


# =============================================================================
# Single Entity Operations with /{entity_id} path parameter
# =============================================================================


@router.get(
    "/{entity_id}",
    response_model=EntityResponse,
    summary="Get entity by ID",
    description="Get a specific entity by ID, optionally at a point in time.",
)
async def get_entity(
    entity_id: UUID,
    _session: DbSession,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
    at_time: AtTimeQuery = None,
) -> EntityResponse:
    """Get entity by ID.

    Args:
        entity_id: The entity UUID.
        at_time: Optional ISO timestamp for time-travel query.

    Returns:
        The entity if found.

    Raises:
        EntityNotFoundError: If entity not found.
    """
    entity = await entity_repo.get_by_id(str(entity_id), at_time=at_time)

    if entity is None:
        raise EntityNotFoundError(str(entity_id), "Entity")

    return _to_response(entity)


@router.put(
    "/{entity_id}",
    response_model=EntityResponse,
    summary="Update entity",
    description="Update an existing entity with optimistic locking.",
)
async def update_entity(
    entity_id: UUID,
    data: EntityUpdate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    validation_engine: ValidationEngineDep,
    entity_type_repo: EntityTypeRepoDep,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> EntityResponse:
    """エンティティを更新する."""
    uc = UpdateEntityUseCase(
        entity_type_repo=entity_type_repo,
        entity_repo=entity_repo,
        validation_engine=validation_engine,
        uow=uow,
    )
    result = await uc.execute(
        entity_id=entity_id,
        properties=data.properties,
        current_version=data.version,
        principal_id=None,
    )

    await uow.commit()

    return _to_response(result.entity, type_name=result.entity_type_name)


@router.delete(
    "/{entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete entity",
    description="Delete an entity by ID.",
)
async def delete_entity(
    entity_id: UUID,
    _session: DbSession,
    uow: UnitOfWorkDep,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> Response:
    """エンティティを削除する."""
    uc = DeleteEntityUseCase(entity_repo=entity_repo, uow=uow)
    await uc.execute(entity_id=entity_id)

    await uow.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{entity_id}/history",
    response_model=list[dict[str, Any]],
    summary="Get entity history",
    description="Get version history for an entity.",
)
async def get_entity_history(
    entity_id: UUID,
    _session: DbSession,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> list[dict[str, Any]]:
    """Get version history for an entity.

    Args:
        entity_id: The entity UUID.

    Returns:
        List of history records.

    Raises:
        EntityNotFoundError: If entity not found.
    """
    # Check if entity exists
    entity = await entity_repo.get_by_id(str(entity_id))
    if entity is None:
        raise EntityNotFoundError(str(entity_id), "Entity")

    history = await entity_repo.get_history(str(entity_id))
    return history


# Query parameter type aliases for time travel
FromVersionQuery = Annotated[int, Query(ge=1, description="比較元バージョン")]
ToVersionQuery = Annotated[int, Query(ge=1, description="比較先バージョン")]


@router.get(
    "/{entity_id}/at/{timestamp}",
    response_model=EntitySnapshotResponse,
    summary="Get entity snapshot at timestamp",
    description="指定時刻に有効なエンティティのスナップショットを取得.",
)
async def get_entity_at_timestamp(
    entity_id: UUID,
    timestamp: str,
    _session: DbSession,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> EntitySnapshotResponse:
    """指定時刻に有効なエンティティのスナップショットを取得.

    Args:
        entity_id: エンティティの UUID.
        timestamp: ISO8601 形式のタイムスタンプ文字列.

    Returns:
        指定時刻に有効な EntitySnapshotResponse.

    Raises:
        EntityNotFoundError: スナップショットが見つからない場合.
    """
    # Parse ISO8601 timestamp
    at_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    snapshot = await entity_repo.get_snapshot_at_time(str(entity_id), at_time)

    if snapshot is None:
        raise EntityNotFoundError(str(entity_id), "Entity snapshot")

    return EntitySnapshotResponse(
        entity_id=snapshot.entity_id,
        type_id=snapshot.type_id,
        version=snapshot.version,
        properties=snapshot.properties,
        valid_from=snapshot.valid_from,
        valid_to=snapshot.valid_to,
        operation=snapshot.operation,
        is_current=snapshot.is_current,
    )


@router.get(
    "/{entity_id}/diff",
    response_model=EntityDiffResponse,
    summary="Get entity diff between versions",
    description="2つのバージョン間のエンティティ差分を取得.",
)
async def get_entity_diff(
    entity_id: UUID,
    from_version: FromVersionQuery,
    to_version: ToVersionQuery,
    _session: DbSession,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> EntityDiffResponse:
    """2つのバージョン間のエンティティ差分を取得.

    Args:
        entity_id: エンティティの UUID.
        from_version: 比較元バージョン番号.
        to_version: 比較先バージョン番号.

    Returns:
        EntityDiffResponse: 差分情報.

    Raises:
        EntityNotFoundError: スナップショットが見つからない場合.
    """
    # Get both snapshots
    from_snapshot = await entity_repo.get_snapshot_by_version(str(entity_id), from_version)
    if from_snapshot is None:
        raise EntityNotFoundError(str(entity_id), f"Entity snapshot (version {from_version})")

    to_snapshot = await entity_repo.get_snapshot_by_version(str(entity_id), to_version)
    if to_snapshot is None:
        raise EntityNotFoundError(str(entity_id), f"Entity snapshot (version {to_version})")

    # Compute diff using TimeTravelService
    diff = TimeTravelService.compute_diff(from_snapshot, to_snapshot)

    # Convert PropertyChange to PropertyChangeResponse
    changes = [
        PropertyChangeResponse(
            field=change.field,
            old_value=change.old_value,
            new_value=change.new_value,
            change_type=change.change_type,
        )
        for change in diff.changes
    ]

    return EntityDiffResponse(
        entity_id=diff.entity_id,
        from_version=diff.from_version,
        to_version=diff.to_version,
        from_time=diff.from_time,
        to_time=diff.to_time,
        changes=changes,
        has_changes=diff.has_changes,
    )


@router.post(
    "/{entity_id}/rollback",
    response_model=EntityResponse,
    summary="Rollback entity to previous version",
    description="エンティティを過去のバージョンまたは時点にロールバックする。履歴は保持され、新しいバージョンとして保存される。",
)
async def rollback_entity(
    entity_id: UUID,
    data: EntityRollbackRequest,
    _session: DbSession,
    uow: UnitOfWorkDep,
    validation_engine: ValidationEngineDep,
    entity_type_repo: EntityTypeRepoDep,
    entity_repo: EntityRepoDep,
    namespace_id: NamespaceIdDep,
) -> EntityResponse:
    """エンティティを過去のバージョンまたは時点にロールバック.

    ロールバックは新しいバージョンとして保存され、履歴は保持される。

    Args:
        entity_id: エンティティの UUID.
        data: ロールバックリクエスト（target_version または target_time を指定）.

    Returns:
        ロールバック後の EntityResponse.

    Raises:
        EntityNotFoundError: エンティティまたはスナップショットが見つからない場合.
        InvalidRollbackError: ロールバックが無効な場合.
        ValidationError: プロパティの検証に失敗した場合.
    """
    # 1. 現在のエンティティを取得
    current_entity = await entity_repo.get_by_id(str(entity_id))
    if current_entity is None:
        raise EntityNotFoundError(str(entity_id), "Entity")

    # 2. ターゲットスナップショットを取得
    target_snapshot = None
    if data.target_version is not None:
        target_snapshot = await entity_repo.get_snapshot_by_version(str(entity_id), data.target_version)
        if target_snapshot is None:
            raise EntityNotFoundError(str(entity_id), f"Entity snapshot (version {data.target_version})")
    elif data.target_time is not None:
        # ISO8601 タイムスタンプをパース
        try:
            at_time = datetime.fromisoformat(data.target_time.replace("Z", "+00:00"))
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timestamp format: {data.target_time}. Expected ISO8601 format.",
            ) from e

        target_snapshot = await entity_repo.get_snapshot_at_time(str(entity_id), at_time)
        if target_snapshot is None:
            raise EntityNotFoundError(str(entity_id), f"Entity snapshot at time {data.target_time}")

    # このポイントで target_snapshot は必ず None ではない（Pydantic バリデーションにより）
    assert target_snapshot is not None

    # 3. RollbackService で検証
    RollbackService.validate_rollback(current_entity, target_snapshot)

    # 4. EntityType を取得して ValidationEngine でプロパティ検証
    entity_type = await entity_type_repo.get_by_id(str(current_entity.type_id))
    if entity_type is None:
        raise EntityNotFoundError(str(current_entity.type_id), "EntityType")

    # スナップショットのプロパティを検証
    validated_properties = validation_engine.validate_and_apply_defaults(
        target_snapshot.properties,
        entity_type,
        existing_properties=current_entity.properties,
    )

    # 5. RollbackService でロールバック用 Entity を準備
    rollback_entity_obj = Entity(
        id=current_entity.id,
        type_id=current_entity.type_id,
        version=current_entity.version,
        properties=validated_properties,
        created_at=current_entity.created_at,
        updated_at=datetime.now(UTC),
    )

    # 6. repo.update() で更新（新バージョンとして保存）
    updated = await entity_repo.update(rollback_entity_obj, current_version=current_entity.version)
    await uow.commit()

    return _to_response(updated, type_name=entity_type.name)
