"""天中殺モデルのテスト."""

from __future__ import annotations

from sanmei_core.domain.kanshi import TwelveBranch
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType


class TestTenchuusatsuType:
    def test_count(self) -> None:
        assert len(TenchuusatsuType) == 6

    def test_values(self) -> None:
        assert TenchuusatsuType.NE_USHI.value == "子丑天中殺"
        assert TenchuusatsuType.TORA_U.value == "寅卯天中殺"
        assert TenchuusatsuType.TATSU_MI.value == "辰巳天中殺"
        assert TenchuusatsuType.UMA_HITSUJI.value == "午未天中殺"
        assert TenchuusatsuType.SARU_TORI.value == "申酉天中殺"
        assert TenchuusatsuType.INU_I.value == "戌亥天中殺"


class TestTenchuusatsu:
    def test_creation(self) -> None:
        tc = Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        )
        assert tc.type == TenchuusatsuType.INU_I
        assert tc.branches == (TwelveBranch.INU, TwelveBranch.I)
