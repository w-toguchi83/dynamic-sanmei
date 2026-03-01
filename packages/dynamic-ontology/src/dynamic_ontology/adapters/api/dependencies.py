"""動的オントロジー API 依存関数."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from dynamic_ontology.adapters.persistence.postgresql import (
    DatabaseSessionManager,
    PostgresEntityRepository,
    PostgresEntityTypeRepository,
    PostgresRelationshipRepository,
    PostgresRelationshipTypeRepository,
    PostgresSchemaVersionRepository,
    PostgresUnitOfWork,
)
from dynamic_ontology.domain.ports.repository import (
    EntityRepository,
    EntityTypeRepository,
    RelationshipRepository,
    RelationshipTypeRepository,
)
from dynamic_ontology.domain.ports.schema_version_repository import SchemaVersionRepository
from dynamic_ontology.domain.ports.unit_of_work import UnitOfWork
from dynamic_ontology.domain.services.query_engine import QueryEngine
from dynamic_ontology.domain.services.validation import ValidationEngine


def get_session_manager(request: Request) -> DatabaseSessionManager:
    """アプリケーションの SessionManager を取得."""
    return request.app.state.ontology_session_manager


async def get_db_session(
    session_manager: Annotated[DatabaseSessionManager, Depends(get_session_manager)],
) -> AsyncGenerator[AsyncSession]:
    """リクエストスコープの DB セッション."""
    async with session_manager.session() as session:
        yield session


_DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_namespace_id(request: Request) -> str:
    """namespace_id を取得する依存関数.

    デフォルトでは X-Namespace-Id ヘッダーから取得。
    アプリ側でオーバーライド可能。
    """
    namespace_id = request.headers.get("X-Namespace-Id", "default")
    return namespace_id


_NamespaceId = Annotated[str, Depends(get_namespace_id)]


async def get_unit_of_work(session: _DbSession) -> UnitOfWork:
    """UnitOfWork を取得する."""
    return PostgresUnitOfWork(session)


UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]


async def get_entity_repository(session: _DbSession, namespace_id: _NamespaceId) -> EntityRepository:
    """EntityRepository を取得する."""
    return PostgresEntityRepository(session, namespace_id)


async def get_entity_type_repository(session: _DbSession, namespace_id: _NamespaceId) -> EntityTypeRepository:
    """EntityTypeRepository を取得する."""
    return PostgresEntityTypeRepository(session, namespace_id)


async def get_relationship_repository(session: _DbSession, namespace_id: _NamespaceId) -> RelationshipRepository:
    """RelationshipRepository を取得する."""
    return PostgresRelationshipRepository(session, namespace_id)


async def get_relationship_type_repository(
    session: _DbSession, namespace_id: _NamespaceId
) -> RelationshipTypeRepository:
    """RelationshipTypeRepository を取得する."""
    return PostgresRelationshipTypeRepository(session, namespace_id)


async def get_schema_version_repository(session: _DbSession, namespace_id: _NamespaceId) -> SchemaVersionRepository:
    """SchemaVersionRepository を取得する."""
    return PostgresSchemaVersionRepository(session, namespace_id)


async def get_query_engine(session: _DbSession, namespace_id: _NamespaceId) -> QueryEngine:
    """QueryEngine を取得する."""
    return QueryEngine(session, namespace_id)


async def get_validation_engine(request: Request) -> ValidationEngine:
    """ValidationEngine を取得."""
    registry = getattr(request.app.state, "ontology_validator_registry", None)
    return ValidationEngine(registry)
