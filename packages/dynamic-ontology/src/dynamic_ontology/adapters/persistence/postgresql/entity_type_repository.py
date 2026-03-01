"""PostgreSQL repository implementation for EntityType."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.domain.exceptions import EntityNotFoundError, ValidationError
from dynamic_ontology.domain.models.entity_type import EntityType, PropertyDefinition, PropertyType


class PostgresEntityTypeRepository:
    """PostgreSQL implementation of EntityTypeRepository."""

    def __init__(self, session: AsyncSession, namespace_id: str) -> None:
        """Initialize with database session and namespace ID.

        Args:
            session: SQLAlchemy async session for database operations.
            namespace_id: ネームスペース識別子.
        """
        self._session = session
        self._namespace_id = namespace_id

    @property
    def _namespace_where(self) -> str:
        """namespace_id 条件の WHERE 句."""
        return "WHERE namespace_id = :namespace_id"

    @property
    def _namespace_and(self) -> str:
        """namespace_id 条件の AND 句."""
        return "AND namespace_id = :namespace_id"

    def _with_namespace(self, params: dict[str, object]) -> dict[str, object]:
        """パラメータに namespace_id を追加."""
        return {**params, "namespace_id": self._namespace_id}

    async def create(self, entity_type: EntityType) -> EntityType:
        """Create a new entity type.

        Args:
            entity_type: The entity type domain model to persist.

        Returns:
            The created entity type with timestamps from the database.
        """
        namespace_id = self._namespace_id
        schema_definition = self._to_schema_definition(entity_type)

        query = text("""
            INSERT INTO do_entity_types (id, namespace_id, name, description, schema_definition, display_property, created_at, updated_at)
            VALUES (:id, :namespace_id, :name, :description, :schema_definition, :display_property, :created_at, :updated_at)
            RETURNING id, name, description, schema_definition, display_property, created_at, updated_at
        """)

        try:
            result = await self._session.execute(
                query,
                {
                    "id": str(entity_type.id),
                    "namespace_id": namespace_id,
                    "name": entity_type.name,
                    "description": entity_type.description,
                    "schema_definition": json.dumps(schema_definition),
                    "display_property": entity_type.display_property,
                    "created_at": entity_type.created_at,
                    "updated_at": entity_type.updated_at,
                },
            )
        except IntegrityError as e:
            error_str = str(e)
            if (
                "entity_types_name_key" in error_str
                or "uq_entity_types_namespace_name" in error_str
                or "uq_do_entity_types_namespace_name" in error_str
            ):
                raise ValidationError(
                    [
                        {
                            "field": "name",
                            "message": f"EntityType with name '{entity_type.name}' already exists",
                        }
                    ]
                ) from None
            raise

        row = result.fetchone()
        if row is None:
            raise RuntimeError("Failed to create entity type")

        return self._row_to_entity_type(row)

    async def get_by_id(self, entity_type_id: str) -> EntityType | None:
        """Get entity type by ID.

        Args:
            entity_type_id: The UUID string of the entity type.

        Returns:
            The entity type if found, None otherwise.
        """
        query = text(f"""
            SELECT id, name, description, schema_definition, display_property, created_at, updated_at
            FROM do_entity_types
            WHERE id = :id {self._namespace_and}
        """)

        result = await self._session.execute(query, self._with_namespace({"id": entity_type_id}))
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_entity_type(row)

    async def get_by_name(self, name: str) -> EntityType | None:
        """Get entity type by name.

        Args:
            name: The unique name of the entity type.

        Returns:
            The entity type if found, None otherwise.
        """
        query = text(f"""
            SELECT id, name, description, schema_definition, display_property, created_at, updated_at
            FROM do_entity_types
            WHERE name = :name {self._namespace_and}
        """)

        result = await self._session.execute(query, self._with_namespace({"name": name}))
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_entity_type(row)

    async def list_all(self) -> list[EntityType]:
        """List all entity types.

        Returns:
            List of all entity types ordered by name.
        """
        query = text(f"""
            SELECT id, name, description, schema_definition, display_property, created_at, updated_at
            FROM do_entity_types
            {self._namespace_where}
            ORDER BY name
        """)

        result = await self._session.execute(query, self._with_namespace({}))
        rows = result.fetchall()

        return [self._row_to_entity_type(row) for row in rows]

    async def update(self, entity_type: EntityType) -> EntityType:
        """Update an existing entity type.

        Args:
            entity_type: The entity type with updated values.

        Returns:
            The updated entity type.
        """
        namespace_id = self._namespace_id
        schema_definition = self._to_schema_definition(entity_type)

        query = text("""
            UPDATE do_entity_types
            SET name = :name,
                description = :description,
                schema_definition = :schema_definition,
                display_property = :display_property,
                updated_at = :updated_at
            WHERE id = :id AND namespace_id = :namespace_id
            RETURNING id, name, description, schema_definition, display_property, created_at, updated_at
        """)

        try:
            result = await self._session.execute(
                query,
                {
                    "id": str(entity_type.id),
                    "namespace_id": namespace_id,
                    "name": entity_type.name,
                    "description": entity_type.description,
                    "schema_definition": json.dumps(schema_definition),
                    "display_property": entity_type.display_property,
                    "updated_at": datetime.now(UTC),
                },
            )
        except IntegrityError as e:
            error_str = str(e)
            if (
                "entity_types_name_key" in error_str
                or "uq_entity_types_namespace_name" in error_str
                or "uq_do_entity_types_namespace_name" in error_str
            ):
                raise ValidationError(
                    [
                        {
                            "field": "name",
                            "message": f"EntityType with name '{entity_type.name}' already exists",
                        }
                    ]
                ) from None
            raise

        row = result.fetchone()
        if row is None:
            raise EntityNotFoundError(str(entity_type.id), "EntityType")

        return self._row_to_entity_type(row)

    async def delete(self, entity_type_id: str) -> bool:
        """Delete an entity type.

        Args:
            entity_type_id: The UUID string of the entity type to delete.

        Returns:
            True if deleted, False if not found.
        """
        namespace_id = self._namespace_id
        query = text("""
            DELETE FROM do_entity_types
            WHERE id = :id AND namespace_id = :namespace_id
            RETURNING id
        """)

        result = await self._session.execute(
            query, {"id": entity_type_id, "namespace_id": namespace_id}
        )
        row = result.fetchone()

        return row is not None

    def _to_schema_definition(self, entity_type: EntityType) -> dict[str, Any]:
        """Convert EntityType properties to JSONB schema definition.

        Args:
            entity_type: The entity type to convert.

        Returns:
            Dictionary suitable for JSONB storage.
        """
        properties: dict[str, dict[str, Any]] = {}

        for prop_name, prop_def in entity_type.properties.items():
            prop_dict: dict[str, Any] = {
                "type": prop_def.type.value,
                "required": prop_def.required,
                "indexed": prop_def.indexed,
            }

            if prop_def.default is not None:
                prop_dict["default"] = prop_def.default

            # String constraints
            if prop_def.min_length is not None:
                prop_dict["min_length"] = prop_def.min_length
            if prop_def.max_length is not None:
                prop_dict["max_length"] = prop_def.max_length
            if prop_def.pattern is not None:
                prop_dict["pattern"] = prop_def.pattern
            if prop_def.enum is not None:
                prop_dict["enum"] = prop_def.enum

            # Numeric constraints
            if prop_def.min_value is not None:
                prop_dict["min_value"] = prop_def.min_value
            if prop_def.max_value is not None:
                prop_dict["max_value"] = prop_def.max_value

            # State transition constraints
            if prop_def.state_transitions is not None:
                prop_dict["state_transitions"] = prop_def.state_transitions

            properties[prop_name] = prop_dict

        return {
            "properties": properties,
            "custom_validators": entity_type.custom_validators,
        }

    def _row_to_entity_type(self, row: Any) -> EntityType:
        """Convert database row to EntityType domain model.

        Args:
            row: Database row with entity type data.

        Returns:
            EntityType domain model.
        """
        # Handle both dict-like and tuple-like row access
        if hasattr(row, "_mapping"):
            # SQLAlchemy Row object
            row_dict = dict(row._mapping)
        else:
            # Named tuple or similar
            row_dict = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "schema_definition": row[3],
                "display_property": row[4],
                "created_at": row[5],
                "updated_at": row[6],
            }

        schema_def = row_dict["schema_definition"]
        if isinstance(schema_def, str):
            schema_def = json.loads(schema_def)

        properties: dict[str, PropertyDefinition] = {}
        for prop_name, prop_data in schema_def.get("properties", {}).items():
            properties[prop_name] = PropertyDefinition(
                type=PropertyType(prop_data["type"]),
                required=prop_data["required"],
                indexed=prop_data.get("indexed", False),
                default=prop_data.get("default"),
                min_length=prop_data.get("min_length"),
                max_length=prop_data.get("max_length"),
                pattern=prop_data.get("pattern"),
                enum=prop_data.get("enum"),
                min_value=prop_data.get("min_value"),
                max_value=prop_data.get("max_value"),
                state_transitions=prop_data.get("state_transitions"),
            )

        # Parse UUID if it's a string
        entity_id = row_dict["id"]
        if isinstance(entity_id, str):
            entity_id = UUID(entity_id)

        return EntityType(
            id=entity_id,
            name=row_dict["name"],
            description=row_dict["description"] or "",
            properties=properties,
            custom_validators=schema_def.get("custom_validators", []),
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
            display_property=row_dict.get("display_property"),
        )
