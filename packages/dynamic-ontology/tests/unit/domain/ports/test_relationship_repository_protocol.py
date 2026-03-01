"""Unit tests for RelationshipRepository batch method signatures."""

from typing import Any

from dynamic_ontology.domain.models.batch import BatchResult
from dynamic_ontology.domain.models.relationship import Relationship
from dynamic_ontology.domain.ports.repository import RelationshipRepository


class FakeRelationshipRepository:
    """Fake implementation of RelationshipRepository for protocol compliance testing."""

    async def create(self, relationship: Relationship) -> Relationship:
        return relationship

    async def get_by_id(
        self,
        relationship_id: str,
        at_time: str | None = None,
    ) -> Relationship | None:
        return None

    async def list_by_entity(
        self,
        entity_id: str,
        relationship_type: str | None = None,
        direction: str = "both",
        limit: int = 100,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[Relationship], int]:
        return [], 0

    async def update(self, relationship: Relationship, current_version: int) -> Relationship:
        return relationship

    async def delete(self, relationship_id: str) -> bool:
        return True

    async def get_history(self, relationship_id: str) -> list[dict[str, Any]]:
        return []

    async def create_many(self, relationships: list[Relationship]) -> BatchResult:
        return BatchResult(
            success=True,
            total=len(relationships),
            succeeded=len(relationships),
            failed=0,
            entity_ids=[],
            errors=[],
        )

    async def update_many(self, updates: list[tuple[Relationship, int]]) -> BatchResult:
        return BatchResult(
            success=True,
            total=len(updates),
            succeeded=len(updates),
            failed=0,
            entity_ids=[],
            errors=[],
        )

    async def list_all(
        self,
        type_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        cursor: str | None = None,
    ) -> tuple[list[Relationship], int]:
        return [], 0

    async def list_by_type(
        self,
        type_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Relationship], int]:
        return [], 0

    async def delete_many(self, relationship_ids: list[str]) -> BatchResult:
        return BatchResult(
            success=True,
            total=len(relationship_ids),
            succeeded=len(relationship_ids),
            failed=0,
            entity_ids=[],
            errors=[],
        )

    async def exists_by_pair(
        self,
        type_id: str,
        from_entity_id: str,
        to_entity_id: str,
    ) -> bool:
        return False


class TestRelationshipRepositoryProtocol:
    """Tests for RelationshipRepository batch method signatures."""

    def test_fake_is_instance_of_protocol(self) -> None:
        """FakeRelationshipRepository satisfies the RelationshipRepository protocol."""
        repo = FakeRelationshipRepository()
        assert isinstance(repo, RelationshipRepository)

    def test_create_many_exists(self) -> None:
        """RelationshipRepository defines create_many method."""
        assert hasattr(RelationshipRepository, "create_many")

    def test_update_many_exists(self) -> None:
        """RelationshipRepository defines update_many method."""
        assert hasattr(RelationshipRepository, "update_many")

    def test_delete_many_exists(self) -> None:
        """RelationshipRepository defines delete_many method."""
        assert hasattr(RelationshipRepository, "delete_many")
