"""スキーマタイプ変換の共有ヘルパー（EntityType / RelationshipType）.

entity_types ルーター、relationship_types ルーター、schema_versions ルーターで
共通利用される変換ロジックを集約する。
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from dynamic_ontology.adapters.api.models import (
    EntityTypeResponse,
    PropertyDefinitionCreate,
    PropertyDefinitionResponse,
    RelationshipTypeResponse,
)
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.relationship import RelationshipType
from dynamic_ontology.domain.models.schema_version import CompatibilityLevel, SchemaVersion, TypeKind
from dynamic_ontology.domain.ports.schema_version_repository import SchemaVersionRepository
from dynamic_ontology.domain.services.schema_versioning import compute_diff, generate_change_summary


def to_domain_property_definition(prop: PropertyDefinitionCreate) -> PropertyDefinition:
    """API プロパティ定義をドメインモデルに変換する.

    Args:
        prop: API プロパティ定義モデル.

    Returns:
        ドメイン PropertyDefinition インスタンス.
    """
    return PropertyDefinition(
        type=PropertyType(prop.type),
        required=prop.required,
        indexed=prop.indexed,
        default=prop.default,
        min_length=prop.min_length,
        max_length=prop.max_length,
        pattern=prop.pattern,
        enum=prop.enum,
        min_value=prop.min_value,
        max_value=prop.max_value,
        state_transitions=prop.state_transitions,
    )


def to_response_property_definition(prop: PropertyDefinition) -> PropertyDefinitionResponse:
    """ドメインプロパティ定義を API レスポンスモデルに変換する.

    Args:
        prop: ドメイン PropertyDefinition インスタンス.

    Returns:
        API PropertyDefinitionResponse インスタンス.
    """
    return PropertyDefinitionResponse(
        type=prop.type.value,
        required=prop.required,
        indexed=prop.indexed,
        default=prop.default,
        min_length=prop.min_length,
        max_length=prop.max_length,
        pattern=prop.pattern,
        enum=prop.enum,
        min_value=prop.min_value,
        max_value=prop.max_value,
        state_transitions=prop.state_transitions,
    )


def to_entity_type_response(entity_type: EntityType) -> EntityTypeResponse:
    """ドメイン EntityType を API レスポンスモデルに変換する.

    Args:
        entity_type: ドメイン EntityType インスタンス.

    Returns:
        API EntityTypeResponse インスタンス.
    """
    properties = {name: to_response_property_definition(prop) for name, prop in entity_type.properties.items()}
    return EntityTypeResponse(
        id=entity_type.id,
        name=entity_type.name,
        description=entity_type.description,
        properties=properties,
        custom_validators=entity_type.custom_validators,
        created_at=entity_type.created_at,
        updated_at=entity_type.updated_at,
        display_property=entity_type.display_property,
    )


def serialize_properties_to_schema_def(
    properties: dict[str, PropertyDefinition],
) -> dict[str, object]:
    """プロパティ定義を schema_definition JSONB 用の dict に変換する.

    SchemaVersion の schema_definition フィールドに保存するための
    シリアライズ処理。

    Args:
        properties: ドメインの PropertyDefinition 辞書.

    Returns:
        JSONB 保存可能な schema_definition dict.
    """
    serialized: dict[str, object] = {}
    for prop_name, prop_def in properties.items():
        prop_dict: dict[str, object] = {
            "type": prop_def.type.value,
            "required": prop_def.required,
        }
        if prop_def.indexed:
            prop_dict["indexed"] = prop_def.indexed
        if prop_def.default is not None:
            prop_dict["default"] = prop_def.default
        if prop_def.min_length is not None:
            prop_dict["min_length"] = prop_def.min_length
        if prop_def.max_length is not None:
            prop_dict["max_length"] = prop_def.max_length
        if prop_def.pattern is not None:
            prop_dict["pattern"] = prop_def.pattern
        if prop_def.enum is not None:
            prop_dict["enum"] = prop_def.enum
        if prop_def.min_value is not None:
            prop_dict["min_value"] = prop_def.min_value
        if prop_def.max_value is not None:
            prop_dict["max_value"] = prop_def.max_value
        if prop_def.state_transitions is not None:
            prop_dict["state_transitions"] = prop_def.state_transitions
        serialized[prop_name] = prop_dict
    return {"properties": serialized}


def check_schema_compatibility(
    old_schema_def: dict[str, object],
    new_schema_def: dict[str, object],
    *,
    force: bool,
) -> "SchemaDiff":
    """スキーマ変更の互換性をチェックし、破壊的変更時に 409 を返す.

    互換性が FORWARD（フィールド削除）または NONE（破壊的変更）の場合、
    force=False なら HTTPException(409) を送出する。

    Args:
        old_schema_def: 変更前のスキーマ定義.
        new_schema_def: 変更後のスキーマ定義.
        force: True の場合、破壊的変更でもエラーにしない.

    Returns:
        計算された SchemaDiff.

    Raises:
        HTTPException: 破壊的変更で force=False の場合（409 Conflict）.
    """

    diff = compute_diff(old_schema_def, new_schema_def)

    if diff.compatibility in (CompatibilityLevel.FORWARD, CompatibilityLevel.NONE) and not force:
        detail: dict[str, object] = {
            "message": "破壊的なスキーマ変更が検出されました",
            "compatibility": diff.compatibility.value,
            "added_fields": diff.added_fields,
            "removed_fields": diff.removed_fields,
            "modified_fields": list(diff.modified_fields.keys()),
            "hint": "force=true クエリパラメータを追加して強制実行できます",
        }
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    return diff


async def record_schema_version(
    schema_version_repo: SchemaVersionRepository,
    type_kind: TypeKind,
    type_id: UUID,
    new_schema_def: dict[str, object],
    namespace_id: str,
    created_by: str | None = None,
) -> SchemaVersion:
    """スキーマ更新時にバージョンレコードを自動作成する.

    最新バージョンが存在する場合は差分を計算し、新バージョンを記録する。
    初回の場合はバージョン 1 として記録する。

    Args:
        schema_version_repo: スキーマバージョンリポジトリ.
        type_kind: タイプの種類（entity_type / relationship_type）.
        type_id: 対象タイプの UUID.
        new_schema_def: 新しいスキーマ定義.
        namespace_id: namespace 識別子.
        created_by: 作成者の識別子.

    Returns:
        作成された SchemaVersion.
    """
    latest_version = await schema_version_repo.get_latest_version(str(type_id))

    if latest_version is not None:
        diff = compute_diff(latest_version.schema_definition, new_schema_def)
        change_summary = generate_change_summary(diff)
        new_version_num = latest_version.version + 1
        previous_version_id = latest_version.id
        compatibility = diff.compatibility
    else:
        new_version_num = 1
        previous_version_id = None
        compatibility = None
        change_summary = None

    # namespace_id を UUID に変換（str で渡される場合）
    ns_id = UUID(namespace_id) if isinstance(namespace_id, str) else namespace_id

    schema_version = SchemaVersion(
        id=uuid4(),
        type_kind=type_kind,
        type_id=type_id,
        version=new_version_num,
        schema_definition=new_schema_def,
        previous_version_id=previous_version_id,
        compatibility=compatibility,
        change_summary=change_summary,
        created_at=datetime.now(UTC),
        created_by=created_by,
        namespace_id=ns_id,
    )
    return await schema_version_repo.create(schema_version)


def to_relationship_type_response(
    relationship_type: RelationshipType,
) -> RelationshipTypeResponse:
    """ドメイン RelationshipType を API レスポンスモデルに変換する.

    Args:
        relationship_type: ドメイン RelationshipType インスタンス.

    Returns:
        API RelationshipTypeResponse インスタンス.
    """
    properties = {name: to_response_property_definition(prop) for name, prop in relationship_type.properties.items()}
    return RelationshipTypeResponse(
        id=relationship_type.id,
        name=relationship_type.name,
        description=relationship_type.description,
        directional=relationship_type.directional,
        properties=properties,
        custom_validators=relationship_type.custom_validators,
        created_at=relationship_type.created_at,
        updated_at=relationship_type.updated_at,
        allowed_source_types=relationship_type.allowed_source_types,
        allowed_target_types=relationship_type.allowed_target_types,
        allow_duplicates=relationship_type.allow_duplicates,
    )
