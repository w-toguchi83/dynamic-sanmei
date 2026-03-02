"""蔵干特定テーブルのテスト."""

from __future__ import annotations

import pytest
from sanmei_core.domain.kanshi import TwelveBranch
from sanmei_core.tables.zoukan_tokutei import ZOUKAN_BOUNDARIES, ZoukanBoundary


class TestZoukanBoundariesComplete:
    """全12支の境界値が定義されていること."""

    def test_all_twelve_branches_defined(self) -> None:
        """全12支の境界が定義されている."""
        for branch in TwelveBranch:
            assert branch in ZOUKAN_BOUNDARIES, f"{branch.name} not in ZOUKAN_BOUNDARIES"

    def test_exactly_twelve_entries(self) -> None:
        """ちょうど12エントリ."""
        assert len(ZOUKAN_BOUNDARIES) == 12


class TestZoukanBoundaryValues:
    """各支の境界値が書籍テーブルと一致すること."""

    @pytest.mark.parametrize(
        ("branch", "expected"),
        [
            (TwelveBranch.NE, ZoukanBoundary(None, None)),
            (TwelveBranch.USHI, ZoukanBoundary(9, 12)),
            (TwelveBranch.TORA, ZoukanBoundary(7, 14)),
            (TwelveBranch.U, ZoukanBoundary(None, None)),
            (TwelveBranch.TATSU, ZoukanBoundary(9, 12)),
            (TwelveBranch.MI, ZoukanBoundary(5, 14)),
            (TwelveBranch.UMA, ZoukanBoundary(19, None)),
            (TwelveBranch.HITSUJI, ZoukanBoundary(9, 12)),
            (TwelveBranch.SARU, ZoukanBoundary(10, 13)),
            (TwelveBranch.TORI, ZoukanBoundary(None, None)),
            (TwelveBranch.INU, ZoukanBoundary(9, 12)),
            (TwelveBranch.I, ZoukanBoundary(None, 12)),
        ],
    )
    def test_boundary_matches_book(self, branch: TwelveBranch, expected: ZoukanBoundary) -> None:
        """書籍テーブルの境界値と一致."""
        assert ZOUKAN_BOUNDARIES[branch] == expected
