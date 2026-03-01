"""Batch operation domain models."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class BatchItemError:
    """Error information for a single item in batch operation.

    Attributes:
        index: The 0-based index of the item in the batch request.
        entity_id: The entity ID if known (None for create failures).
        message: Human-readable error message.
    """

    index: int
    entity_id: UUID | None
    message: str


@dataclass(frozen=True)
class BatchResult:
    """Result of a batch operation.

    All-or-nothing semantics: if success=False, the entire transaction
    was rolled back and no changes were persisted.

    Attributes:
        success: True if all operations succeeded, False if any failed.
        total: Total number of items in the batch request.
        succeeded: Number of items that would have succeeded (before rollback).
        failed: Number of items that failed.
        entity_ids: List of entity IDs (populated only on success).
        errors: List of errors for failed items.
    """

    success: bool
    total: int
    succeeded: int
    failed: int
    entity_ids: list[UUID]
    errors: list[BatchItemError]
