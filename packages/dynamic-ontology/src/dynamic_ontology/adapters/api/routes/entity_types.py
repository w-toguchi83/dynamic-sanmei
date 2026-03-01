"""EntityType CRUD API routes."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.adapters.api.dependencies import (
    UnitOfWorkDep,
    get_db_session,
    get_entity_type_repository,
    get_namespace_id,
    get_schema_version_repository,
)
from dynamic_ontology.adapters.api.models import (
    EntityTypeCreate,
    EntityTypeResponse,
    EntityTypeUpdate,
)
from dynamic_ontology.adapters.api.schema_helpers import (
    check_schema_compatibility,
    record_schema_version,
    serialize_properties_to_schema_def,
    to_domain_property_definition,
    to_entity_type_response,
)
from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.entity_type import EntityType
from dynamic_ontology.domain.models.schema_version import TypeKind
from dynamic_ontology.domain.ports.repository import EntityTypeRepository
from dynamic_ontology.domain.ports.schema_version_repository import SchemaVersionRepository

router = APIRouter(prefix="/schema/entity-types", tags=["Schema - Entity Types"])

# Dependency injection type aliases
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
Repo = Annotated[EntityTypeRepository, Depends(get_entity_type_repository)]
SchemaVersionRepo = Annotated[SchemaVersionRepository, Depends(get_schema_version_repository)]
NamespaceIdDep = Annotated[str, Depends(get_namespace_id)]


@router.post(
    "",
    response_model=EntityTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create entity type",
    description="Create a new entity type schema definition.",
)
async def create_entity_type(
    data: EntityTypeCreate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    repo: Repo,
    schema_version_repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
) -> EntityTypeResponse:
    """Create a new entity type.

    Args:
        data: The entity type creation data.
        repo: Entity type repository from dependency injection.

    Returns:
        The created entity type.
    """
    now = datetime.now(UTC)
    properties = {
        name: to_domain_property_definition(prop) for name, prop in data.properties.items()
    }

    entity_type = EntityType(
        id=uuid4(),
        name=data.name,
        description=data.description,
        properties=properties,
        custom_validators=data.custom_validators,
        created_at=now,
        updated_at=now,
        display_property=data.display_property,
    )

    created = await repo.create(entity_type)

    # 初期スキーマバージョン（v1）を記録
    initial_schema_def = serialize_properties_to_schema_def(properties)
    await record_schema_version(
        schema_version_repo=schema_version_repo,
        type_kind=TypeKind.ENTITY_TYPE,
        type_id=created.id,
        new_schema_def=initial_schema_def,
        namespace_id=namespace_id,
        created_by=None,
    )

    await uow.commit()

    return to_entity_type_response(created)


@router.get(
    "",
    response_model=list[EntityTypeResponse],
    summary="List entity types",
    description="Get all entity type schema definitions.",
)
async def list_entity_types(
    repo: Repo,
    namespace_id: NamespaceIdDep,
) -> list[EntityTypeResponse]:
    """List all entity types.

    Args:
        repo: Entity type repository from dependency injection.

    Returns:
        List of all entity types.
    """
    entity_types = await repo.list_all()

    return [to_entity_type_response(et) for et in entity_types]


@router.get(
    "/{entity_type_id}",
    response_model=EntityTypeResponse,
    summary="Get entity type by ID",
    description="Get a specific entity type schema definition by ID.",
)
async def get_entity_type(
    entity_type_id: UUID,
    repo: Repo,
    namespace_id: NamespaceIdDep,
) -> EntityTypeResponse:
    """Get entity type by ID.

    Args:
        entity_type_id: The entity type UUID.
        repo: Entity type repository from dependency injection.

    Returns:
        The entity type if found.

    Raises:
        EntityNotFoundError: If entity type not found.
    """
    entity_type = await repo.get_by_id(str(entity_type_id))

    if entity_type is None:
        raise EntityNotFoundError(str(entity_type_id), "EntityType")

    return to_entity_type_response(entity_type)


@router.put(
    "/{entity_type_id}",
    response_model=EntityTypeResponse,
    summary="Update entity type",
    description="Update an existing entity type schema definition.",
)
async def update_entity_type(
    entity_type_id: UUID,
    data: EntityTypeUpdate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    repo: Repo,
    schema_version_repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
    force: bool = Query(default=False, description="破壊的変更を強制実行する"),
) -> EntityTypeResponse:
    """Update entity type by ID.

    Args:
        entity_type_id: The entity type UUID.
        data: The update data.
        repo: Entity type repository from dependency injection.

    Returns:
        The updated entity type.

    Raises:
        EntityNotFoundError: If entity type not found.
    """
    existing = await repo.get_by_id(str(entity_type_id))

    if existing is None:
        raise EntityNotFoundError(str(entity_type_id), "EntityType")

    # Apply partial updates
    name = data.name if data.name is not None else existing.name
    description = data.description if data.description is not None else existing.description
    custom_validators = (
        data.custom_validators if data.custom_validators is not None else existing.custom_validators
    )

    if data.properties is not None:
        properties = {
            prop_name: to_domain_property_definition(prop)
            for prop_name, prop in data.properties.items()
        }
    else:
        properties = existing.properties

    # display_property は明示的に None を送れるので、
    # リクエストに含まれているかで判定する
    display_property = (
        data.display_property if data.display_property is not None else existing.display_property
    )
    updated_entity_type = EntityType(
        id=existing.id,
        name=name,
        description=description,
        properties=properties,
        custom_validators=custom_validators,
        created_at=existing.created_at,
        updated_at=datetime.now(UTC),
        display_property=display_property,
    )

    # スキーマ互換性チェック（破壊的変更の検出）
    old_schema_def = serialize_properties_to_schema_def(existing.properties)
    new_schema_def = serialize_properties_to_schema_def(properties)
    check_schema_compatibility(old_schema_def, new_schema_def, force=force)

    # スキーマバージョンを自動記録（更新前にスナップショット）
    await record_schema_version(
        schema_version_repo=schema_version_repo,
        type_kind=TypeKind.ENTITY_TYPE,
        type_id=entity_type_id,
        new_schema_def=new_schema_def,
        namespace_id=namespace_id,
        created_by=None,
    )

    updated = await repo.update(updated_entity_type)
    await uow.commit()

    return to_entity_type_response(updated)


@router.delete(
    "/{entity_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete entity type",
    description="Delete an entity type schema definition.",
)
async def delete_entity_type(
    entity_type_id: UUID,
    _session: DbSession,
    uow: UnitOfWorkDep,
    repo: Repo,
    namespace_id: NamespaceIdDep,
) -> Response:
    """Delete entity type by ID.

    Args:
        entity_type_id: The entity type UUID.
        repo: Entity type repository from dependency injection.

    Returns:
        204 No Content on success.

    Raises:
        EntityNotFoundError: If entity type not found.
    """
    existing = await repo.get_by_id(str(entity_type_id))
    if existing is None:
        raise EntityNotFoundError(str(entity_type_id), "EntityType")

    deleted = await repo.delete(str(entity_type_id))

    if not deleted:
        raise EntityNotFoundError(str(entity_type_id), "EntityType")

    await uow.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
