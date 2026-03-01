"""Integration persistence test shared fixtures.

永続化レイヤーの統合テストで共通利用するフィクスチャ。
database_url / db_manager / db_session / test_namespace_id を提供し、
各テストファイルでの重複定義を排除する。
"""

import os
from uuid import uuid4

import pytest

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager


@pytest.fixture
def database_url() -> str:
    """Get database URL from settings."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/dynamic_ontology_test",
    )


@pytest.fixture
async def db_manager(database_url: str):
    """Create and initialize database manager."""
    manager = DatabaseSessionManager()
    manager.init(database_url)
    yield manager
    await manager.close()


@pytest.fixture
async def db_session(db_manager: DatabaseSessionManager):
    """Provide a database session."""
    async with db_manager.session() as session:
        yield session


@pytest.fixture
def test_namespace_id() -> str:
    """テスト用の namespace_id を返す."""
    return str(uuid4())
