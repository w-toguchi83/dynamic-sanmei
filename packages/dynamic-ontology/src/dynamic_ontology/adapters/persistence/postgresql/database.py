"""Database session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class PostgresUnitOfWork:
    """SQLAlchemy セッションをラップした UnitOfWork 実装。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        """現在のトランザクションをコミットする。"""
        await self._session.commit()

    async def rollback(self) -> None:
        """現在のトランザクションをロールバックする。"""
        await self._session.rollback()


class DatabaseSessionManager:
    """Manages database connections and sessions."""

    def __init__(self) -> None:
        """Initialize the session manager."""
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    def init(
        self,
        database_url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        echo: bool = False,
    ) -> None:
        """Initialize the database engine and session factory."""
        self.engine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=echo,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        """Close the database engine."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Provide a transactional scope around a series of operations.

        NOTE: ルートハンドラーでは UnitOfWork.commit() が明示的コミットポイント。
        ここの auto-commit はテスト・ミドルウェア・バックグラウンドタスク用の
        安全ネットとして維持（UoW が先にコミット済みなら no-op）。
        """
        if self.session_factory is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


async def get_session(
    manager: DatabaseSessionManager,
) -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency for getting a database session."""
    async with manager.session() as session:
        yield session
