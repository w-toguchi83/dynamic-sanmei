"""Registry for custom validators."""

from dynamic_ontology.domain.ports.validator import CustomValidator


class ValidatorRegistry:
    """Registry for managing custom validators.

    Provides registration, lookup, and listing of validators by name.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._validators: dict[str, CustomValidator] = {}

    def register(self, validator: CustomValidator) -> None:
        """Register a custom validator.

        Args:
            validator: The validator to register.

        Raises:
            ValueError: If a validator with the same name is already registered.
        """
        name = validator.name
        if name in self._validators:
            raise ValueError(f"Validator '{name}' is already registered")
        self._validators[name] = validator

    def unregister(self, name: str) -> None:
        """Unregister a validator by name.

        Args:
            name: The name of the validator to unregister.

        Raises:
            KeyError: If no validator with the given name is registered.
        """
        if name not in self._validators:
            raise KeyError(f"Validator '{name}' is not registered")
        del self._validators[name]

    def get(self, name: str) -> CustomValidator | None:
        """Get a validator by name.

        Args:
            name: The name of the validator to get.

        Returns:
            The validator if found, None otherwise.
        """
        return self._validators.get(name)

    def list_all(self) -> list[str]:
        """List all registered validator names.

        Returns:
            List of registered validator names.
        """
        return list(self._validators.keys())
