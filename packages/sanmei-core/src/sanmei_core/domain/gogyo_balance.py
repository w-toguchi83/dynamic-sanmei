"""五行バランスのドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel

from sanmei_core.domain.gogyo import GoGyo

_GOGYO_FIELDS = ("wood", "fire", "earth", "metal", "water")


class GoGyoCount(BaseModel, frozen=True):
    """命式中の各五行の出現数."""

    wood: int = 0
    fire: int = 0
    earth: int = 0
    metal: int = 0
    water: int = 0

    def get(self, gogyo: GoGyo) -> int:
        """GoGyo enum から対応するカウントを取得."""
        value: int = getattr(self, _GOGYO_FIELDS[gogyo.value])
        return value

    @property
    def total(self) -> int:
        """全五行の合計."""
        return self.wood + self.fire + self.earth + self.metal + self.water


class GoGyoBalance(BaseModel, frozen=True):
    """五行バランス分析結果."""

    stem_count: GoGyoCount
    branch_count: GoGyoCount
    total_count: GoGyoCount
    dominant: GoGyo
    lacking: tuple[GoGyo, ...]
    day_stem_gogyo: GoGyo
