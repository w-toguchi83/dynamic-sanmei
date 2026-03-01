"""EntityType domain model."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class PropertyType(StrEnum):
    """Property data types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"


@dataclass
class PropertyDefinition:
    """Definition of a property in an entity type schema."""

    type: PropertyType
    required: bool
    indexed: bool = False
    default: Any = None

    # String constraints
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[str] | None = None

    # Numeric constraints
    min_value: int | float | None = None
    max_value: int | float | None = None

    # 状態遷移制約
    state_transitions: dict[str, list[str]] | None = None


@dataclass
class EntityType:
    """Entity type definition (meta-meta level)."""

    id: UUID
    name: str
    description: str
    properties: dict[str, PropertyDefinition]
    custom_validators: list[str]
    created_at: datetime
    updated_at: datetime
    display_property: str | None = None
