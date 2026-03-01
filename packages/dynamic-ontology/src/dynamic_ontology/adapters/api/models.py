"""動的オントロジー API リクエスト/レスポンス Pydantic モデル."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Error Models
class ErrorDetail(BaseModel):
    """バリデーションエラーの詳細."""

    field: str = Field(..., description="Field that caused the error")
    message: str = Field(..., description="Error message")


class ErrorResponse(BaseModel):
    """エラーレスポンスモデル."""

    detail: str = Field(..., description="Error message")
    errors: list[ErrorDetail] | None = Field(default=None, description="List of validation errors")


# Property Definition Models
class PropertyDefinitionCreate(BaseModel):
    """プロパティ定義の作成リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="Property type (string, integer, float, boolean, date)")
    required: bool = Field(..., description="Whether the property is required")
    indexed: bool = Field(default=False, description="Whether to index this property")
    default: str | int | float | bool | None = Field(default=None, description="Default value")

    # String constraints
    min_length: int | None = Field(default=None, ge=0, description="Minimum length")
    max_length: int | None = Field(default=None, ge=0, description="Maximum length")
    pattern: str | None = Field(default=None, description="Regex pattern for validation")
    enum: list[str] | None = Field(default=None, description="Allowed values")

    # Numeric constraints
    min_value: int | float | None = Field(default=None, description="Minimum value")
    max_value: int | float | None = Field(default=None, description="Maximum value")

    # State machine constraints
    state_transitions: dict[str, list[str]] | None = Field(
        default=None,
        description="Allowed state transitions (key=current state, value=allowed next states)",
    )


class PropertyDefinitionResponse(BaseModel):
    """プロパティ定義のレスポンスモデル."""

    model_config = ConfigDict(from_attributes=True)

    type: str
    required: bool
    indexed: bool
    default: str | int | float | bool | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[str] | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    state_transitions: dict[str, list[str]] | None = None


# EntityType Models
class EntityTypeCreate(BaseModel):
    """エンティティタイプの作成リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=255)]
    description: str = Field(default="", max_length=1000)
    properties: dict[str, PropertyDefinitionCreate] = Field(
        default_factory=dict, description="Property definitions"
    )
    custom_validators: list[str] = Field(default_factory=list, description="Custom validator names")
    display_property: str | None = Field(
        default=None, description="Property name to use as display label for entities of this type"
    )


class EntityTypeUpdate(BaseModel):
    """エンティティタイプの更新リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    description: str | None = Field(default=None, max_length=1000)
    properties: dict[str, PropertyDefinitionCreate] | None = None
    custom_validators: list[str] | None = None
    display_property: str | None = None


class EntityTypeResponse(BaseModel):
    """エンティティタイプのレスポンスモデル."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    properties: dict[str, PropertyDefinitionResponse]
    custom_validators: list[str]
    created_at: datetime
    updated_at: datetime
    display_property: str | None = None


# Entity Models
class EntityCreate(BaseModel):
    """エンティティの作成リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    type_id: UUID = Field(..., description="The entity type ID")
    properties: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict, description="Entity properties"
    )


class EntityUpdate(BaseModel):
    """エンティティの更新リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    properties: dict[str, str | int | float | bool | None] = Field(
        ..., description="Updated properties"
    )
    version: int = Field(..., ge=1, description="Current version for optimistic locking")


class EntityResponse(BaseModel):
    """エンティティのレスポンスモデル."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type_id: UUID
    type_name: str | None = None
    version: int
    properties: dict[str, str | int | float | bool | None]
    created_at: datetime
    updated_at: datetime
    changed_by: str | None = None


class EntityListResponse(BaseModel):
    """エンティティ一覧のレスポンスモデル."""

    items: list[EntityResponse]
    total: int = Field(..., ge=0, description="Total number of items")
    limit: int = Field(..., ge=1, description="Page size")
    offset: int = Field(..., ge=0, description="Page offset")
    next_cursor: str | None = Field(default=None, description="Cursor for next page")
    has_more: bool = Field(default=False, description="Whether more items exist")


# RelationshipType Models
class RelationshipTypeCreate(BaseModel):
    """リレーションシップタイプの作成リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=255)]
    description: str = Field(default="", max_length=1000)
    directional: bool = Field(default=True, description="Whether the relationship is directional")
    properties: dict[str, PropertyDefinitionCreate] = Field(
        default_factory=dict, description="Property definitions"
    )
    custom_validators: list[str] = Field(default_factory=list, description="Custom validator names")
    allowed_source_types: list[UUID] = Field(
        default_factory=list, description="Allowed source entity type IDs"
    )
    allowed_target_types: list[UUID] = Field(
        default_factory=list, description="Allowed target entity type IDs"
    )
    allow_duplicates: bool = Field(
        default=True,
        description="Whether to allow duplicate relationships for the same entity pair",
    )


class RelationshipTypeUpdate(BaseModel):
    """リレーションシップタイプの更新リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    description: str | None = Field(default=None, max_length=1000)
    directional: bool | None = None
    properties: dict[str, PropertyDefinitionCreate] | None = None
    custom_validators: list[str] | None = None
    allowed_source_types: list[UUID] | None = None
    allowed_target_types: list[UUID] | None = None
    allow_duplicates: bool | None = None


class RelationshipTypeResponse(BaseModel):
    """リレーションシップタイプのレスポンスモデル."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    directional: bool
    properties: dict[str, PropertyDefinitionResponse]
    custom_validators: list[str]
    created_at: datetime
    updated_at: datetime
    allowed_source_types: list[UUID] = Field(default_factory=list)
    allowed_target_types: list[UUID] = Field(default_factory=list)
    allow_duplicates: bool = True


# Relationship Models
class RelationshipCreate(BaseModel):
    """リレーションシップの作成リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    type_id: UUID = Field(..., description="The relationship type ID")
    from_entity_id: UUID = Field(..., description="Source entity ID")
    to_entity_id: UUID = Field(..., description="Target entity ID")
    properties: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict, description="Relationship properties"
    )


class RelationshipUpdate(BaseModel):
    """リレーションシップの更新リクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    properties: dict[str, str | int | float | bool | None] = Field(
        ..., description="Updated properties"
    )
    version: int = Field(..., ge=1, description="Current version for optimistic locking")


class RelationshipResponse(BaseModel):
    """リレーションシップのレスポンスモデル."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type_id: UUID
    from_entity_id: UUID
    to_entity_id: UUID
    version: int
    properties: dict[str, str | int | float | bool | None]
    created_at: datetime
    updated_at: datetime
    type_name: str | None = None
    from_entity_display_name: str | None = None
    to_entity_display_name: str | None = None
    from_entity_type_name: str | None = None
    to_entity_type_name: str | None = None
    changed_by: str | None = None


class RelationshipListResponse(BaseModel):
    """リレーションシップ一覧のレスポンスモデル."""

    items: list[RelationshipResponse]
    total: int = Field(..., ge=0, description="Total number of items in database")
    limit: int = Field(default=100, ge=1, description="Page size")
    offset: int = Field(default=0, ge=0, description="Page offset")
    next_cursor: str | None = Field(default=None, description="Cursor for next page")
    has_more: bool = Field(default=False, description="Whether more items exist")


# Query Models
class FilterConditionRequest(BaseModel):
    """フィルタ条件のリクエストモデル（ネストされた AND/OR ロジック対応）."""

    model_config = ConfigDict(extra="forbid")

    field: str | None = Field(default=None, description="Property field name to filter on")
    op: str | None = Field(
        default=None,
        description="Filter operator: eq, ne, gt, gte, lt, lte, in, not_in, contains, starts_with, ends_with, is_null, is_not_null, regex, full_text",
    )
    value: str | int | float | bool | list[str] | list[int] | list[float] | None = Field(
        default=None, description="Value to compare against"
    )
    and_: list[FilterConditionRequest] | None = Field(
        default=None, alias="and", description="AND conditions (all must match)"
    )
    or_: list[FilterConditionRequest] | None = Field(
        default=None, alias="or", description="OR conditions (any must match)"
    )


class SortFieldRequest(BaseModel):
    """ソートフィールドのリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(..., description="Property field name to sort by")
    order: str = Field(
        default="asc",
        description="Sort order: asc or desc",
    )


class TraverseConfigRequest(BaseModel):
    """リレーションシップトラバーサル設定のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="Relationship type name to traverse")
    direction: str = Field(
        default="outgoing",
        description="Traversal direction: outgoing, incoming, or both",
    )
    depth: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum traversal depth (1-5)",
    )


class AggregateConfigRequest(BaseModel):
    """集約操作のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    count: bool = Field(default=False, description="Include count in results")
    sum: str | None = Field(default=None, description="Property field to sum")
    avg: str | None = Field(default=None, description="Property field to average")
    min: str | None = Field(default=None, description="Property field to get minimum")
    max: str | None = Field(default=None, description="Property field to get maximum")
    group_by: list[str] = Field(default_factory=list, description="Fields to group by")


class QueryRequest(BaseModel):
    """クエリ実行のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    entity_type: str = Field(..., description="Entity type name to query")
    filter: FilterConditionRequest | None = Field(default=None, description="Filter conditions")
    sort: list[SortFieldRequest] = Field(default_factory=list, description="Sort configuration")
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results (1-1000)",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip",
    )
    traverse: TraverseConfigRequest | None = Field(
        default=None, description="Relationship traversal configuration"
    )
    aggregate: AggregateConfigRequest | None = Field(
        default=None, description="Aggregation configuration"
    )
    at_time: str | None = Field(default=None, description="ISO timestamp for time-travel query")
    cursor: str | None = Field(default=None, description="Cursor for cursor-based pagination")


class RelatedEntitiesResponse(BaseModel):
    """トラバーサルによる関連エンティティのレスポンスモデル."""

    entity_id: str = Field(..., description="Starting entity ID")
    related: list[EntityResponse] = Field(
        default_factory=list, description="Related entities found through traversal"
    )


class QueryResultResponse(BaseModel):
    """クエリ結果のレスポンスモデル."""

    items: list[EntityResponse] = Field(default_factory=list, description="Matching entities")
    total: int = Field(..., ge=0, description="Total count before pagination")
    limit: int = Field(..., ge=1, description="Page size used")
    offset: int = Field(..., ge=0, description="Offset used")
    aggregations: (
        dict[str, int | float | str | list[dict[str, int | float | str | None]] | None] | None
    ) = Field(default=None, description="Aggregation results if requested")
    related_entities: list[RelatedEntitiesResponse] | None = Field(
        default=None, description="Related entities from traversal if requested"
    )
    next_cursor: str | None = Field(default=None, description="Cursor for next page")
    has_more: bool = Field(default=False, description="Whether more items exist")


# Time Travel Models
class PropertyChangeResponse(BaseModel):
    """プロパティ変更のレスポンスモデル."""

    field: str = Field(..., description="変更されたプロパティ名")
    old_value: Any = Field(..., description="変更前の値")
    new_value: Any = Field(..., description="変更後の値")
    change_type: str = Field(..., description="変更タイプ: added, removed, modified")


class EntityDiffResponse(BaseModel):
    """エンティティ差分のレスポンスモデル."""

    entity_id: UUID = Field(..., description="エンティティID")
    from_version: int = Field(..., ge=1, description="比較元バージョン")
    to_version: int = Field(..., ge=1, description="比較先バージョン")
    from_time: datetime = Field(..., description="比較元の時刻")
    to_time: datetime = Field(..., description="比較先の時刻")
    changes: list[PropertyChangeResponse] = Field(
        default_factory=list, description="プロパティ変更リスト"
    )
    has_changes: bool = Field(..., description="変更があるかどうか")


class EntitySnapshotResponse(BaseModel):
    """エンティティスナップショットのレスポンスモデル."""

    entity_id: UUID = Field(..., description="エンティティID")
    type_id: UUID = Field(..., description="エンティティタイプID")
    version: int = Field(..., ge=1, description="バージョン番号")
    properties: dict[str, Any] = Field(..., description="プロパティ")
    valid_from: datetime = Field(..., description="有効期間開始時刻")
    valid_to: datetime | None = Field(
        default=None, description="有効期間終了時刻（None は現在有効）"
    )
    operation: str = Field(..., description="操作タイプ: CREATE, UPDATE, DELETE")
    is_current: bool = Field(..., description="現在有効なスナップショットかどうか")


class EntityRollbackRequest(BaseModel):
    """エンティティロールバックのリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    target_version: int | None = Field(
        default=None, ge=1, description="ロールバック先のバージョン番号"
    )
    target_time: str | None = Field(
        default=None, description="ロールバック先の ISO8601 タイムスタンプ"
    )

    @model_validator(mode="after")
    def validate_target(self) -> EntityRollbackRequest:
        """target_version または target_time のいずれかが必須."""
        if self.target_version is None and self.target_time is None:
            raise ValueError("target_version または target_time のいずれかを指定してください")
        return self


# Batch Operation Models
class BatchEntityCreate(BaseModel):
    """エンティティ一括作成のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    entities: list[EntityCreate] = Field(
        ..., description="List of entities to create", min_length=1, max_length=1000
    )


class BatchEntityUpdate(BaseModel):
    """一括更新における単一エンティティの更新."""

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(..., description="Entity ID to update")
    version: int = Field(..., description="Current version for optimistic locking", ge=1)
    properties: dict[str, str | int | float | bool | None] = Field(
        ..., description="Updated properties"
    )


class BatchEntityUpdateRequest(BaseModel):
    """エンティティ一括更新のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    updates: list[BatchEntityUpdate] = Field(
        ..., description="List of entity updates", min_length=1, max_length=1000
    )


class BatchEntityDelete(BaseModel):
    """エンティティ一括削除のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    entity_ids: list[UUID] = Field(
        ..., description="List of entity IDs to delete", min_length=1, max_length=1000
    )


class BatchItemErrorResponse(BaseModel):
    """一括操作レスポンスにおける個別エラー情報."""

    index: int = Field(..., description="0-based index of the failed item")
    entity_id: UUID | None = Field(None, description="Entity ID if known")
    message: str = Field(..., description="Error message")


class BatchResultResponse(BaseModel):
    """一括操作のレスポンスモデル."""

    success: bool = Field(..., description="True if all operations succeeded")
    total: int = Field(..., description="Total items in request")
    succeeded: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    entity_ids: list[UUID] = Field(
        default_factory=list, description="IDs of affected entities (on success only)"
    )
    errors: list[BatchItemErrorResponse] = Field(
        default_factory=list, description="Error details for failed items"
    )


# Relationship Batch Operation Models
class BatchRelationshipCreate(BaseModel):
    """リレーションシップ一括作成のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    relationships: list[RelationshipCreate] = Field(
        ..., description="List of relationships to create", min_length=1, max_length=1000
    )


class BatchRelationshipUpdate(BaseModel):
    """一括更新における単一リレーションシップの更新."""

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(..., description="Relationship ID to update")
    version: int = Field(..., description="Current version for optimistic locking", ge=1)
    properties: dict[str, str | int | float | bool | None] = Field(
        ..., description="Updated properties"
    )


class BatchRelationshipUpdateRequest(BaseModel):
    """リレーションシップ一括更新のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    updates: list[BatchRelationshipUpdate] = Field(
        ..., description="List of relationship updates", min_length=1, max_length=1000
    )


class BatchRelationshipDelete(BaseModel):
    """リレーションシップ一括削除のリクエストモデル."""

    model_config = ConfigDict(extra="forbid")

    relationship_ids: list[UUID] = Field(
        ..., description="List of relationship IDs to delete", min_length=1, max_length=1000
    )


# Schema Version Models
class SchemaVersionResponse(BaseModel):
    """スキーマバージョンのレスポンスモデル."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type_kind: str
    type_id: UUID
    version: int
    schema_definition: dict[str, object]
    compatibility: str | None = None
    change_summary: dict[str, object] | None = None
    created_at: datetime
    created_by: str | None = None


class SchemaDiffResponse(BaseModel):
    """スキーマ差分のレスポンスモデル."""

    model_config = ConfigDict(from_attributes=True)

    added_fields: list[str]
    removed_fields: list[str]
    modified_fields: dict[str, dict[str, object]]
    compatibility: str


class SchemaRollbackRequest(BaseModel):
    """スキーマロールバックのリクエストモデル."""

    to_version: int = Field(ge=1, description="ロールバック先のバージョン番号")
