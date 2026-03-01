"""Entity domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class Entity:
    """Entity instance (data level)."""

    id: UUID
    type_id: UUID
    version: int
    properties: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    changed_by: str | None = None
