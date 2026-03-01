"""Unit of Work ポート定義。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class UnitOfWork(Protocol):
    """トランザクション境界を管理するプロトコル。"""

    async def commit(self) -> None:
        """現在のトランザクションをコミットする。"""
        ...

    async def rollback(self) -> None:
        """現在のトランザクションをロールバックする。"""
        ...
