"""Custom validator protocol for cross-property validation."""

from typing import Any, Protocol, runtime_checkable

from dynamic_ontology.domain.models.entity_type import EntityType


@runtime_checkable
class CustomValidator(Protocol):
    """Protocol for custom validators.

    Custom validators perform cross-property validation that cannot be
    expressed through simple property constraints. They are referenced
    by name in EntityType.custom_validators.
    """

    @property
    def name(self) -> str:
        """The unique name of this validator.

        This name is used to reference the validator in EntityType.custom_validators.
        """
        ...

    def validate(self, properties: dict[str, Any], entity_type: EntityType) -> list[str]:
        """Validate properties against custom rules.

        Args:
            properties: The properties to validate.
            entity_type: The entity type for context.

        Returns:
            List of error messages. Empty list means validation passed.
        """
        ...
