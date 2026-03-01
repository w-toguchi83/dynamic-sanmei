"""干支（十干・十二支）のドメインモデル."""

from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel, Field


class TenStem(IntEnum):
    """十干（天干）."""

    KINOE = 0  # 甲 木陽
    KINOTO = 1  # 乙 木陰
    HINOE = 2  # 丙 火陽
    HINOTO = 3  # 丁 火陰
    TSUCHINOE = 4  # 戊 土陽
    TSUCHINOTO = 5  # 己 土陰
    KANOE = 6  # 庚 金陽
    KANOTO = 7  # 辛 金陰
    MIZUNOE = 8  # 壬 水陽
    MIZUNOTO = 9  # 癸 水陰


_STEM_KANJI = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")


class TwelveBranch(IntEnum):
    """十二支（地支）."""

    NE = 0  # 子
    USHI = 1  # 丑
    TORA = 2  # 寅
    U = 3  # 卯
    TATSU = 4  # 辰
    MI = 5  # 巳
    UMA = 6  # 午
    HITSUJI = 7  # 未
    SARU = 8  # 申
    TORI = 9  # 酉
    INU = 10  # 戌
    I = 11  # 亥  # noqa: E741


_BRANCH_KANJI = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")


class Kanshi(BaseModel, frozen=True):
    """干支（天干+地支のペア）.

    六十干支サイクルの1要素を表す。
    index は 0-59 の通し番号で、stem = index % 10, branch = index % 12。
    """

    stem: TenStem
    branch: TwelveBranch
    index: int = Field(ge=0, lt=60)

    @classmethod
    def from_index(cls, index: int) -> Kanshi:
        """六十干支の通し番号から Kanshi を生成."""
        idx = index % 60
        return cls(
            stem=TenStem(idx % 10),
            branch=TwelveBranch(idx % 12),
            index=idx,
        )

    @property
    def kanji(self) -> str:
        """漢字表記（例: '甲子'）."""
        return _STEM_KANJI[self.stem.value] + _BRANCH_KANJI[self.branch.value]
