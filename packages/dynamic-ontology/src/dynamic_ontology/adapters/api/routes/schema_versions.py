"""SchemaVersion API routes -- バージョン一覧・取得・差分・ロールバック."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.adapters.api.dependencies import (
    UnitOfWorkDep,
    get_db_session,
    get_entity_type_repository,
    get_namespace_id,
    get_relationship_type_repository,
    get_schema_version_repository,
)
from dynamic_ontology.adapters.api.models import (
    EntityTypeResponse,
    RelationshipTypeResponse,
    SchemaDiffResponse,
    SchemaRollbackRequest,
    SchemaVersionResponse,
)
from dynamic_ontology.adapters.api.schema_helpers import (
    record_schema_version,
    serialize_properties_to_schema_def,
    to_entity_type_response,
    to_relationship_type_response,
)
from dynamic_ontology.domain.exceptions import EntityNotFoundError
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.relationship import RelationshipType
from dynamic_ontology.domain.models.schema_version import SchemaVersion, TypeKind
from dynamic_ontology.domain.ports.repository import EntityTypeRepository, RelationshipTypeRepository
from dynamic_ontology.domain.ports.schema_version_repository import SchemaVersionRepository
from dynamic_ontology.domain.services.schema_versioning import compute_diff

router = APIRouter(tags=["Schema - Versions"])

# DI aliases
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
SchemaVersionRepo = Annotated[SchemaVersionRepository, Depends(get_schema_version_repository)]
EntityTypeRepo = Annotated[EntityTypeRepository, Depends(get_entity_type_repository)]
RelationshipTypeRepo = Annotated[RelationshipTypeRepository, Depends(get_relationship_type_repository)]
NamespaceIdDep = Annotated[str, Depends(get_namespace_id)]


def _schema_def_to_properties(
    schema_def: dict[str, object],
) -> dict[str, PropertyDefinition]:
    """schema_definition JSONB からドメインの PropertyDefinition に復元する."""
    props_raw = schema_def.get("properties", {})
    result: dict[str, PropertyDefinition] = {}
    if not isinstance(props_raw, dict):
        return result
    for prop_name, prop_data in props_raw.items():
        if not isinstance(prop_data, dict):
            continue
        result[prop_name] = PropertyDefinition(
            type=PropertyType(str(prop_data.get("type", "string"))),
            required=bool(prop_data.get("required", False)),
            indexed=bool(prop_data.get("indexed", False)),
            default=prop_data.get("default"),
            min_length=prop_data.get("min_length"),
            max_length=prop_data.get("max_length"),
            pattern=prop_data.get("pattern"),
            enum=prop_data.get("enum"),
            min_value=prop_data.get("min_value"),
            max_value=prop_data.get("max_value"),
            state_transitions=prop_data.get("state_transitions"),
        )
    return result


def _to_schema_version_response(sv: SchemaVersion) -> SchemaVersionResponse:
    """ドメインモデルを Pydantic レスポンスに変換する."""
    return SchemaVersionResponse(
        id=sv.id,
        type_kind=sv.type_kind.value,
        type_id=sv.type_id,
        version=sv.version,
        schema_definition=sv.schema_definition,
        compatibility=sv.compatibility.value if sv.compatibility else None,
        change_summary=sv.change_summary,
        created_at=sv.created_at,
        created_by=sv.created_by,
    )


# --- Entity Type Versions ---


@router.get(
    "/schema/entity-types/{entity_type_id}/versions",
    response_model=list[SchemaVersionResponse],
    summary="List entity type schema versions",
)
async def list_entity_type_versions(
    entity_type_id: UUID,
    repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
) -> list[SchemaVersionResponse]:
    """エンティティタイプのスキーマバージョン一覧を取得する."""
    versions = await repo.list_by_type_id(str(entity_type_id), TypeKind.ENTITY_TYPE)
    return [_to_schema_version_response(v) for v in versions]


@router.get(
    "/schema/entity-types/{entity_type_id}/versions/{version}",
    response_model=SchemaVersionResponse,
    summary="Get entity type schema version",
)
async def get_entity_type_version(
    entity_type_id: UUID,
    version: int,
    repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
) -> SchemaVersionResponse:
    """エンティティタイプの特定スキーマバージョンを取得する."""
    sv = await repo.get_by_version(str(entity_type_id), version)
    if sv is None:
        raise EntityNotFoundError(f"version {version}", "SchemaVersion")
    return _to_schema_version_response(sv)


@router.get(
    "/schema/entity-types/{entity_type_id}/diff",
    response_model=SchemaDiffResponse,
    summary="Diff entity type schema versions",
)
async def diff_entity_type_versions(
    entity_type_id: UUID,
    from_version: Annotated[int, Query(ge=1)],
    to_version: Annotated[int, Query(ge=1)],
    repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
) -> SchemaDiffResponse:
    """エンティティタイプの2つのバージョン間の差分を取得する."""
    from_sv = await repo.get_by_version(str(entity_type_id), from_version)
    if from_sv is None:
        raise EntityNotFoundError(f"version {from_version}", "SchemaVersion")
    to_sv = await repo.get_by_version(str(entity_type_id), to_version)
    if to_sv is None:
        raise EntityNotFoundError(f"version {to_version}", "SchemaVersion")

    diff = compute_diff(from_sv.schema_definition, to_sv.schema_definition)
    return SchemaDiffResponse(
        added_fields=diff.added_fields,
        removed_fields=diff.removed_fields,
        modified_fields=diff.modified_fields,
        compatibility=diff.compatibility.value,
    )


@router.post(
    "/schema/entity-types/{entity_type_id}/rollback",
    response_model=EntityTypeResponse,
    summary="EntityType を指定バージョンにロールバック",
    description="指定バージョンのスキーマ定義を復元し、新バージョンとして保存する。",
)
async def rollback_entity_type_schema(
    entity_type_id: UUID,
    body: SchemaRollbackRequest,
    _session: DbSession,
    uow: UnitOfWorkDep,
    schema_version_repo: SchemaVersionRepo,
    entity_type_repo: EntityTypeRepo,
    namespace_id: NamespaceIdDep,
) -> EntityTypeResponse:
    """EntityType のスキーマを指定バージョンにロールバックする.

    ロールバックはタイムトラベルパターンに従い、指定バージョンのスキーマ定義を
    新しいバージョンとして保存する（履歴は破壊しない）。
    """
    # 指定バージョンのスキーマを取得
    target_sv = await schema_version_repo.get_by_version(str(entity_type_id), body.to_version)
    if target_sv is None:
        raise EntityNotFoundError(f"version {body.to_version}", "SchemaVersion")

    # 現在の EntityType を取得
    existing = await entity_type_repo.get_by_id(str(entity_type_id))
    if existing is None:
        raise EntityNotFoundError(str(entity_type_id), "EntityType")

    # スキーマ定義からプロパティを復元
    restored_properties = _schema_def_to_properties(target_sv.schema_definition)
    new_schema_def = serialize_properties_to_schema_def(restored_properties)

    # 新バージョンとして記録
    await record_schema_version(
        schema_version_repo=schema_version_repo,
        type_kind=TypeKind.ENTITY_TYPE,
        type_id=entity_type_id,
        new_schema_def=new_schema_def,
        namespace_id=namespace_id,
        created_by=None,
    )

    # EntityType を更新
    updated_entity_type = EntityType(
        id=existing.id,
        name=existing.name,
        description=existing.description,
        properties=restored_properties,
        custom_validators=existing.custom_validators,
        created_at=existing.created_at,
        updated_at=datetime.now(UTC),
        display_property=existing.display_property,
    )
    updated = await entity_type_repo.update(updated_entity_type)
    await uow.commit()

    return to_entity_type_response(updated)


# --- Relationship Type Versions ---


@router.get(
    "/schema/relationship-types/{relationship_type_id}/versions",
    response_model=list[SchemaVersionResponse],
    summary="List relationship type schema versions",
)
async def list_relationship_type_versions(
    relationship_type_id: UUID,
    repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
) -> list[SchemaVersionResponse]:
    """リレーションシップタイプのスキーマバージョン一覧を取得する."""
    versions = await repo.list_by_type_id(str(relationship_type_id), TypeKind.RELATIONSHIP_TYPE)
    return [_to_schema_version_response(v) for v in versions]


@router.get(
    "/schema/relationship-types/{relationship_type_id}/versions/{version}",
    response_model=SchemaVersionResponse,
    summary="Get relationship type schema version",
)
async def get_relationship_type_version(
    relationship_type_id: UUID,
    version: int,
    repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
) -> SchemaVersionResponse:
    """リレーションシップタイプの特定スキーマバージョンを取得する."""
    sv = await repo.get_by_version(str(relationship_type_id), version)
    if sv is None:
        raise EntityNotFoundError(f"version {version}", "SchemaVersion")
    return _to_schema_version_response(sv)


@router.get(
    "/schema/relationship-types/{relationship_type_id}/diff",
    response_model=SchemaDiffResponse,
    summary="Diff relationship type schema versions",
)
async def diff_relationship_type_versions(
    relationship_type_id: UUID,
    from_version: Annotated[int, Query(ge=1)],
    to_version: Annotated[int, Query(ge=1)],
    repo: SchemaVersionRepo,
    namespace_id: NamespaceIdDep,
) -> SchemaDiffResponse:
    """リレーションシップタイプの2つのバージョン間の差分を取得する."""
    from_sv = await repo.get_by_version(str(relationship_type_id), from_version)
    if from_sv is None:
        raise EntityNotFoundError(f"version {from_version}", "SchemaVersion")
    to_sv = await repo.get_by_version(str(relationship_type_id), to_version)
    if to_sv is None:
        raise EntityNotFoundError(f"version {to_version}", "SchemaVersion")

    diff = compute_diff(from_sv.schema_definition, to_sv.schema_definition)
    return SchemaDiffResponse(
        added_fields=diff.added_fields,
        removed_fields=diff.removed_fields,
        modified_fields=diff.modified_fields,
        compatibility=diff.compatibility.value,
    )


@router.post(
    "/schema/relationship-types/{relationship_type_id}/rollback",
    response_model=RelationshipTypeResponse,
    summary="RelationshipType を指定バージョンにロールバック",
    description="指定バージョンのスキーマ定義を復元し、新バージョンとして保存する。",
)
async def rollback_relationship_type_schema(
    relationship_type_id: UUID,
    body: SchemaRollbackRequest,
    _session: DbSession,
    uow: UnitOfWorkDep,
    schema_version_repo: SchemaVersionRepo,
    relationship_type_repo: RelationshipTypeRepo,
    namespace_id: NamespaceIdDep,
) -> RelationshipTypeResponse:
    """RelationshipType のスキーマを指定バージョンにロールバックする.

    ロールバックはタイムトラベルパターンに従い、指定バージョンのスキーマ定義を
    新しいバージョンとして保存する（履歴は破壊しない）。
    """
    # 指定バージョンのスキーマを取得
    target_sv = await schema_version_repo.get_by_version(str(relationship_type_id), body.to_version)
    if target_sv is None:
        raise EntityNotFoundError(f"version {body.to_version}", "SchemaVersion")

    # 現在の RelationshipType を取得
    existing = await relationship_type_repo.get_by_id(str(relationship_type_id))
    if existing is None:
        raise EntityNotFoundError(str(relationship_type_id), "RelationshipType")

    # スキーマ定義からプロパティを復元
    restored_properties = _schema_def_to_properties(target_sv.schema_definition)
    new_schema_def = serialize_properties_to_schema_def(restored_properties)

    # 新バージョンとして記録
    await record_schema_version(
        schema_version_repo=schema_version_repo,
        type_kind=TypeKind.RELATIONSHIP_TYPE,
        type_id=relationship_type_id,
        new_schema_def=new_schema_def,
        namespace_id=namespace_id,
        created_by=None,
    )

    # RelationshipType を更新
    updated_relationship_type = RelationshipType(
        id=existing.id,
        name=existing.name,
        description=existing.description,
        directional=existing.directional,
        properties=restored_properties,
        custom_validators=existing.custom_validators,
        created_at=existing.created_at,
        updated_at=datetime.now(UTC),
        allowed_source_types=existing.allowed_source_types,
        allowed_target_types=existing.allowed_target_types,
        allow_duplicates=existing.allow_duplicates,
    )
    updated = await relationship_type_repo.update(updated_relationship_type)
    await uow.commit()

    return to_relationship_type_response(updated)
