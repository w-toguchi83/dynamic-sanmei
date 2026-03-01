"""位相法ドメインモデルのテスト."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.isouhou import (
    BranchInteraction,
    BranchInteractionType,
    IsouhouResult,
    StemInteraction,
    StemInteractionType,
)
from sanmei_core.domain.kanshi import TenStem, TwelveBranch


class TestStemInteractionType:
    def test_gou(self) -> None:
        assert StemInteractionType.GOU.value == "合"


class TestBranchInteractionType:
    def test_all_types(self) -> None:
        assert len(BranchInteractionType) == 6
        assert BranchInteractionType.RIKUGOU.value == "六合"
        assert BranchInteractionType.SANGOU.value == "三合局"
        assert BranchInteractionType.ROKUCHUU.value == "六冲"
        assert BranchInteractionType.KEI.value == "刑"
        assert BranchInteractionType.JIKEI.value == "自刑"
        assert BranchInteractionType.RIKUGAI.value == "六害"


class TestStemInteraction:
    def test_creation(self) -> None:
        si = StemInteraction(
            type=StemInteractionType.GOU,
            stems=(TenStem.KINOE, TenStem.TSUCHINOTO),
            result_gogyo=GoGyo.EARTH,
        )
        assert si.type == StemInteractionType.GOU
        assert si.stems == (TenStem.KINOE, TenStem.TSUCHINOTO)
        assert si.result_gogyo == GoGyo.EARTH


class TestBranchInteraction:
    def test_creation_with_gogyo(self) -> None:
        bi = BranchInteraction(
            type=BranchInteractionType.RIKUGOU,
            branches=(TwelveBranch.NE, TwelveBranch.USHI),
            result_gogyo=GoGyo.EARTH,
        )
        assert bi.result_gogyo == GoGyo.EARTH

    def test_creation_without_gogyo(self) -> None:
        bi = BranchInteraction(
            type=BranchInteractionType.ROKUCHUU,
            branches=(TwelveBranch.NE, TwelveBranch.UMA),
            result_gogyo=None,
        )
        assert bi.result_gogyo is None

    def test_three_branches_for_sangou(self) -> None:
        bi = BranchInteraction(
            type=BranchInteractionType.SANGOU,
            branches=(TwelveBranch.I, TwelveBranch.U, TwelveBranch.HITSUJI),
            result_gogyo=GoGyo.WOOD,
        )
        assert len(bi.branches) == 3


class TestIsouhouResult:
    def test_empty(self) -> None:
        result = IsouhouResult(stem_interactions=(), branch_interactions=())
        assert len(result.stem_interactions) == 0
        assert len(result.branch_interactions) == 0
