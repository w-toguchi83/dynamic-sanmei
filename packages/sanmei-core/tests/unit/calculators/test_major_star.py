"""十大主星計算のテスト."""

from __future__ import annotations

import pytest
from sanmei_core.calculators.major_star import calculate_major_star_chart
from sanmei_core.domain.kanshi import Kanshi, TenStem
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar
from sanmei_core.schools.standard import StandardSchool

# 書籍テーブル: 他干(row) × 日干(col) → 十大主星
# fmt: off
_BOOK_TABLE: dict[tuple[TenStem, TenStem], MajorStar] = {}

# 日干別の列データ（書籍の【十大主星表】そのまま）
_COLUMNS: dict[TenStem, tuple[MajorStar, ...]] = {
    TenStem.KINOE: (
        MajorStar.KANSAKU, MajorStar.SEKIMON, MajorStar.HOUKAKU, MajorStar.CHOUJYO,
        MajorStar.ROKUZON, MajorStar.SHIROKU, MajorStar.SHAKI, MajorStar.KENGYU,
        MajorStar.RYUKOU, MajorStar.GYOKUDO,
    ),
    TenStem.KINOTO: (
        MajorStar.SEKIMON, MajorStar.KANSAKU, MajorStar.CHOUJYO, MajorStar.HOUKAKU,
        MajorStar.SHIROKU, MajorStar.ROKUZON, MajorStar.KENGYU, MajorStar.SHAKI,
        MajorStar.GYOKUDO, MajorStar.RYUKOU,
    ),
    TenStem.HINOE: (
        MajorStar.RYUKOU, MajorStar.GYOKUDO, MajorStar.KANSAKU, MajorStar.SEKIMON,
        MajorStar.HOUKAKU, MajorStar.CHOUJYO, MajorStar.ROKUZON, MajorStar.SHIROKU,
        MajorStar.SHAKI, MajorStar.KENGYU,
    ),
    TenStem.HINOTO: (
        MajorStar.GYOKUDO, MajorStar.RYUKOU, MajorStar.SEKIMON, MajorStar.KANSAKU,
        MajorStar.CHOUJYO, MajorStar.HOUKAKU, MajorStar.SHIROKU, MajorStar.ROKUZON,
        MajorStar.KENGYU, MajorStar.SHAKI,
    ),
    TenStem.TSUCHINOE: (
        MajorStar.SHAKI, MajorStar.KENGYU, MajorStar.RYUKOU, MajorStar.GYOKUDO,
        MajorStar.KANSAKU, MajorStar.SEKIMON, MajorStar.HOUKAKU, MajorStar.CHOUJYO,
        MajorStar.ROKUZON, MajorStar.SHIROKU,
    ),
    TenStem.TSUCHINOTO: (
        MajorStar.KENGYU, MajorStar.SHAKI, MajorStar.GYOKUDO, MajorStar.RYUKOU,
        MajorStar.SEKIMON, MajorStar.KANSAKU, MajorStar.CHOUJYO, MajorStar.HOUKAKU,
        MajorStar.SHIROKU, MajorStar.ROKUZON,
    ),
    TenStem.KANOE: (
        MajorStar.ROKUZON, MajorStar.SHIROKU, MajorStar.SHAKI, MajorStar.KENGYU,
        MajorStar.RYUKOU, MajorStar.GYOKUDO, MajorStar.KANSAKU, MajorStar.SEKIMON,
        MajorStar.HOUKAKU, MajorStar.CHOUJYO,
    ),
    TenStem.KANOTO: (
        MajorStar.SHIROKU, MajorStar.ROKUZON, MajorStar.KENGYU, MajorStar.SHAKI,
        MajorStar.GYOKUDO, MajorStar.RYUKOU, MajorStar.SEKIMON, MajorStar.KANSAKU,
        MajorStar.CHOUJYO, MajorStar.HOUKAKU,
    ),
    TenStem.MIZUNOE: (
        MajorStar.HOUKAKU, MajorStar.CHOUJYO, MajorStar.ROKUZON, MajorStar.SHIROKU,
        MajorStar.SHAKI, MajorStar.KENGYU, MajorStar.RYUKOU, MajorStar.GYOKUDO,
        MajorStar.KANSAKU, MajorStar.SEKIMON,
    ),
    TenStem.MIZUNOTO: (
        MajorStar.CHOUJYO, MajorStar.HOUKAKU, MajorStar.SHIROKU, MajorStar.ROKUZON,
        MajorStar.KENGYU, MajorStar.SHAKI, MajorStar.GYOKUDO, MajorStar.RYUKOU,
        MajorStar.SEKIMON, MajorStar.KANSAKU,
    ),
}

_STEM_ORDER = list(TenStem)
for _day_stem, _column in _COLUMNS.items():
    for _i, _star in enumerate(_column):
        _BOOK_TABLE[(_STEM_ORDER[_i], _day_stem)] = _star
# fmt: on


class TestMajorStarBookTable:
    """書籍の十大主星表（10×10=100パターン）を全検証."""

    @pytest.mark.parametrize(
        ("other_stem", "day_stem", "expected"),
        [(*key, star) for key, star in _BOOK_TABLE.items()],
        ids=[f"{TenStem(k[0]).name}-{TenStem(k[1]).name}" for k in _BOOK_TABLE],
    )
    def test_book_table(self, other_stem: TenStem, day_stem: TenStem, expected: MajorStar) -> None:
        school = StandardSchool()
        assert school.determine_major_star(day_stem, other_stem) == expected


class TestCalculateMajorStarChart:
    def test_mizunoe_ne_chart(self) -> None:
        """年柱=甲子, 月柱=丙寅, 日柱=壬子 の十大主星配置.

        書籍配置: ①北=年干, ②南=月干, ③東=年支蔵干, ④中央=月支蔵干, ⑤西=日支蔵干
        """
        school = StandardSchool()
        pillars = ThreePillars(
            year=Kanshi.from_index(0),  # 甲子
            month=Kanshi.from_index(2),  # 丙寅
            day=Kanshi.from_index(48),  # 壬子
        )
        hidden = {
            "year": school.get_hidden_stems(pillars.year.branch),  # 子 → 癸
            "month": school.get_hidden_stems(pillars.month.branch),  # 寅 → 甲,丙,戊
            "day": school.get_hidden_stems(pillars.day.branch),  # 子 → 癸
        }
        chart = calculate_major_star_chart(pillars, hidden, school)

        # 日干=壬(水陽)
        # ① north: 年干=甲(木陽) vs 壬(水陽) → 食傷・同陰陽 → 鳳閣星
        assert chart.north == MajorStar.HOUKAKU
        # ② south: 月干=丙(火陽) vs 壬(水陽) → 財星・同陰陽 → 禄存星
        assert chart.south == MajorStar.ROKUZON
        # ③ east: 年支蔵干本元=癸(水陰) vs 壬(水陽) → 比劫・異陰陽 → 石門星
        assert chart.east == MajorStar.SEKIMON
        # ④ center: 月支蔵干本元=甲(木陽) vs 壬(水陽) → 食傷・同陰陽 → 鳳閣星
        assert chart.center == MajorStar.HOUKAKU
        # ⑤ west: 日支蔵干本元=癸(水陰) vs 壬(水陽) → 比劫・異陰陽 → 石門星
        assert chart.west == MajorStar.SEKIMON
