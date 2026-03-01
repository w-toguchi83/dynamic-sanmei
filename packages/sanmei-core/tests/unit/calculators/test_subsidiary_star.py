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


class TestCalculateSubsidiaryStar:
    """日干と地支から十二大従星を算出.

    標準流派: 帝旺支から順方向に十二運を割り当て。
    """

    def test_kinoe_at_u_is_tenshou(self) -> None:
        """甲(木) の帝旺支=卯 → 卯=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOE, TwelveBranch.U, school) == SubsidiaryStar.TENSHOU

    def test_kinoe_at_tatsu_is_tendou(self) -> None:
        """甲(木) の帝旺支=卯 → 辰=帝旺+1=衰=天堂星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOE, TwelveBranch.TATSU, school) == SubsidiaryStar.TENDOU

    def test_kinoe_at_tora_is_tenroku(self) -> None:
        """甲(木) の帝旺支=卯 → 寅=帝旺-1=建禄=天禄星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOE, TwelveBranch.TORA, school) == SubsidiaryStar.TENROKU

    def test_hinoe_at_uma_is_tenshou(self) -> None:
        """丙(火) の帝旺支=午 → 午=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.HINOE, TwelveBranch.UMA, school) == SubsidiaryStar.TENSHOU

    def test_mizunoe_at_ne_is_tenshou(self) -> None:
        """壬(水) の帝旺支=子 → 子=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.MIZUNOE, TwelveBranch.NE, school) == SubsidiaryStar.TENSHOU

    @pytest.mark.parametrize(
        ("stem", "branch", "expected"),
        [
            # 甲(帝旺=卯): 子=帝旺から+9=沐浴=天恍星
            (TenStem.KINOE, TwelveBranch.NE, SubsidiaryStar.TENKOU),
            # 甲(帝旺=卯): 午=帝旺から+3=死=天極星
            (TenStem.KINOE, TwelveBranch.UMA, SubsidiaryStar.TENKYOKU),
            # 甲(帝旺=卯): 酉=帝旺から+6=胎=天報星
            (TenStem.KINOE, TwelveBranch.TORI, SubsidiaryStar.TENPOU),
        ],
    )
    def test_parametrized_cases(self, stem: TenStem, branch: TwelveBranch, expected: SubsidiaryStar) -> None:
        school = StandardSchool()
        assert calculate_subsidiary_star(stem, branch, school) == expected


class TestCalculateSubsidiaryStarChart:
    def test_chart_from_pillars(self) -> None:
        school = StandardSchool()
        # 日干=戊, 年支=子, 月支=寅, 日支=辰
        pillars = ThreePillars(
            year=Kanshi.from_index(0),  # 甲子
            month=Kanshi.from_index(2),  # 丙寅
            day=Kanshi.from_index(4),  # 戊辰 (stem=4=戊, branch=4=辰)
        )
        # 日干=戊(土陽) の帝旺支=戌(StandardSchool)
        # 年支=子: (0 - 10) % 12 = 2 → index 2 = 病 = 天胡星
        # 月支=寅: (2 - 10) % 12 = 4 → index 4 = 墓 = 天庫星
        # 日支=辰: (4 - 10) % 12 = 6 → index 6 = 胎 = 天報星
        chart = calculate_subsidiary_star_chart(pillars, pillars.day.stem, school)
        assert chart.year == SubsidiaryStar.TENKO  # 病=天胡星
        assert chart.month == SubsidiaryStar.TENKU  # 墓=天庫星
        assert chart.day == SubsidiaryStar.TENPOU  # 胎=天報星
