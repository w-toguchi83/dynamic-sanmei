"""蔵干テーブルのテスト."""

from __future__ import annotations

import pytest
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.tables.hidden_stems import STANDARD_HIDDEN_STEMS


class TestStandardHiddenStems:
    def test_all_branches_present(self) -> None:
        assert len(STANDARD_HIDDEN_STEMS) == 12
        for branch in TwelveBranch:
            assert branch in STANDARD_HIDDEN_STEMS

    @pytest.mark.parametrize(
        ("branch", "main", "middle", "minor"),
        [
            (TwelveBranch.NE, TenStem.MIZUNOTO, None, None),
            (TwelveBranch.USHI, TenStem.TSUCHINOTO, TenStem.KANOTO, TenStem.MIZUNOTO),
            (TwelveBranch.TORA, TenStem.KINOE, TenStem.HINOE, TenStem.TSUCHINOE),
            (TwelveBranch.U, TenStem.KINOTO, None, None),
            (TwelveBranch.TATSU, TenStem.TSUCHINOE, TenStem.KINOTO, TenStem.MIZUNOTO),
            (TwelveBranch.MI, TenStem.HINOE, TenStem.KANOE, TenStem.TSUCHINOE),
            (TwelveBranch.UMA, TenStem.HINOTO, TenStem.TSUCHINOTO, None),
            (TwelveBranch.HITSUJI, TenStem.TSUCHINOTO, TenStem.HINOTO, TenStem.KINOTO),
            (TwelveBranch.SARU, TenStem.KANOE, TenStem.MIZUNOE, TenStem.TSUCHINOE),
            (TwelveBranch.TORI, TenStem.KANOTO, None, None),
            (TwelveBranch.INU, TenStem.TSUCHINOE, TenStem.KANOTO, TenStem.HINOTO),
            (TwelveBranch.I, TenStem.MIZUNOE, TenStem.KINOE, None),
        ],
    )
    def test_hidden_stems(
        self,
        branch: TwelveBranch,
        main: TenStem,
        middle: TenStem | None,
        minor: TenStem | None,
    ) -> None:
        hs = STANDARD_HIDDEN_STEMS[branch]
        assert hs.main == main
        assert hs.middle == middle
        assert hs.minor == minor
