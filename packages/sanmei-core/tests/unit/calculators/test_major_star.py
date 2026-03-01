"""十大主星計算のテスト."""

from __future__ import annotations

from sanmei_core.calculators.major_star import calculate_major_star_chart
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar
from sanmei_core.schools.standard import StandardSchool


class TestCalculateMajorStarChart:
    def test_mizunoe_ne_chart(self) -> None:
        """年柱=甲子, 月柱=丙寅, 日柱=壬子 の十大主星配置."""
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
        # north: 年干=甲(木陽) vs 壬(水陽) → 食傷・同陽 → 鳳閣星
        assert chart.north == MajorStar.HOUKAKU
        # east: 月干=丙(火陽) vs 壬(水陽) → 財星・同陽 → 禄存星
        assert chart.east == MajorStar.ROKUZON
        # center: 日支蔵干主気=癸(水陰) vs 壬(水陽) → 比劫・異陰陽 → 石門星
        assert chart.center == MajorStar.SEKIMON
        # west: 月支蔵干主気=甲(木陽) vs 壬(水陽) → 食傷・同陽 → 鳳閣星
        assert chart.west == MajorStar.HOUKAKU
        # south: 年支蔵干主気=癸(水陰) vs 壬(水陽) → 比劫・異陰陽 → 石門星
        assert chart.south == MajorStar.SEKIMON
