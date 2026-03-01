"""位相法算出のテスト."""

from __future__ import annotations

from sanmei_core.calculators.isouhou import (
    analyze_branch_interactions,
    analyze_isouhou,
    analyze_stem_interactions,
)
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.isouhou import BranchInteractionType, StemInteractionType
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars


class TestAnalyzeStemInteractions:
    def test_gou_detected(self) -> None:
        """甲・己 → 合（土）."""
        result = analyze_stem_interactions([TenStem.KINOE, TenStem.TSUCHINOTO])
        assert len(result) == 1
        assert result[0].type == StemInteractionType.GOU
        assert result[0].result_gogyo == GoGyo.EARTH

    def test_no_gou(self) -> None:
        """合にならない組み合わせ."""
        result = analyze_stem_interactions([TenStem.KINOE, TenStem.HINOE])
        assert len(result) == 0

    def test_multiple_stems(self) -> None:
        """3天干の場合、全ペアを検査."""
        result = analyze_stem_interactions([TenStem.KINOE, TenStem.TSUCHINOTO, TenStem.KANOE])
        assert len(result) == 1  # 甲己合のみ


class TestAnalyzeBranchInteractions:
    def test_rikugou_detected(self) -> None:
        """子・丑 → 六合（土）."""
        result = analyze_branch_interactions([TwelveBranch.NE, TwelveBranch.USHI])
        types = {i.type for i in result}
        assert BranchInteractionType.RIKUGOU in types

    def test_rokuchuu_detected(self) -> None:
        """子・午 → 六冲."""
        result = analyze_branch_interactions([TwelveBranch.NE, TwelveBranch.UMA])
        types = {i.type for i in result}
        assert BranchInteractionType.ROKUCHUU in types

    def test_sangou_detected(self) -> None:
        """亥・卯・未 → 三合局（木）."""
        result = analyze_branch_interactions([TwelveBranch.I, TwelveBranch.U, TwelveBranch.HITSUJI])
        types = {i.type for i in result}
        assert BranchInteractionType.SANGOU in types
        sangou = next(i for i in result if i.type == BranchInteractionType.SANGOU)
        assert sangou.result_gogyo == GoGyo.WOOD

    def test_sankei_detected(self) -> None:
        """寅・巳・申 → 三刑."""
        result = analyze_branch_interactions([TwelveBranch.TORA, TwelveBranch.MI, TwelveBranch.SARU])
        types = {i.type for i in result}
        assert BranchInteractionType.KEI in types

    def test_jikei_detected(self) -> None:
        """午・午 → 自刑."""
        result = analyze_branch_interactions([TwelveBranch.UMA, TwelveBranch.UMA])
        types = {i.type for i in result}
        assert BranchInteractionType.JIKEI in types

    def test_rikugai_detected(self) -> None:
        """子・未 → 六害."""
        result = analyze_branch_interactions([TwelveBranch.NE, TwelveBranch.HITSUJI])
        types = {i.type for i in result}
        assert BranchInteractionType.RIKUGAI in types

    def test_no_interaction(self) -> None:
        """相互作用なし."""
        result = analyze_branch_interactions([TwelveBranch.NE, TwelveBranch.TORA])
        assert len(result) == 0

    def test_multiple_interactions(self) -> None:
        """同じペアで複数の相互作用が検出されうる."""
        result = analyze_branch_interactions([TwelveBranch.USHI, TwelveBranch.UMA])
        types = {i.type for i in result}
        assert BranchInteractionType.RIKUGAI in types


class TestAnalyzeIsouhou:
    def test_basic_pillars(self) -> None:
        """三柱の位相法分析."""
        pillars = ThreePillars(
            year=Kanshi(stem=TenStem.KINOE, branch=TwelveBranch.NE, index=0),
            month=Kanshi(stem=TenStem.TSUCHINOTO, branch=TwelveBranch.UMA, index=5),
            day=Kanshi(stem=TenStem.HINOE, branch=TwelveBranch.TORA, index=2),
        )
        result = analyze_isouhou(pillars)
        stem_types = {si.type for si in result.stem_interactions}
        assert StemInteractionType.GOU in stem_types
        branch_types = {bi.type for bi in result.branch_interactions}
        assert BranchInteractionType.ROKUCHUU in branch_types

    def test_no_interactions(self) -> None:
        """相互作用のない命式."""
        pillars = ThreePillars(
            year=Kanshi(stem=TenStem.KINOE, branch=TwelveBranch.TORA, index=50),
            month=Kanshi(stem=TenStem.HINOE, branch=TwelveBranch.UMA, index=42),
            day=Kanshi(stem=TenStem.KANOE, branch=TwelveBranch.INU, index=46),
        )
        result = analyze_isouhou(pillars)
        assert len(result.stem_interactions) == 0
        branch_types = {bi.type for bi in result.branch_interactions}
        assert BranchInteractionType.SANGOU in branch_types
