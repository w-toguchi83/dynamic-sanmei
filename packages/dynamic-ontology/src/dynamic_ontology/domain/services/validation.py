"""ValidationEngine for property validation against EntityType schema."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from dynamic_ontology.domain.exceptions import ValidationError
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.validators.state_transition import StateTransitionValidator

if TYPE_CHECKING:
    from dynamic_ontology.domain.services.validator_registry import ValidatorRegistry


class ValidationEngine:
    """Validates entity properties against EntityType schema definitions."""

    def __init__(self, validator_registry: ValidatorRegistry | None = None) -> None:
        """Initialize ValidationEngine.

        Args:
            validator_registry: Optional registry of custom validators.
                               If None, custom validators in entity types are skipped.
        """
        self._validator_registry = validator_registry
        self._state_transition_validator = StateTransitionValidator()

    def validate(
        self,
        properties: dict[str, Any],
        entity_type: EntityType,
        existing_properties: dict[str, Any] | None = None,
    ) -> None:
        """Validate properties against entity type schema.

        Args:
            properties: The properties to validate.
            entity_type: The entity type containing the schema definition.
            existing_properties: The current properties before update.
                                If provided, state transition constraints are checked.
                                Pass None for entity creation (no transition check).

        Raises:
            ValidationError: If validation fails with list of error details.
        """
        errors = self._collect_validation_errors(properties, entity_type)

        # Run custom validators if registry is available
        custom_errors = self._run_custom_validators(properties, entity_type)
        errors.extend(custom_errors)

        # 状態遷移チェック（更新時のみ）
        if existing_properties is not None:
            transition_errors = self._state_transition_validator.validate(existing_properties, properties, entity_type)
            for msg in transition_errors:
                errors.append({"field": "_state_transition", "message": msg})

        if errors:
            raise ValidationError(errors)

    def validate_and_apply_defaults(
        self,
        properties: dict[str, Any],
        entity_type: EntityType,
        existing_properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Validate properties and apply default values for missing optional fields.

        Args:
            properties: The properties to validate.
            entity_type: The entity type containing the schema definition.
            existing_properties: The current properties before update.
                                If provided, state transition constraints are checked.
                                Pass None for entity creation (no transition check).

        Returns:
            A new dictionary with validated properties and defaults applied.

        Raises:
            ValidationError: If validation fails with list of error details.
        """
        self.validate(properties, entity_type, existing_properties=existing_properties)

        result = dict(properties)
        for prop_name, prop_def in entity_type.properties.items():
            if prop_name not in result and prop_def.default is not None:
                result[prop_name] = prop_def.default

        return result

    def _collect_validation_errors(self, properties: dict[str, Any], entity_type: EntityType) -> list[dict[str, str]]:
        """Collect all validation errors for the given properties.

        Args:
            properties: The properties to validate.
            entity_type: The entity type containing the schema definition.

        Returns:
            List of error dictionaries with 'field' and 'message' keys.
        """
        errors: list[dict[str, str]] = []

        # Check for required properties
        for prop_name, prop_def in entity_type.properties.items():
            if prop_def.required and prop_name not in properties:
                errors.append(
                    {
                        "field": prop_name,
                        "message": f"Required property '{prop_name}' is missing",
                    }
                )

        # Validate each provided property
        for prop_name, value in properties.items():
            if prop_name not in entity_type.properties:
                # Skip unknown properties (or could add error for strict mode)
                continue

            prop_def = entity_type.properties[prop_name]
            prop_errors = self._validate_property(prop_name, value, prop_def)
            errors.extend(prop_errors)

        return errors

    def _validate_property(self, prop_name: str, value: Any, prop_def: PropertyDefinition) -> list[dict[str, str]]:
        """Validate a single property value against its definition.

        Args:
            prop_name: The name of the property.
            value: The value to validate.
            prop_def: The property definition containing constraints.

        Returns:
            List of error dictionaries for this property.
        """
        errors: list[dict[str, str]] = []

        # Allow None for optional properties
        if value is None:
            if prop_def.required:
                errors.append(
                    {
                        "field": prop_name,
                        "message": f"Required property '{prop_name}' cannot be null",
                    }
                )
            return errors

        # Type validation
        type_error = self._validate_type(prop_name, value, prop_def.type)
        if type_error:
            errors.append(type_error)
            return errors  # Skip constraint validation if type is wrong

        # Constraint validation based on type
        if prop_def.type == PropertyType.STRING:
            errors.extend(self._validate_string_constraints(prop_name, value, prop_def))
        elif prop_def.type in (PropertyType.INTEGER, PropertyType.FLOAT):
            errors.extend(self._validate_numeric_constraints(prop_name, value, prop_def))

        return errors

    def _validate_type(self, prop_name: str, value: Any, expected_type: PropertyType) -> dict[str, str] | None:
        """Validate the type of a value.

        Args:
            prop_name: The name of the property.
            value: The value to validate.
            expected_type: The expected PropertyType.

        Returns:
            Error dictionary if type is invalid, None otherwise.
        """
        type_valid = False

        if expected_type == PropertyType.STRING:
            type_valid = isinstance(value, str)
        elif expected_type == PropertyType.INTEGER:
            # IMPORTANT: bool is subtype of int in Python, so we must exclude it
            type_valid = isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == PropertyType.FLOAT:
            # Accept both int and float for float fields (int is implicitly convertible)
            type_valid = isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == PropertyType.BOOLEAN:
            type_valid = isinstance(value, bool)
        elif expected_type == PropertyType.DATE:
            # Accept date, datetime, or ISO date string
            type_valid = isinstance(value, (date, datetime)) or (
                isinstance(value, str) and self._is_valid_date_string(value)
            )

        if not type_valid:
            return {
                "field": prop_name,
                "message": f"Property '{prop_name}' must be of type {expected_type.value}, got {type(value).__name__}",
            }

        return None

    def _is_valid_date_string(self, value: str) -> bool:
        """Check if a string is a valid ISO date format.

        Args:
            value: The string to check.

        Returns:
            True if valid date string, False otherwise.
        """
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False

    def _validate_string_constraints(
        self, prop_name: str, value: str, prop_def: PropertyDefinition
    ) -> list[dict[str, str]]:
        """Validate string-specific constraints.

        Args:
            prop_name: The name of the property.
            value: The string value to validate.
            prop_def: The property definition containing constraints.

        Returns:
            List of error dictionaries for constraint violations.
        """
        errors: list[dict[str, str]] = []

        # Min length validation
        if prop_def.min_length is not None and len(value) < prop_def.min_length:
            errors.append(
                {
                    "field": prop_name,
                    "message": f"Property '{prop_name}' must be at least "
                    f"{prop_def.min_length} characters, got {len(value)}",
                }
            )

        # Max length validation
        if prop_def.max_length is not None and len(value) > prop_def.max_length:
            errors.append(
                {
                    "field": prop_name,
                    "message": f"Property '{prop_name}' must be at most "
                    f"{prop_def.max_length} characters, got {len(value)}",
                }
            )

        # Pattern validation
        if prop_def.pattern is not None and not re.match(prop_def.pattern, value):
            errors.append(
                {
                    "field": prop_name,
                    "message": f"Property '{prop_name}' does not match pattern '{prop_def.pattern}'",
                }
            )

        # Enum validation
        if prop_def.enum is not None and value not in prop_def.enum:
            errors.append(
                {
                    "field": prop_name,
                    "message": f"Property '{prop_name}' must be one of {prop_def.enum}, got '{value}'",
                }
            )

        return errors

    def _validate_numeric_constraints(
        self, prop_name: str, value: int | float, prop_def: PropertyDefinition
    ) -> list[dict[str, str]]:
        """Validate numeric constraints (min_value, max_value).

        Args:
            prop_name: The name of the property.
            value: The numeric value to validate.
            prop_def: The property definition containing constraints.

        Returns:
            List of error dictionaries for constraint violations.
        """
        errors: list[dict[str, str]] = []

        # Min value validation
        if prop_def.min_value is not None and value < prop_def.min_value:
            errors.append(
                {
                    "field": prop_name,
                    "message": f"Property '{prop_name}' must be at least {prop_def.min_value}, got {value}",
                }
            )

        # Max value validation
        if prop_def.max_value is not None and value > prop_def.max_value:
            errors.append(
                {
                    "field": prop_name,
                    "message": f"Property '{prop_name}' must be at most {prop_def.max_value}, got {value}",
                }
            )

        return errors

    def _run_custom_validators(self, properties: dict[str, Any], entity_type: EntityType) -> list[dict[str, str]]:
        """Run custom validators defined in the entity type.

        Args:
            properties: The properties to validate.
            entity_type: The entity type containing custom validator names.

        Returns:
            List of error dictionaries from custom validators.
        """
        errors: list[dict[str, str]] = []

        # Skip if no registry available
        if self._validator_registry is None:
            return errors

        for validator_name in entity_type.custom_validators:
            validator = self._validator_registry.get(validator_name)

            if validator is None:
                errors.append(
                    {
                        "field": "_custom_validator",
                        "message": f"Unknown custom validator: '{validator_name}'",
                    }
                )
                continue

            # Run the validator
            validator_errors = validator.validate(properties, entity_type)
            for error_msg in validator_errors:
                errors.append(
                    {
                        "field": "_custom_validator",
                        "message": error_msg,
                    }
                )

        return errors
