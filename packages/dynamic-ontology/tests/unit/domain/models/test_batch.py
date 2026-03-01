"""Unit tests for Batch domain models."""

from uuid import uuid4

import pytest

from dynamic_ontology.domain.models.batch import BatchItemError, BatchResult


class TestBatchItemError:
    """Tests for BatchItemError model."""

    def test_create_batch_item_error(self) -> None:
        """BatchItemError stores index, entity_id, and message."""
        entity_id = uuid4()
        error = BatchItemError(
            index=0,
            entity_id=entity_id,
            message="Validation failed",
        )

        assert error.index == 0
        assert error.entity_id == entity_id
        assert error.message == "Validation failed"

    def test_batch_item_error_without_entity_id(self) -> None:
        """BatchItemError can be created without entity_id (for create failures)."""
        error = BatchItemError(
            index=2,
            entity_id=None,
            message="Type not found",
        )

        assert error.index == 2
        assert error.entity_id is None
        assert error.message == "Type not found"


class TestBatchResult:
    """Tests for BatchResult model."""

    def test_create_success_batch_result(self) -> None:
        """BatchResult with all successes."""
        entity_ids = [uuid4(), uuid4(), uuid4()]
        result = BatchResult(
            success=True,
            total=3,
            succeeded=3,
            failed=0,
            entity_ids=entity_ids,
            errors=[],
        )

        assert result.success is True
        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0
        assert result.entity_ids == entity_ids
        assert result.errors == []

    def test_create_failed_batch_result(self) -> None:
        """BatchResult with failures triggers rollback."""
        error = BatchItemError(index=1, entity_id=None, message="Invalid type")
        result = BatchResult(
            success=False,
            total=3,
            succeeded=0,
            failed=1,
            entity_ids=[],
            errors=[error],
        )

        assert result.success is False
        assert result.total == 3
        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.errors) == 1
        assert result.errors[0].index == 1

    def test_batch_result_immutable(self) -> None:
        """BatchResult is immutable (frozen dataclass)."""
        result = BatchResult(
            success=True,
            total=1,
            succeeded=1,
            failed=0,
            entity_ids=[uuid4()],
            errors=[],
        )

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]
