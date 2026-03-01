"""天中殺計算のテスト."""

from __future__ import annotations

import pytest
from sanmei_core.calculators.tenchuusatsu import calculate_tenchuusatsu
from sanmei_core.domain.kanshi import Kanshi, TwelveBranch
from sanmei_core.domain.tenchuusatsu import TenchuusatsuType


class TestCalculateTenchuusatsu:
    def test_group0_inu_i(self) -> None:
        """甲子(0)〜癸酉(9) → 戌亥天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(0))
        assert tc.type == TenchuusatsuType.INU_I
        assert tc.branches == (TwelveBranch.INU, TwelveBranch.I)

    def test_group1_saru_tori(self) -> None:
        """甲戌(10)〜癸未(19) → 申酉天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(10))
        assert tc.type == TenchuusatsuType.SARU_TORI

    def test_group2_uma_hitsuji(self) -> None:
        """甲申(20)〜癸巳(29) → 午未天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(20))
        assert tc.type == TenchuusatsuType.UMA_HITSUJI

    def test_group3_tatsu_mi(self) -> None:
        """甲午(30)〜癸卯(39) → 辰巳天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(30))
        assert tc.type == TenchuusatsuType.TATSU_MI

    def test_group4_tora_u(self) -> None:
        """甲辰(40)〜癸丑(49) → 寅卯天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(40))
        assert tc.type == TenchuusatsuType.TORA_U

    def test_group5_ne_ushi(self) -> None:
        """甲寅(50)〜癸亥(59) → 子丑天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(50))
        assert tc.type == TenchuusatsuType.NE_USHI

    @pytest.mark.parametrize("index", range(60))
    def test_all_60_kanshi_have_valid_type(self, index: int) -> None:
        tc = calculate_tenchuusatsu(Kanshi.from_index(index))
        assert isinstance(tc.type, TenchuusatsuType)
        assert len(tc.branches) == 2
