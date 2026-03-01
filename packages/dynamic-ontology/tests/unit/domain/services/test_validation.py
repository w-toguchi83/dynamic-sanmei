"""Test ValidationEngine for property validation."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from dynamic_ontology.domain.exceptions import ValidationError
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType
from dynamic_ontology.domain.services.validation import ValidationEngine
from dynamic_ontology.domain.services.validator_registry import ValidatorRegistry
from dynamic_ontology.domain.validators.date_range import DateRangeValidator


@pytest.fixture
def validation_engine() -> ValidationEngine:
    """Create ValidationEngine instance."""
    return ValidationEngine()


@pytest.fixture
def task_entity_type() -> EntityType:
    """Create a sample Task entity type for testing."""
    return EntityType(
        id=uuid4(),
        name="Task",
        description="A task entity",
        properties={
            "title": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                min_length=1,
                max_length=100,
            ),
            "description": PropertyDefinition(
                type=PropertyType.STRING,
                required=False,
                default="No description",
            ),
            "priority": PropertyDefinition(
                type=PropertyType.INTEGER,
                required=True,
                min_value=1,
                max_value=5,
            ),
            "progress": PropertyDefinition(
                type=PropertyType.FLOAT,
                required=False,
                min_value=0.0,
                max_value=100.0,
            ),
            "is_completed": PropertyDefinition(
                type=PropertyType.BOOLEAN,
                required=False,
                default=False,
            ),
            "due_date": PropertyDefinition(
                type=PropertyType.DATE,
                required=False,
            ),
            "status": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
                enum=["pending", "in_progress", "completed"],
            ),
            "tags": PropertyDefinition(
                type=PropertyType.STRING,
                required=False,
                pattern=r"^[a-z]+(-[a-z]+)*$",
            ),
        },
        custom_validators=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestValidateValidProperties:
    """Test validation of valid properties."""

    def test_validate_valid_properties(self, validation_engine: ValidationEngine, task_entity_type: EntityType) -> None:
        """Test that valid properties pass validation without raising errors."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
        }

        # Should not raise any exception
        validation_engine.validate(properties, task_entity_type)

    def test_validate_valid_properties_with_all_fields(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test validation with all fields including optional ones."""
        properties = {
            "title": "My Task",
            "description": "A detailed description",
            "priority": 3,
            "progress": 50.5,
            "is_completed": False,
            "due_date": "2025-12-31",
            "status": "in_progress",
            "tags": "work-urgent",
        }

        validation_engine.validate(properties, task_entity_type)


class TestRequiredPropertyValidation:
    """Test required property validation."""

    def test_validate_missing_required_property(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that missing required property raises ValidationError."""
        properties = {
            "priority": 3,
            "status": "pending",
            # missing 'title' which is required
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        assert len(exc_info.value.errors) >= 1
        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "title" in error_fields

    def test_validate_multiple_missing_required_properties(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that multiple missing required properties are reported."""
        properties = {
            "description": "Some description",
            # missing 'title', 'priority', and 'status' which are required
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "title" in error_fields
        assert "priority" in error_fields
        assert "status" in error_fields


class TestStringConstraintValidation:
    """Test string constraint validation."""

    def test_validate_string_min_length(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that string below min_length raises ValidationError."""
        properties = {
            "title": "",  # min_length is 1
            "priority": 3,
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "title" in error_fields

    def test_validate_string_max_length(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that string exceeding max_length raises ValidationError."""
        properties = {
            "title": "x" * 101,  # max_length is 100
            "priority": 3,
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "title" in error_fields

    def test_validate_string_pattern(self, validation_engine: ValidationEngine, task_entity_type: EntityType) -> None:
        """Test that string not matching pattern raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            "tags": "INVALID_TAG",  # pattern requires lowercase with hyphens
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "tags" in error_fields


class TestNumericConstraintValidation:
    """Test numeric constraint validation."""

    def test_validate_integer_min_value(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that integer below min_value raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": 0,  # min_value is 1
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "priority" in error_fields

    def test_validate_integer_max_value(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that integer exceeding max_value raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": 10,  # max_value is 5
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "priority" in error_fields

    def test_validate_float_min_value(self, validation_engine: ValidationEngine, task_entity_type: EntityType) -> None:
        """Test that float below min_value raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            "progress": -1.0,  # min_value is 0.0
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "progress" in error_fields

    def test_validate_float_max_value(self, validation_engine: ValidationEngine, task_entity_type: EntityType) -> None:
        """Test that float exceeding max_value raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            "progress": 150.0,  # max_value is 100.0
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "progress" in error_fields


class TestEnumValidation:
    """Test enum constraint validation."""

    def test_validate_enum_invalid_value(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that value not in enum raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "invalid_status",  # enum is ['pending', 'in_progress', 'completed']
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "status" in error_fields

    def test_validate_enum_valid_value(self, validation_engine: ValidationEngine, task_entity_type: EntityType) -> None:
        """Test that valid enum value passes validation."""
        for valid_status in ["pending", "in_progress", "completed"]:
            properties = {
                "title": "My Task",
                "priority": 3,
                "status": valid_status,
            }
            validation_engine.validate(properties, task_entity_type)


class TestTypeValidation:
    """Test type validation."""

    def test_validate_wrong_type_string_expected(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that wrong type for string property raises ValidationError."""
        properties = {
            "title": 12345,  # should be string
            "priority": 3,
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "title" in error_fields

    def test_validate_wrong_type_integer_expected(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that wrong type for integer property raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": "high",  # should be integer
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "priority" in error_fields

    def test_validate_wrong_type_boolean_expected(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that wrong type for boolean property raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            "is_completed": "yes",  # should be boolean
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "is_completed" in error_fields

    def test_validate_wrong_type_float_expected(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that wrong type for float property raises ValidationError."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            "progress": "half",  # should be float
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "progress" in error_fields

    def test_validate_bool_not_accepted_as_integer(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that boolean is NOT accepted for integer property.

        IMPORTANT: In Python, bool is a subtype of int, so isinstance(True, int)
        returns True. However, semantically we should reject booleans for integer fields.
        """
        properties = {
            "title": "My Task",
            "priority": True,  # bool should not be accepted for integer
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "priority" in error_fields


class TestDefaultValues:
    """Test default value application."""

    def test_validate_applies_default_values(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that missing optional properties get default values applied."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
        }

        result = validation_engine.validate_and_apply_defaults(properties, task_entity_type)

        assert result["title"] == "My Task"
        assert result["priority"] == 3
        assert result["status"] == "pending"
        assert result["description"] == "No description"  # default value
        assert result["is_completed"] is False  # default value

    def test_validate_does_not_override_provided_values(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that provided values are not overridden by defaults."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            "description": "Custom description",
            "is_completed": True,
        }

        result = validation_engine.validate_and_apply_defaults(properties, task_entity_type)

        assert result["description"] == "Custom description"
        assert result["is_completed"] is True


class TestOptionalProperties:
    """Test optional property validation."""

    def test_validate_optional_property_can_be_none(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that optional properties can be explicitly set to None."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            "description": None,  # optional, explicitly None
            "progress": None,  # optional, explicitly None
            "due_date": None,  # optional, explicitly None
        }

        # Should not raise any exception
        validation_engine.validate(properties, task_entity_type)

    def test_validate_optional_property_can_be_omitted(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that optional properties can be completely omitted."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            # all optional properties omitted
        }

        validation_engine.validate(properties, task_entity_type)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_validate_empty_string_respects_min_length(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that empty string fails when min_length > 0."""
        properties = {
            "title": "",
            "priority": 3,
            "status": "pending",
        }

        with pytest.raises(ValidationError):
            validation_engine.validate(properties, task_entity_type)

    def test_validate_boundary_values_pass(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that boundary values (exactly at min/max) pass validation."""
        properties = {
            "title": "x",  # exactly min_length=1
            "priority": 1,  # exactly min_value
            "status": "pending",
            "progress": 100.0,  # exactly max_value
        }

        validation_engine.validate(properties, task_entity_type)

    def test_validate_integer_accepts_int_not_float(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that integer field rejects float values."""
        properties = {
            "title": "My Task",
            "priority": 3.5,  # should be int, not float
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            validation_engine.validate(properties, task_entity_type)

        error_fields = [e["field"] for e in exc_info.value.errors]
        assert "priority" in error_fields

    def test_validate_float_accepts_int(
        self, validation_engine: ValidationEngine, task_entity_type: EntityType
    ) -> None:
        """Test that float field accepts integer values."""
        properties = {
            "title": "My Task",
            "priority": 3,
            "status": "pending",
            "progress": 50,  # int is acceptable for float field
        }

        validation_engine.validate(properties, task_entity_type)


@pytest.fixture
def validator_registry() -> ValidatorRegistry:
    """Create ValidatorRegistry with built-in validators."""
    registry = ValidatorRegistry()
    registry.register(DateRangeValidator(start_field="start_date", end_field="due_date"))
    return registry


@pytest.fixture
def task_with_custom_validators() -> EntityType:
    """Create a Task entity type with custom validators."""
    return EntityType(
        id=uuid4(),
        name="TaskWithValidators",
        description="A task with custom validators",
        properties={
            "title": PropertyDefinition(
                type=PropertyType.STRING,
                required=True,
            ),
            "start_date": PropertyDefinition(
                type=PropertyType.DATE,
                required=False,
            ),
            "due_date": PropertyDefinition(
                type=PropertyType.DATE,
                required=False,
            ),
        },
        custom_validators=["date_range:start_date:due_date"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestCustomValidatorIntegration:
    """Test ValidationEngine with custom validators."""

    def test_custom_validator_passes_when_valid(
        self,
        validator_registry: ValidatorRegistry,
        task_with_custom_validators: EntityType,
    ) -> None:
        """Test that custom validator passes with valid data."""
        engine = ValidationEngine(validator_registry)
        properties = {
            "title": "My Task",
            "start_date": "2025-01-01",
            "due_date": "2025-12-31",
        }

        # Should not raise
        engine.validate(properties, task_with_custom_validators)

    def test_custom_validator_fails_when_invalid(
        self,
        validator_registry: ValidatorRegistry,
        task_with_custom_validators: EntityType,
    ) -> None:
        """Test that custom validator fails with invalid data."""
        engine = ValidationEngine(validator_registry)
        properties = {
            "title": "My Task",
            "start_date": "2025-12-31",
            "due_date": "2025-01-01",  # Before start_date
        }

        with pytest.raises(ValidationError) as exc_info:
            engine.validate(properties, task_with_custom_validators)

        # Check error contains custom validator message
        error_messages = [e["message"] for e in exc_info.value.errors]
        assert any("due_date" in msg and "start_date" in msg for msg in error_messages)

    def test_custom_validator_unknown_validator_raises_error(
        self,
        validator_registry: ValidatorRegistry,
    ) -> None:
        """Test that unknown custom validator name raises error."""
        engine = ValidationEngine(validator_registry)
        entity_type = EntityType(
            id=uuid4(),
            name="BadEntity",
            description="Entity with unknown validator",
            properties={
                "title": PropertyDefinition(type=PropertyType.STRING, required=True),
            },
            custom_validators=["unknown_validator"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        properties = {"title": "Test"}

        with pytest.raises(ValidationError) as exc_info:
            engine.validate(properties, entity_type)

        error_messages = [e["message"] for e in exc_info.value.errors]
        assert any("unknown_validator" in msg for msg in error_messages)

    def test_validation_engine_without_registry_skips_custom_validators(
        self,
        task_with_custom_validators: EntityType,
    ) -> None:
        """Test that validation without registry skips custom validators."""
        engine = ValidationEngine()  # No registry
        properties = {
            "title": "My Task",
            "start_date": "2025-12-31",
            "due_date": "2025-01-01",  # Invalid but should pass without registry
        }

        # Should not raise because custom validators are skipped
        engine.validate(properties, task_with_custom_validators)

    def test_multiple_custom_validators_all_run(
        self,
    ) -> None:
        """Test that multiple custom validators all run."""
        registry = ValidatorRegistry()
        registry.register(DateRangeValidator(start_field="start_date", end_field="due_date"))
        registry.register(DateRangeValidator(start_field="created_at", end_field="updated_at"))

        engine = ValidationEngine(registry)
        entity_type = EntityType(
            id=uuid4(),
            name="MultiValidator",
            description="Entity with multiple validators",
            properties={
                "title": PropertyDefinition(type=PropertyType.STRING, required=True),
                "start_date": PropertyDefinition(type=PropertyType.DATE, required=False),
                "due_date": PropertyDefinition(type=PropertyType.DATE, required=False),
                "created_at": PropertyDefinition(type=PropertyType.DATE, required=False),
                "updated_at": PropertyDefinition(type=PropertyType.DATE, required=False),
            },
            custom_validators=[
                "date_range:start_date:due_date",
                "date_range:created_at:updated_at",
            ],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Both date ranges are invalid
        properties = {
            "title": "Test",
            "start_date": "2025-12-31",
            "due_date": "2025-01-01",
            "created_at": "2025-12-31",
            "updated_at": "2025-01-01",
        }

        with pytest.raises(ValidationError) as exc_info:
            engine.validate(properties, entity_type)

        # Should have 2 errors from custom validators
        assert len(exc_info.value.errors) == 2


class TestValidationEngineStateTransitions:
    """ValidationEngine の状態遷移チェック統合テスト."""

    def _make_entity_type_with_transitions(self) -> EntityType:
        return EntityType(
            id=uuid4(),
            name=f"order_{uuid4().hex[:8]}",
            description="test",
            properties={
                "status": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                    enum=["draft", "published", "archived"],
                    state_transitions={
                        "draft": ["published"],
                        "published": ["archived"],
                        "archived": [],
                    },
                ),
                "title": PropertyDefinition(
                    type=PropertyType.STRING,
                    required=True,
                ),
            },
            custom_validators=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_allowed_transition_passes_validation(self) -> None:
        """許可された状態遷移はバリデーションを通過する."""
        engine = ValidationEngine()
        et = self._make_entity_type_with_transitions()
        old_props: dict[str, Any] = {"status": "draft", "title": "Test"}
        new_props: dict[str, Any] = {"status": "published", "title": "Test"}
        engine.validate(new_props, et, existing_properties=old_props)

    def test_disallowed_transition_raises_validation_error(self) -> None:
        """許可されていない状態遷移は ValidationError を発生させる."""
        engine = ValidationEngine()
        et = self._make_entity_type_with_transitions()
        old_props: dict[str, Any] = {"status": "archived", "title": "Test"}
        new_props: dict[str, Any] = {"status": "draft", "title": "Test"}
        with pytest.raises(ValidationError) as exc_info:
            engine.validate(new_props, et, existing_properties=old_props)
        assert any("_state_transition" in e["field"] for e in exc_info.value.errors)

    def test_no_existing_properties_skips_transition_check(self) -> None:
        """existing_properties が None の場合、状態遷移チェックをスキップする."""
        engine = ValidationEngine()
        et = self._make_entity_type_with_transitions()
        props: dict[str, Any] = {"status": "archived", "title": "Test"}
        engine.validate(props, et)  # No existing_properties = creation

    def test_validate_and_apply_defaults_with_existing_properties(self) -> None:
        """validate_and_apply_defaults でも状態遷移チェックが実行される."""
        engine = ValidationEngine()
        et = self._make_entity_type_with_transitions()
        old_props: dict[str, Any] = {"status": "archived", "title": "Test"}
        new_props: dict[str, Any] = {"status": "draft", "title": "Test"}
        with pytest.raises(ValidationError):
            engine.validate_and_apply_defaults(new_props, et, existing_properties=old_props)
