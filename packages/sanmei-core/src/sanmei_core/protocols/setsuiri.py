"""SetsuiriProvider Protocol — 節入り日データの供給インターフェース."""

from __future__ import annotations

from typing import Protocol

from sanmei_core.domain.calendar import SetsuiriDate


class SetsuiriProvider(Protocol):
    """節入り日を供給するプロトコル.

    流派ごとに実装を差し替え可能。
    """

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        """指定年の12節入り日（節気のみ、中気は除く）を返す.

        立春〜小寒の12件。算命学の月境界となる節気のみ。
        """
        ...

    def get_risshun(self, year: int) -> SetsuiriDate:
        """指定年の立春（年の境界）を返す."""
        ...
