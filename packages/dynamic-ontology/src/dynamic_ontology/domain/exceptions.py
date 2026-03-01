"""Domain layer exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dynamic_ontology.domain.models.batch import BatchItemError


class DomainException(Exception):
    """Base exception for domain layer."""

    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity is not found."""

    def __init__(self, entity_id: str, entity_type: str | None = None) -> None:
        """Initialize EntityNotFoundError."""
        self.entity_id = entity_id
        self.entity_type = entity_type
        msg = f"Entity {entity_id}"
        if entity_type:
            msg += f" of type {entity_type}"
        msg += " not found"
        super().__init__(msg)


class ValidationError(DomainException):
    """Raised when validation fails."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        """Initialize ValidationError."""
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} error(s)")


class VersionConflictError(DomainException):
    """Raised when optimistic locking detects a version conflict."""

    def __init__(self, entity_id: str, current_version: int, provided_version: int) -> None:
        """Initialize VersionConflictError."""
        self.entity_id = entity_id
        self.current_version = current_version
        self.provided_version = provided_version
        msg = (
            f"Version conflict for entity {entity_id}: "
            f"current version {current_version}, provided version {provided_version}"
        )
        super().__init__(msg)


class BatchOperationError(DomainException):
    """一括操作で1件以上のエラーが発生した場合に発生.

    全体がロールバックされる前に、どの項目が失敗したかの情報を保持する。
    """

    def __init__(self, errors: list[BatchItemError], operation: str) -> None:
        """Initialize BatchOperationError.

        Args:
            errors: List of errors for failed items.
            operation: The operation type (create, update, delete).
        """
        self.errors = errors
        self.operation = operation
        msg = f"Batch {operation} failed with {len(errors)} error(s)"
        super().__init__(msg)


class InvalidRollbackError(DomainException):
    """無効なロールバック操作が要求された場合に発生."""

    def __init__(self, message: str) -> None:
        """Initialize InvalidRollbackError."""
        super().__init__(message)


class DuplicateRelationshipError(DomainException):
    """同一ペアの重複リレーション作成を拒否する場合に発生."""

    def __init__(
        self,
        type_id: str,
        from_entity_id: str,
        to_entity_id: str,
    ) -> None:
        """Initialize DuplicateRelationshipError."""
        self.type_id = type_id
        self.from_entity_id = from_entity_id
        self.to_entity_id = to_entity_id
        msg = f"Duplicate relationship: type={type_id}, from={from_entity_id}, to={to_entity_id} already exists"
        super().__init__(msg)
