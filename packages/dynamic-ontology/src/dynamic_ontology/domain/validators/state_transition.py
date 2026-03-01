"""State transition validator for entity property state constraints."""

from typing import Any

from dynamic_ontology.domain.models.entity_type import EntityType


class StateTransitionValidator:
    """Validates state transition constraints on entity properties.

    Unlike CustomValidator (which takes a single properties dict),
    this validator requires both old and new properties to compare
    state changes. It is used internally by ValidationEngine during
    entity updates, not registered as a custom validator.
    """

    def validate(
        self,
        old_properties: dict[str, Any],
        new_properties: dict[str, Any],
        entity_type: EntityType,
    ) -> list[str]:
        """Validate state transitions for all properties with constraints.

        Args:
            old_properties: The properties before the update.
            new_properties: The properties after the update.
            entity_type: The entity type with property definitions.

        Returns:
            List of error messages. Empty if all transitions are valid.
        """
        errors: list[str] = []

        for prop_name, prop_def in entity_type.properties.items():
            # Skip properties without state transition constraints
            if prop_def.state_transitions is None:
                continue

            # Skip if property missing from either old or new properties
            if prop_name not in old_properties or prop_name not in new_properties:
                continue

            old_value = old_properties[prop_name]
            new_value = new_properties[prop_name]

            # Skip if value unchanged
            if old_value == new_value:
                continue

            # Skip if old value is None (initial setting)
            if old_value is None:
                continue

            # Skip if new value is None (field clear)
            if new_value is None:
                continue

            # Skip if old value not in the transitions map (unknown state)
            if old_value not in prop_def.state_transitions:
                continue

            # Check if the transition is allowed
            allowed_targets = prop_def.state_transitions[old_value]
            if new_value not in allowed_targets:
                if len(allowed_targets) == 0:
                    errors.append(
                        f"State transition not allowed for '{prop_name}': "
                        f"'{old_value}' -> '{new_value}'. "
                        f"No transitions allowed from '{old_value}'"
                    )
                else:
                    allowed_str = ", ".join(f"'{t}'" for t in allowed_targets)
                    errors.append(
                        f"State transition not allowed for '{prop_name}': "
                        f"'{old_value}' -> '{new_value}'. "
                        f"Allowed transitions from '{old_value}': [{allowed_str}]"
                    )

        return errors
