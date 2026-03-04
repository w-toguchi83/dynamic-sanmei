"""大運四季表計算のテスト."""

from __future__ import annotations

from sanmei_core.calculators.taiun_shiki import calculate_taiun_shiki
from sanmei_core.domain.fortune import Taiun, TaiunChart
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.meishiki import (
    MajorStarChart,
    Meishiki,
    SubsidiaryStarChart,
)
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.taiun_shiki import LifeCycle, Season
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType
from sanmei_core.domain.zoukan_tokutei import (
    ActiveHiddenStem,
    HiddenStemType,
    ZoukanTokutei,
)
from sanmei_core.schools.standard import StandardSchool


def _make_dummy_gogyo_balance() -> GoGyoBalance:
    count = GoGyoCount(wood=1, fire=1, earth=1, metal=1, water=1)
    return GoGyoBalance(
        stem_count=count,
        branch_count=count,
        total_count=count,
        dominant=GoGyo.WOOD,
        lacking=(),
        day_stem_gogyo=GoGyo.WOOD,
    )


def _make_test_meishiki() -> Meishiki:
    """テスト命式: 日干=甲(木陽), 月柱=戊辰(index=4)."""
    return Meishiki(
        pillars=ThreePillars(
            year=Kanshi.from_index(0),  # 甲子
            month=Kanshi.from_index(4),  # 戊辰
            day=Kanshi(stem=TenStem.KINOE, branch=TwelveBranch.NE, index=0),  # 甲子
        ),
        hidden_stems={
            "year": HiddenStems(hongen=TenStem.MIZUNOTO),
            "month": HiddenStems(
                hongen=TenStem.TSUCHINOE,
                chuugen=TenStem.MIZUNOTO,
                shogen=TenStem.KINOTO,
            ),
            "day": HiddenStems(hongen=TenStem.MIZUNOTO),
        },
        zoukan_tokutei=ZoukanTokutei(
            days_from_setsuiri=15,
            year=ActiveHiddenStem(stem=TenStem.MIZUNOTO, element=HiddenStemType.HONGEN),
            month=ActiveHiddenStem(stem=TenStem.TSUCHINOE, element=HiddenStemType.HONGEN),
            day=ActiveHiddenStem(stem=TenStem.MIZUNOTO, element=HiddenStemType.HONGEN),
        ),
        major_stars=MajorStarChart(
            north=MajorStar.KANSAKU,
            east=MajorStar.KANSAKU,
            center=MajorStar.KANSAKU,
            west=MajorStar.KANSAKU,
            south=MajorStar.KANSAKU,
        ),
        subsidiary_stars=SubsidiaryStarChart(
            year=SubsidiaryStar.TENPOU,
            month=SubsidiaryStar.TENPOU,
            day=SubsidiaryStar.TENPOU,
        ),
        shimeisei=MajorStar.KANSAKU,
        tenchuusatsu=Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        ),
        shukumei_chuusatsu=(),
        gogyo_balance=_make_dummy_gogyo_balance(),
    )


def _make_test_taiun_chart() -> TaiunChart:
    """テスト大運: 順行、立運5歳、月柱=戊辰(4)から順行で3期間."""
    return TaiunChart(
        direction="順行",
        start_age=5,
        periods=(
            Taiun(kanshi=Kanshi.from_index(5), start_age=5, end_age=14),  # 己巳
            Taiun(kanshi=Kanshi.from_index(6), start_age=15, end_age=24),  # 庚午
            Taiun(kanshi=Kanshi.from_index(7), start_age=25, end_age=34),  # 辛未
        ),
    )


class TestCalculateTaiunShiki:
    def setup_method(self) -> None:
        self.school = StandardSchool()
        self.meishiki = _make_test_meishiki()
        self.taiun_chart = _make_test_taiun_chart()

    def test_returns_chart(self) -> None:
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.direction == "順行"
        assert result.start_age == 5

    def test_entry_count(self) -> None:
        """月干支行 + 3期間 = 4行."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert len(result.entries) == 4

    def test_month_kanshi_entry(self) -> None:
        """先頭行は月干支."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        first = result.entries[0]
        assert first.label == "月干支"
        assert first.kanshi.kanji == "戊辰"
        assert first.start_age == 0
        assert first.end_age == 4

    def test_month_kanshi_season(self) -> None:
        """辰 = 春."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[0].season == Season.SPRING

    def test_month_kanshi_hidden_stems(self) -> None:
        """辰の蔵干: 戊(本元), 癸(中元), 乙(初元)."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        hs = result.entries[0].hidden_stems
        assert hs.hongen == TenStem.TSUCHINOE
        assert hs.chuugen == TenStem.MIZUNOTO
        assert hs.shogen == TenStem.KINOTO

    def test_month_kanshi_major_star(self) -> None:
        """日干=甲(木陽) × 月干=戊(土陽) → 木剋土 = 財星・同陰陽 → 禄存星."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[0].major_star == MajorStar.ROKUZON

    def test_month_kanshi_subsidiary_star(self) -> None:
        """日干=甲 × 辰 → calculate_subsidiary_star で算出."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        # 甲の帝旺支=卯(3), 辰(4), distance=(4-3)%12=1 → JUUNIUN_ORDER[1]=天堂星(衰)
        assert result.entries[0].subsidiary_star == SubsidiaryStar.TENDOU

    def test_month_kanshi_life_cycle(self) -> None:
        """天堂星 → 老人."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[0].life_cycle == LifeCycle.ROUJIN

    def test_period_labels(self) -> None:
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[1].label == "第1句"
        assert result.entries[2].label == "第2句"
        assert result.entries[3].label == "第3句"

    def test_period_1_season(self) -> None:
        """己巳: 巳 = 夏."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[1].season == Season.SUMMER

    def test_period_1_major_star(self) -> None:
        """日干=甲(木陽) × 己(土陰) → 木剋土 = 財星・異陰陽 → 司禄星."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[1].major_star == MajorStar.SHIROKU

    def test_period_2_kanshi(self) -> None:
        """第2句 = 庚午."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[2].kanshi.kanji == "庚午"
        assert result.entries[2].start_age == 15
        assert result.entries[2].end_age == 24

    def test_period_2_season(self) -> None:
        """午 = 夏."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[2].season == Season.SUMMER

    def test_period_3_season(self) -> None:
        """未 = 夏."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[3].season == Season.SUMMER
