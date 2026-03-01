"""動的オントロジーエンジン セットアップ."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request

from dynamic_ontology.adapters.persistence.postgresql import DatabaseSessionManager
from dynamic_ontology.domain.exceptions import (
    DomainException,
    DuplicateRelationshipError,
    EntityNotFoundError,
    ValidationError,
    VersionConflictError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """ドメイン例外を HTTP レスポンスに変換するハンドラを登録する."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(
        _request: Request, exc: EntityNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        _request: Request, exc: ValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "errors": exc.errors},
        )

    @app.exception_handler(VersionConflictError)
    async def version_conflict_handler(
        _request: Request, exc: VersionConflictError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DuplicateRelationshipError)
    async def duplicate_relationship_handler(
        _request: Request, exc: DuplicateRelationshipError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DomainException)
    async def domain_exception_handler(
        _request: Request, exc: DomainException,
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})


def create_ontology_router(
    database_url: str,
    namespace_id: str = "default",
) -> APIRouter:
    """動的オントロジー API ルーターを作成してマウント用に返す.

    Args:
        database_url: PostgreSQL 接続 URL
        namespace_id: 固定 namespace_id（シングルテナント用）

    Returns:
        FastAPI APIRouter
    """
    from dynamic_ontology.adapters.api.routes.entities import router as entities_router
    from dynamic_ontology.adapters.api.routes.entity_types import router as entity_types_router
    from dynamic_ontology.adapters.api.routes.query import router as query_router
    from dynamic_ontology.adapters.api.routes.relationship_types import (
        router as relationship_types_router,
    )
    from dynamic_ontology.adapters.api.routes.relationships import router as relationships_router
    from dynamic_ontology.adapters.api.routes.schema_versions import (
        router as schema_versions_router,
    )

    router = APIRouter()
    router.include_router(entities_router)
    router.include_router(entity_types_router)
    router.include_router(relationships_router)
    router.include_router(relationship_types_router)
    router.include_router(query_router)
    router.include_router(schema_versions_router)

    return router


async def create_ontology_session(database_url: str) -> DatabaseSessionManager:
    """DatabaseSessionManager を作成して初期化.

    Args:
        database_url: PostgreSQL 接続 URL

    Returns:
        初期化済み DatabaseSessionManager
    """
    manager = DatabaseSessionManager()
    manager.init(database_url)
    return manager
