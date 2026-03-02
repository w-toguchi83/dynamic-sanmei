"""十二大従星計算のテスト."""

from __future__ import annotations

import pytest
from sanmei_core.calculators.subsidiary_star import (
    calculate_subsidiary_star,
    calculate_subsidiary_star_chart,
)
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import SubsidiaryStar
from sanmei_core.schools.standard import StandardSchool

S = SubsidiaryStar

# 書籍テーブル: 支(row) × 日干(col) → 十二大従星
# fmt: off
_BOOK_TABLE: dict[tuple[TwelveBranch, TenStem], SubsidiaryStar] = {}

_BRANCH_ORDER = list(TwelveBranch)

# 日干別の列データ（書籍の【十二大従星表】そのまま）
_COLUMNS: dict[TenStem, tuple[SubsidiaryStar, ...]] = {
    TenStem.KINOE: (
        S.TENKOU, S.TENNAN, S.TENROKU, S.TENSHOU, S.TENDOU, S.TENKO,
        S.TENKYOKU, S.TENKU, S.TENCHI, S.TENPOU, S.TENIN, S.TENKI,
    ),
    TenStem.KINOTO: (
        S.TENKO, S.TENDOU, S.TENSHOU, S.TENROKU, S.TENNAN, S.TENKOU,
        S.TENKI, S.TENIN, S.TENPOU, S.TENCHI, S.TENKU, S.TENKYOKU,
    ),
    TenStem.HINOE: (
        S.TENPOU, S.TENIN, S.TENKI, S.TENKOU, S.TENNAN, S.TENROKU,
        S.TENSHOU, S.TENDOU, S.TENKO, S.TENKYOKU, S.TENKU, S.TENCHI,
    ),
    TenStem.HINOTO: (
        S.TENCHI, S.TENKU, S.TENKYOKU, S.TENKO, S.TENDOU, S.TENSHOU,
        S.TENROKU, S.TENNAN, S.TENKOU, S.TENKI, S.TENIN, S.TENPOU,
    ),
    TenStem.TSUCHINOE: (
        S.TENPOU, S.TENIN, S.TENKI, S.TENKOU, S.TENNAN, S.TENROKU,
        S.TENSHOU, S.TENDOU, S.TENKO, S.TENKYOKU, S.TENKU, S.TENCHI,
    ),
    TenStem.TSUCHINOTO: (
        S.TENCHI, S.TENKU, S.TENKYOKU, S.TENKO, S.TENDOU, S.TENSHOU,
        S.TENROKU, S.TENNAN, S.TENKOU, S.TENKI, S.TENIN, S.TENPOU,
    ),
    TenStem.KANOE: (
        S.TENKYOKU, S.TENKU, S.TENCHI, S.TENPOU, S.TENIN, S.TENKI,
        S.TENKOU, S.TENNAN, S.TENROKU, S.TENSHOU, S.TENDOU, S.TENKO,
    ),
    TenStem.KANOTO: (
        S.TENKI, S.TENIN, S.TENPOU, S.TENCHI, S.TENKU, S.TENKYOKU,
        S.TENKO, S.TENDOU, S.TENSHOU, S.TENROKU, S.TENNAN, S.TENKOU,
    ),
    TenStem.MIZUNOE: (
        S.TENSHOU, S.TENDOU, S.TENKO, S.TENKYOKU, S.TENKU, S.TENCHI,
        S.TENPOU, S.TENIN, S.TENKI, S.TENKOU, S.TENNAN, S.TENROKU,
    ),
    TenStem.MIZUNOTO: (
        S.TENROKU, S.TENNAN, S.TENKOU, S.TENKI, S.TENIN, S.TENPOU,
        S.TENCHI, S.TENKU, S.TENKYOKU, S.TENKO, S.TENDOU, S.TENSHOU,
    ),
}

for _day_stem, _column in _COLUMNS.items():
    for _i, _star in enumerate(_column):
        _BOOK_TABLE[(_BRANCH_ORDER[_i], _day_stem)] = _star
# fmt: on


class TestSubsidiaryStarBookTable:
    """書籍の十二大従星表（10×12=120パターン）を全検証."""

    @pytest.mark.parametrize(
        ("branch", "day_stem", "expected"),
        [(*key, star) for key, star in _BOOK_TABLE.items()],
        ids=[f"{TwelveBranch(k[0]).name}-{TenStem(k[1]).name}" for k in _BOOK_TABLE],
    )
    def test_book_table(self, branch: TwelveBranch, day_stem: TenStem, expected: SubsidiaryStar) -> None:
        school = StandardSchool()
        assert calculate_subsidiary_star(day_stem, branch, school) == expected


class TestCalculateSubsidiaryStar:
    """個別ケースのテスト."""

    def test_kinoe_at_u_is_tenshou(self) -> None:
        """甲(木陽) の帝旺支=卯 → 卯=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOE, TwelveBranch.U, school) == SubsidiaryStar.TENSHOU

    def test_kinoe_at_tatsu_is_tendou(self) -> None:
        """甲(木陽) の帝旺支=卯 → 辰=衰=天堂星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOE, TwelveBranch.TATSU, school) == SubsidiaryStar.TENDOU

    def test_kinoto_at_tora_is_tenshou(self) -> None:
        """乙(木陰) の帝旺支=寅 → 寅=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOTO, TwelveBranch.TORA, school) == SubsidiaryStar.TENSHOU

    def test_kinoto_at_u_is_tenroku(self) -> None:
        """乙(木陰) → 卯=建禄=天禄星（逆行）."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOTO, TwelveBranch.U, school) == SubsidiaryStar.TENROKU

    def test_mizunoe_at_ne_is_tenshou(self) -> None:
        """壬(水陽) の帝旺支=子 → 子=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.MIZUNOE, TwelveBranch.NE, school) == SubsidiaryStar.TENSHOU

    def test_mizunoto_at_i_is_tenshou(self) -> None:
        """癸(水陰) の帝旺支=亥 → 亥=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.MIZUNOTO, TwelveBranch.I, school) == SubsidiaryStar.TENSHOU


class TestCalculateSubsidiaryStarChart:
    def test_chart_from_pillars(self) -> None:
        school = StandardSchool()
        # 日干=戊, 年支=子, 月支=寅, 日支=辰
        pillars = ThreePillars(
            year=Kanshi.from_index(0),  # 甲子
            month=Kanshi.from_index(2),  # 丙寅
            day=Kanshi.from_index(4),  # 戊辰 (stem=4=戊, branch=4=辰)
        )
        # 日干=戊(土陽) の帝旺支=午(StandardSchool)
        # 年支=子: (0 - 6) % 12 = 6 → index 6 = 胎 = 天報星
        # 月支=寅: (2 - 6) % 12 = 8 → index 8 = 長生 = 天貴星
        # 日支=辰: (4 - 6) % 12 = 10 → index 10 = 冠帯 = 天南星
        chart = calculate_subsidiary_star_chart(pillars, pillars.day.stem, school)
        assert chart.year == SubsidiaryStar.TENPOU  # 胎=天報星
        assert chart.month == SubsidiaryStar.TENKI  # 長生=天貴星
        assert chart.day == SubsidiaryStar.TENNAN  # 冠帯=天南星
