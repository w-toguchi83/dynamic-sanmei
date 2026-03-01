"""五行（ごぎょう）と陰陽（いんよう）のドメインモデル."""

from __future__ import annotations

from enum import IntEnum

_GOGYO_KANJI = ("木", "火", "土", "金", "水")
_INYOU_KANJI = ("陽", "陰")


class GoGyo(IntEnum):
    """五行."""

    WOOD = 0  # 木
    FIRE = 1  # 火
    EARTH = 2  # 土
    METAL = 3  # 金
    WATER = 4  # 水

    @property
    def kanji(self) -> str:
        """漢字表記."""
        return _GOGYO_KANJI[self.value]


class InYou(IntEnum):
    """陰陽."""

    YOU = 0  # 陽
    IN = 1  # 陰

    @property
    def kanji(self) -> str:
        """漢字表記."""
        return _INYOU_KANJI[self.value]
