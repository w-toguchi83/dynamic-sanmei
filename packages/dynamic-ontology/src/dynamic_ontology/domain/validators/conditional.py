"""Conditional required validator for field dependencies."""

from typing import Any

from dynamic_ontology.domain.models.entity_type import EntityType


class ConditionalRequiredValidator:
    """Validates that certain fields are required when a condition is met.

    For example, when status="completed", completed_at is required.
    """

    def __init__(
        self,
        condition_field: str,
        condition_value: str,
        required_fields: list[str],
    ) -> None:
        """Initialize the validator with condition and required fields.

        Args:
            condition_field: The field to check for the condition.
            condition_value: The value that triggers the requirement.
            required_fields: Fields that become required when condition is met.
        """
        self._condition_field = condition_field
        self._condition_value = condition_value
        self._required_fields = required_fields

    @property
    def name(self) -> str:
        """Return the unique name of this validator."""
        fields = ",".join(self._required_fields)
        return f"conditional_required:{self._condition_field}:{self._condition_value}:{fields}"

    def validate(self, properties: dict[str, Any], entity_type: EntityType) -> list[str]:
        """Validate that required fields are present when condition is met.

        Args:
            properties: The properties to validate.
            entity_type: The entity type (unused but required by protocol).

        Returns:
            List of error messages. Empty if valid.
        """
        _ = entity_type  # Unused but required by protocol

        # Get condition field value
        condition_value = properties.get(self._condition_field)

        # Skip validation if condition field is missing or null
        if condition_value is None:
            return []

        # Skip validation if condition is not met
        if condition_value != self._condition_value:
            return []

        # Check all required fields
        errors: list[str] = []
        for field in self._required_fields:
            value = properties.get(field)
            if value is None:
                errors.append(f"'{field}' is required when '{self._condition_field}' is '{self._condition_value}'")

        return errors
