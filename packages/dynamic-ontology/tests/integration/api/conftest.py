"""Shared fixtures for API integration tests.

動的オントロジーパッケージの API 統合テスト用フィクスチャ。
FastAPI テストアプリを作成し、DatabaseSessionManager を設定する。
"""

import os
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager
from dynamic_ontology.setup import create_ontology_router, register_exception_handlers


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _session_db_manager():
    """セッション全体で共有する DatabaseSessionManager."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/dynamic_ontology_test",
    )
    manager = DatabaseSessionManager()
    manager.init(database_url)
    yield manager
    await manager.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _session_namespace_id() -> str:
    """セッション全体で共有する namespace_id."""
    return str(uuid4())


@pytest.fixture
async def app(_session_db_manager, _session_namespace_id):
    """Create a test FastAPI application with ontology router mounted."""
    from fastapi import FastAPI

    application = FastAPI()

    # ontology ルーターを作成してマウント
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/dynamic_ontology_test",
    )
    ontology_router = create_ontology_router(database_url=database_url)
    application.include_router(ontology_router)

    # SessionManager を app.state に設定（依存関数が参照する）
    application.state.ontology_session_manager = _session_db_manager

    # ドメイン例外 → HTTP レスポンス変換ハンドラを登録
    register_exception_handlers(application)

    yield application


@pytest.fixture
async def db_session(_session_db_manager):
    """Provide a database session for test data setup.

    Uses the session_manager to create a separate session.
    Data committed in this session is visible to the API's own sessions
    because PostgreSQL commits are durable across connections.
    """
    async with _session_db_manager.session() as session:
        yield session


@pytest.fixture
async def client(app, _session_namespace_id):
    """Create an async test client with X-Namespace-Id header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Namespace-Id": _session_namespace_id},
    ) as ac:
        yield ac


@pytest.fixture
def test_namespace_id(_session_namespace_id) -> str:
    """テスト用 namespace_id を返す（セッション共有）.

    各テスト関数で新しい namespace を作成する代わりに、
    セッション開始時に作成した共有 namespace の ID を返す。
    """
    return _session_namespace_id
