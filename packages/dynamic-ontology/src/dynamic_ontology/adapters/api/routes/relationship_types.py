"""RelationshipType CRUD API routes."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.adapters.api.dependencies import (
    UnitOfWorkDep,
    get_db_session,
    get_namespace_id,
    get_relationship_type_repository,
    get_schema_version_repository,
)
from dynamic_ontology.adapters.api.models import (
    RelationshipTypeCreate,
    RelationshipTypeResponse,
    RelationshipTypeUpdate,
)
from dynamic_ontology.adapters.api.schema_helpers import (
    check_schema_compatibility,
    record_schema_version,
    serialize_properties_to_schema_def,
    to_domain_property_definition,
    to_relationship_type_response,
)
from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.relationship import RelationshipType
from dynamic_ontology.domain.models.schema_version import TypeKind
from dynamic_ontology.domain.ports.repository import RelationshipTypeRepository
from dynamic_ontology.domain.ports.schema_version_repository import SchemaVersionRepository

router = APIRouter(prefix="/schema/relationship-types", tags=["Schema - Relationship Types"])

# Dependency injection type aliases
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
Repo = Annotated[RelationshipTypeRepository, Depends(get_relationship_type_repository)]
SchemaVersionRepo = Annotated[SchemaVersionRepository, Depends(get_schema_version_repository)]
NamespaceIdDep = Annotated[str, Depends(get_namespace_id)]


@router.post(
    "",
    response_model=RelationshipTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create relationship type",
    description="Create a new relationship type schema definition.",
)
async def create_relationship_type(
    data: RelationshipTypeCreate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    repo: Repo,
    schema_version_repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
) -> RelationshipTypeResponse:
    """Create a new relationship type.

    Args:
        data: The relationship type creation data.
        repo: Relationship type repository from dependency injection.

    Returns:
        The created relationship type.
    """
    now = datetime.now(UTC)
    properties = {name: to_domain_property_definition(prop) for name, prop in data.properties.items()}

    relationship_type = RelationshipType(
        id=uuid4(),
        name=data.name,
        description=data.description,
        directional=data.directional,
        properties=properties,
        custom_validators=data.custom_validators,
        created_at=now,
        updated_at=now,
        allowed_source_types=data.allowed_source_types,
        allowed_target_types=data.allowed_target_types,
        allow_duplicates=data.allow_duplicates,
    )

    created = await repo.create(relationship_type)

    # 初期スキーマバージョン（v1）を記録
    initial_schema_def = serialize_properties_to_schema_def(properties)
    await record_schema_version(
        schema_version_repo=schema_version_repo,
        type_kind=TypeKind.RELATIONSHIP_TYPE,
        type_id=created.id,
        new_schema_def=initial_schema_def,
        namespace_id=namespace_id,
        created_by=None,
    )

    await uow.commit()

    return to_relationship_type_response(created)


@router.get(
    "",
    response_model=list[RelationshipTypeResponse],
    summary="List relationship types",
    description="Get all relationship type schema definitions.",
)
async def list_relationship_types(
    repo: Repo,
    namespace_id: NamespaceIdDep,
) -> list[RelationshipTypeResponse]:
    """List all relationship types.

    Args:
        repo: Relationship type repository from dependency injection.

    Returns:
        List of all relationship types.
    """
    relationship_types = await repo.list_all()

    return [to_relationship_type_response(rt) for rt in relationship_types]


@router.get(
    "/{relationship_type_id}",
    response_model=RelationshipTypeResponse,
    summary="Get relationship type by ID",
    description="Get a specific relationship type schema definition by ID.",
)
async def get_relationship_type(
    relationship_type_id: UUID,
    repo: Repo,
    namespace_id: NamespaceIdDep,
) -> RelationshipTypeResponse:
    """Get relationship type by ID.

    Args:
        relationship_type_id: The relationship type UUID.
        repo: Relationship type repository from dependency injection.

    Returns:
        The relationship type if found.

    Raises:
        EntityNotFoundError: If relationship type not found.
    """
    relationship_type = await repo.get_by_id(str(relationship_type_id))

    if relationship_type is None:
        raise EntityNotFoundError(str(relationship_type_id), "RelationshipType")

    return to_relationship_type_response(relationship_type)


@router.delete(
    "/{relationship_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete relationship type",
    description="Delete a relationship type schema definition.",
)
async def delete_relationship_type(
    relationship_type_id: UUID,
    _session: DbSession,
    uow: UnitOfWorkDep,
    repo: Repo,
    namespace_id: NamespaceIdDep,
) -> Response:
    """Delete relationship type by ID.

    Args:
        relationship_type_id: The relationship type UUID.
        repo: Relationship type repository from dependency injection.

    Returns:
        204 No Content on success.

    Raises:
        EntityNotFoundError: If relationship type not found.
    """
    existing = await repo.get_by_id(str(relationship_type_id))
    if existing is None:
        raise EntityNotFoundError(str(relationship_type_id), "RelationshipType")

    deleted = await repo.delete(str(relationship_type_id))

    if not deleted:
        raise EntityNotFoundError(str(relationship_type_id), "RelationshipType")

    await uow.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{relationship_type_id}",
    response_model=RelationshipTypeResponse,
    summary="Update relationship type",
    description="Update an existing relationship type schema definition.",
)
async def update_relationship_type(
    relationship_type_id: UUID,
    data: RelationshipTypeUpdate,
    _session: DbSession,
    uow: UnitOfWorkDep,
    repo: Repo,
    schema_version_repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
    force: bool = Query(default=False, description="破壊的変更を強制実行する"),
) -> RelationshipTypeResponse:
    """Update relationship type by ID.

    Args:
        relationship_type_id: The relationship type UUID.
        data: The update data.
        repo: Relationship type repository from dependency injection.

    Returns:
        The updated relationship type.

    Raises:
        EntityNotFoundError: If relationship type not found.
    """
    existing = await repo.get_by_id(str(relationship_type_id))

    if existing is None:
        raise EntityNotFoundError(str(relationship_type_id), "RelationshipType")

    # Apply partial updates
    name = data.name if data.name is not None else existing.name
    description = data.description if data.description is not None else existing.description
    directional = data.directional if data.directional is not None else existing.directional
    custom_validators = data.custom_validators if data.custom_validators is not None else existing.custom_validators

    if data.properties is not None:
        properties = {prop_name: to_domain_property_definition(prop) for prop_name, prop in data.properties.items()}
    else:
        properties = existing.properties

    allowed_source_types = (
        data.allowed_source_types if data.allowed_source_types is not None else existing.allowed_source_types
    )
    allowed_target_types = (
        data.allowed_target_types if data.allowed_target_types is not None else existing.allowed_target_types
    )
    allow_duplicates = data.allow_duplicates if data.allow_duplicates is not None else existing.allow_duplicates
    updated_relationship_type = RelationshipType(
        id=existing.id,
        name=name,
        description=description,
        directional=directional,
        properties=properties,
        custom_validators=custom_validators,
        created_at=existing.created_at,
        updated_at=datetime.now(UTC),
        allowed_source_types=allowed_source_types,
        allowed_target_types=allowed_target_types,
        allow_duplicates=allow_duplicates,
    )

    # スキーマ互換性チェック（破壊的変更の検出）
    old_schema_def = serialize_properties_to_schema_def(existing.properties)
    new_schema_def = serialize_properties_to_schema_def(properties)
    check_schema_compatibility(old_schema_def, new_schema_def, force=force)

    # スキーマバージョンを自動記録（更新前にスナップショット）
    await record_schema_version(
        schema_version_repo=schema_version_repo,
        type_kind=TypeKind.RELATIONSHIP_TYPE,
        type_id=relationship_type_id,
        new_schema_def=new_schema_def,
        namespace_id=namespace_id,
        created_by=None,
    )

    updated = await repo.update(updated_relationship_type)
    await uow.commit()

    return to_relationship_type_response(updated)
