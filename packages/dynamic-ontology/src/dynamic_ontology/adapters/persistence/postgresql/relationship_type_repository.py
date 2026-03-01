"""PostgreSQL repository implementation for RelationshipType."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.domain.exceptions import EntityNotFoundError, ValidationError
from dynamic_ontology.domain.models.entity_type import PropertyDefinition, PropertyType
from dynamic_ontology.domain.models.relationship import RelationshipType


class PostgresRelationshipTypeRepository:
    """PostgreSQL implementation of RelationshipTypeRepository."""

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

    async def create(self, relationship_type: RelationshipType) -> RelationshipType:
        """Create a new relationship type.

        Args:
            relationship_type: The relationship type domain model to persist.

        Returns:
            The created relationship type with timestamps from the database.
        """
        namespace_id = self._namespace_id
        schema_definition = self._to_schema_definition(relationship_type)

        query = text("""
            INSERT INTO do_relationship_types (
                id, namespace_id, name, description, schema_definition,
                directional, allowed_source_types, allowed_target_types,
                allow_duplicates, created_at, updated_at
            )
            VALUES (
                :id, :namespace_id, :name, :description, :schema_definition,
                :directional, :allowed_source_types, :allowed_target_types,
                :allow_duplicates, :created_at, :updated_at
            )
            RETURNING
                id, name, description, schema_definition, directional,
                allowed_source_types, allowed_target_types, allow_duplicates,
                created_at, updated_at
        """)

        try:
            result = await self._session.execute(
                query,
                {
                    "id": str(relationship_type.id),
                    "namespace_id": namespace_id,
                    "name": relationship_type.name,
                    "description": relationship_type.description,
                    "schema_definition": json.dumps(schema_definition),
                    "directional": relationship_type.directional,
                    "allowed_source_types": json.dumps([str(u) for u in relationship_type.allowed_source_types]),
                    "allowed_target_types": json.dumps([str(u) for u in relationship_type.allowed_target_types]),
                    "allow_duplicates": relationship_type.allow_duplicates,
                    "created_at": relationship_type.created_at,
                    "updated_at": relationship_type.updated_at,
                },
            )
        except IntegrityError as e:
            error_str = str(e)
            if (
                "relationship_types_name_key" in error_str
                or "uq_relationship_types_namespace_name" in error_str
                or "uq_do_relationship_types_namespace_name" in error_str
            ):
                raise ValidationError(
                    [
                        {
                            "field": "name",
                            "message": f"RelationshipType with name '{relationship_type.name}' already exists",
                        }
                    ]
                ) from None
            raise

        row = result.fetchone()
        if row is None:
            raise RuntimeError("Failed to create relationship type")

        return self._row_to_relationship_type(row)

    async def get_by_id(self, relationship_type_id: str) -> RelationshipType | None:
        """Get relationship type by ID.

        Args:
            relationship_type_id: The UUID string of the relationship type.

        Returns:
            The relationship type if found, None otherwise.
        """
        query = text(f"""
            SELECT id, name, description, schema_definition, directional, allowed_source_types, allowed_target_types, allow_duplicates, created_at, updated_at
            FROM do_relationship_types
            WHERE id = :id {self._namespace_and}
        """)

        result = await self._session.execute(query, self._with_namespace({"id": relationship_type_id}))
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_relationship_type(row)

    async def get_by_name(self, name: str) -> RelationshipType | None:
        """Get relationship type by name.

        Args:
            name: The unique name of the relationship type.

        Returns:
            The relationship type if found, None otherwise.
        """
        query = text(f"""
            SELECT id, name, description, schema_definition, directional, allowed_source_types, allowed_target_types, allow_duplicates, created_at, updated_at
            FROM do_relationship_types
            WHERE name = :name {self._namespace_and}
        """)

        result = await self._session.execute(query, self._with_namespace({"name": name}))
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_relationship_type(row)

    async def list_all(self) -> list[RelationshipType]:
        """List all relationship types.

        Returns:
            List of all relationship types ordered by name.
        """
        query = text(f"""
            SELECT id, name, description, schema_definition, directional, allowed_source_types, allowed_target_types, allow_duplicates, created_at, updated_at
            FROM do_relationship_types
            {self._namespace_where}
            ORDER BY name
        """)

        result = await self._session.execute(query, self._with_namespace({}))
        rows = result.fetchall()

        return [self._row_to_relationship_type(row) for row in rows]

    async def update(self, relationship_type: RelationshipType) -> RelationshipType:
        """Update an existing relationship type.

        Args:
            relationship_type: The relationship type with updated values.

        Returns:
            The updated relationship type.
        """
        namespace_id = self._namespace_id
        schema_definition = self._to_schema_definition(relationship_type)

        query = text("""
            UPDATE do_relationship_types
            SET name = :name,
                description = :description,
                schema_definition = :schema_definition,
                directional = :directional,
                allowed_source_types = :allowed_source_types,
                allowed_target_types = :allowed_target_types,
                allow_duplicates = :allow_duplicates,
                updated_at = :updated_at
            WHERE id = :id AND namespace_id = :namespace_id
            RETURNING id, name, description, schema_definition, directional, allowed_source_types, allowed_target_types, allow_duplicates, created_at, updated_at
        """)

        try:
            result = await self._session.execute(
                query,
                {
                    "id": str(relationship_type.id),
                    "namespace_id": namespace_id,
                    "name": relationship_type.name,
                    "description": relationship_type.description,
                    "schema_definition": json.dumps(schema_definition),
                    "directional": relationship_type.directional,
                    "allowed_source_types": json.dumps([str(u) for u in relationship_type.allowed_source_types]),
                    "allowed_target_types": json.dumps([str(u) for u in relationship_type.allowed_target_types]),
                    "allow_duplicates": relationship_type.allow_duplicates,
                    "updated_at": datetime.now(UTC),
                },
            )
        except IntegrityError as e:
            error_str = str(e)
            if (
                "relationship_types_name_key" in error_str
                or "uq_relationship_types_namespace_name" in error_str
                or "uq_do_relationship_types_namespace_name" in error_str
            ):
                raise ValidationError(
                    [
                        {
                            "field": "name",
                            "message": f"RelationshipType with name '{relationship_type.name}' already exists",
                        }
                    ]
                ) from None
            raise

        row = result.fetchone()
        if row is None:
            raise EntityNotFoundError(str(relationship_type.id), "RelationshipType")

        return self._row_to_relationship_type(row)

    async def delete(self, relationship_type_id: str) -> bool:
        """Delete a relationship type.

        Args:
            relationship_type_id: The UUID string of the relationship type to delete.

        Returns:
            True if deleted, False if not found.
        """
        namespace_id = self._namespace_id
        query = text("""
            DELETE FROM do_relationship_types
            WHERE id = :id AND namespace_id = :namespace_id
            RETURNING id
        """)

        result = await self._session.execute(query, {"id": relationship_type_id, "namespace_id": namespace_id})
        row = result.fetchone()

        return row is not None

    def _to_schema_definition(self, relationship_type: RelationshipType) -> dict[str, Any]:
        """Convert RelationshipType properties to JSONB schema definition.

        Args:
            relationship_type: The relationship type to convert.

        Returns:
            Dictionary suitable for JSONB storage.
        """
        properties: dict[str, dict[str, Any]] = {}

        for prop_name, prop_def in relationship_type.properties.items():
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
            "custom_validators": relationship_type.custom_validators,
        }

    def _row_to_relationship_type(self, row: Any) -> RelationshipType:
        """Convert database row to RelationshipType domain model.

        Args:
            row: Database row with relationship type data.

        Returns:
            RelationshipType domain model.
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
                "directional": row[4],
                "allowed_source_types": row[5],
                "allowed_target_types": row[6],
                "allow_duplicates": row[7],
                "created_at": row[9],
                "updated_at": row[10],
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
        relationship_type_id = row_dict["id"]
        if isinstance(relationship_type_id, str):
            relationship_type_id = UUID(relationship_type_id)

        # Parse allowed_source_types / allowed_target_types from JSONB
        allowed_src = row_dict.get("allowed_source_types", [])
        if isinstance(allowed_src, str):
            allowed_src = json.loads(allowed_src)
        allowed_source_types = [UUID(s) for s in (allowed_src or [])]

        allowed_tgt = row_dict.get("allowed_target_types", [])
        if isinstance(allowed_tgt, str):
            allowed_tgt = json.loads(allowed_tgt)
        allowed_target_types = [UUID(s) for s in (allowed_tgt or [])]

        return RelationshipType(
            id=relationship_type_id,
            name=row_dict["name"],
            description=row_dict["description"] or "",
            directional=row_dict["directional"],
            properties=properties,
            custom_validators=schema_def.get("custom_validators", []),
            allowed_source_types=allowed_source_types,
            allowed_target_types=allowed_target_types,
            allow_duplicates=row_dict["allow_duplicates"],
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
        )
