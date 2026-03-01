"""Relationship domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from dynamic_ontology.domain.models.entity_type import PropertyDefinition


@dataclass
class RelationshipType:
    """Relationship type definition (meta-meta level)."""

    id: UUID
    name: str
    description: str
    directional: bool
    properties: dict[str, PropertyDefinition]
    custom_validators: list[str]
    created_at: datetime
    updated_at: datetime
    allowed_source_types: list[UUID] = field(default_factory=list)
    allowed_target_types: list[UUID] = field(default_factory=list)
    allow_duplicates: bool = True


@dataclass
class Relationship:
    """Relationship instance (data level)."""

    id: UUID
    type_id: UUID
    from_entity_id: UUID
    to_entity_id: UUID
    version: int
    properties: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    changed_by: str | None = None
