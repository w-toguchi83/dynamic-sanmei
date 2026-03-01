"""Date range validator for ensuring end date is after start date."""

from datetime import date, datetime
from typing import Any

from dynamic_ontology.domain.models.entity_type import EntityType


class DateRangeValidator:
    """Validates that an end date field is not before a start date field.

    This validator ensures proper chronological ordering of date pairs,
    such as start_date/end_date or created_at/completed_at.
    """

    def __init__(self, start_field: str, end_field: str) -> None:
        """Initialize the validator with field names.

        Args:
            start_field: Name of the start date property.
            end_field: Name of the end date property.
        """
        self._start_field = start_field
        self._end_field = end_field

    @property
    def name(self) -> str:
        """Return the unique name of this validator."""
        return f"date_range:{self._start_field}:{self._end_field}"

    def validate(self, properties: dict[str, Any], entity_type: EntityType) -> list[str]:
        """Validate that end date is not before start date.

        Args:
            properties: The properties to validate.
            entity_type: The entity type (unused but required by protocol).

        Returns:
            List of error messages. Empty if valid.
        """
        _ = entity_type  # Unused but required by protocol

        start_value = properties.get(self._start_field)
        end_value = properties.get(self._end_field)

        # Skip validation if either date is missing
        if start_value is None or end_value is None:
            return []

        # Convert to comparable format
        start_date = self._to_date(start_value)
        end_date = self._to_date(end_value)

        if start_date is None or end_date is None:
            return []

        if end_date < start_date:
            return [f"'{self._end_field}' must be on or after '{self._start_field}'"]

        return []

    def _to_date(self, value: Any) -> date | None:
        """Convert a value to a date for comparison.

        Args:
            value: The value to convert (str, date, or datetime).

        Returns:
            A date object or None if conversion fails.
        """
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
                return parsed.date()
            except ValueError:
                return None
        return None
