"""大運×命式の相互作用分析テスト."""

from __future__ import annotations

from sanmei_core.calculators.fortune_analyzer import analyze_fortune_interaction
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.isouhou import BranchInteractionType, StemInteractionType
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.meishiki import (
    MajorStarChart,
    Meishiki,
    SubsidiaryStarChart,
)
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType
from sanmei_core.domain.zoukan_tokutei import (
    ActiveHiddenStem,
    HiddenStemType,
    ZoukanTokutei,
)


def _make_dummy_gogyo_balance() -> GoGyoBalance:
    """テスト用ダミー五行バランス."""
    count = GoGyoCount(wood=1, fire=1, earth=1, metal=1, water=1)
    return GoGyoBalance(
        stem_count=count,
        branch_count=count,
        total_count=count,
        dominant=GoGyo.WOOD,
        lacking=(),
        day_stem_gogyo=GoGyo.WOOD,
    )


def _make_meishiki(
    year_stem: TenStem,
    year_branch: TwelveBranch,
    month_stem: TenStem,
    month_branch: TwelveBranch,
    day_stem: TenStem,
    day_branch: TwelveBranch,
) -> Meishiki:
    return Meishiki(
        pillars=ThreePillars(
            year=Kanshi(stem=year_stem, branch=year_branch, index=0),
            month=Kanshi(stem=month_stem, branch=month_branch, index=1),
            day=Kanshi(stem=day_stem, branch=day_branch, index=2),
        ),
        hidden_stems={
            "year": HiddenStems(hongen=TenStem.MIZUNOTO),
            "month": HiddenStems(hongen=TenStem.MIZUNOTO),
            "day": HiddenStems(hongen=TenStem.MIZUNOTO),
        },
        zoukan_tokutei=ZoukanTokutei(
            days_from_setsuiri=15,
            year=ActiveHiddenStem(stem=TenStem.MIZUNOTO, element=HiddenStemType.HONGEN),
            month=ActiveHiddenStem(stem=TenStem.MIZUNOTO, element=HiddenStemType.HONGEN),
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


class TestAnalyzeFortuneInteraction:
    def test_stem_gou_detected(self) -> None:
        """大運天干と命式天干の合を検出."""
        meishiki = _make_meishiki(
            TenStem.KINOE,
            TwelveBranch.NE,
            TenStem.HINOE,
            TwelveBranch.TORA,
            TenStem.KANOE,
            TwelveBranch.UMA,
        )
        # 大運干支が己(TSUCHINOTO) → 甲(KINOE)との合
        period_kanshi = Kanshi(stem=TenStem.TSUCHINOTO, branch=TwelveBranch.MI, index=5)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        stem_types = {si.type for si in fi.isouhou.stem_interactions}
        assert StemInteractionType.GOU in stem_types

    def test_branch_rokuchuu_detected(self) -> None:
        """大運地支と命式地支の六冲を検出."""
        meishiki = _make_meishiki(
            TenStem.KINOE,
            TwelveBranch.NE,
            TenStem.HINOE,
            TwelveBranch.TORA,
            TenStem.KANOE,
            TwelveBranch.UMA,
        )
        # 大運地支が午(UMA) → 子(NE)との六冲
        period_kanshi = Kanshi(stem=TenStem.HINOTO, branch=TwelveBranch.UMA, index=43)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        branch_types = {bi.type for bi in fi.isouhou.branch_interactions}
        assert BranchInteractionType.ROKUCHUU in branch_types

    def test_no_interaction(self) -> None:
        """相互作用なし."""
        meishiki = _make_meishiki(
            TenStem.KINOE,
            TwelveBranch.TORA,
            TenStem.HINOE,
            TwelveBranch.UMA,
            TenStem.KANOE,
            TwelveBranch.INU,
        )
        period_kanshi = Kanshi(stem=TenStem.MIZUNOE, branch=TwelveBranch.NE, index=48)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        assert len(fi.isouhou.stem_interactions) == 0

    def test_excludes_meishiki_internal_interactions(self) -> None:
        """命式内部の相互作用は除外される."""
        meishiki = _make_meishiki(
            TenStem.KINOE,
            TwelveBranch.TORA,
            TenStem.TSUCHINOTO,
            TwelveBranch.UMA,
            TenStem.HINOE,
            TwelveBranch.INU,
        )
        period_kanshi = Kanshi(stem=TenStem.MIZUNOE, branch=TwelveBranch.NE, index=48)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        assert len(fi.isouhou.stem_interactions) == 0

    def test_affected_stars_is_none(self) -> None:
        """affected_stars は現時点では None."""
        meishiki = _make_meishiki(
            TenStem.KINOE,
            TwelveBranch.NE,
            TenStem.HINOE,
            TwelveBranch.TORA,
            TenStem.KANOE,
            TwelveBranch.UMA,
        )
        period_kanshi = Kanshi(stem=TenStem.TSUCHINOTO, branch=TwelveBranch.MI, index=5)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        assert fi.affected_stars is None

    def test_period_kanshi_in_result(self) -> None:
        """結果に period_kanshi が含まれる."""
        meishiki = _make_meishiki(
            TenStem.KINOE,
            TwelveBranch.NE,
            TenStem.HINOE,
            TwelveBranch.TORA,
            TenStem.KANOE,
            TwelveBranch.UMA,
        )
        period_kanshi = Kanshi(stem=TenStem.TSUCHINOTO, branch=TwelveBranch.MI, index=5)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        assert fi.period_kanshi == period_kanshi

    def test_branch_rikugou_detected(self) -> None:
        """大運地支と命式地支の六合を検出."""
        meishiki = _make_meishiki(
            TenStem.KINOE,
            TwelveBranch.NE,
            TenStem.HINOE,
            TwelveBranch.TORA,
            TenStem.KANOE,
            TwelveBranch.UMA,
        )
        # 大運地支が丑(USHI) → 子(NE)との六合
        period_kanshi = Kanshi(stem=TenStem.MIZUNOE, branch=TwelveBranch.USHI, index=49)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        branch_types = {bi.type for bi in fi.isouhou.branch_interactions}
        assert BranchInteractionType.RIKUGOU in branch_types
