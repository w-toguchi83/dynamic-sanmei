"""蔵干特定の算出テスト.

テスト値は書籍の蔵干表と現行 STANDARD_HIDDEN_STEMS（算命学体系）に基づく。
辰・未・戌は算命学体系でchuugen/shogenがswap済みのため、正しいフィールド値を使用。
"""

from __future__ import annotations

import pytest
from sanmei_core.calculators.zoukan_tokutei import determine_active_hidden_stem
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.zoukan_tokutei import HiddenStemType
from sanmei_core.tables.hidden_stems import STANDARD_HIDDEN_STEMS


class TestDetermineActiveHiddenStem:
    """全12支の蔵干特定テスト."""

    # --- 子: 常に本元(癸) ---

    @pytest.mark.parametrize("days", [1, 5, 10, 15, 20, 30])
    def test_ne_always_hongen(self, days: int) -> None:
        """子: 任意の日数で本元(癸)."""
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.NE]
        result = determine_active_hidden_stem(TwelveBranch.NE, hs, days)
        assert result.stem == TenStem.MIZUNOTO  # 癸
        assert result.element == HiddenStemType.HONGEN

    # --- 丑: 1-9初元(癸), 10-12中元(辛), 13+本元(己) ---

    def test_ushi_day1_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.USHI]
        result = determine_active_hidden_stem(TwelveBranch.USHI, hs, 1)
        assert result.stem == TenStem.MIZUNOTO  # 癸
        assert result.element == HiddenStemType.SHOGEN

    def test_ushi_day9_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.USHI]
        result = determine_active_hidden_stem(TwelveBranch.USHI, hs, 9)
        assert result.stem == TenStem.MIZUNOTO  # 癸
        assert result.element == HiddenStemType.SHOGEN

    def test_ushi_day10_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.USHI]
        result = determine_active_hidden_stem(TwelveBranch.USHI, hs, 10)
        assert result.stem == TenStem.KANOTO  # 辛
        assert result.element == HiddenStemType.CHUUGEN

    def test_ushi_day12_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.USHI]
        result = determine_active_hidden_stem(TwelveBranch.USHI, hs, 12)
        assert result.stem == TenStem.KANOTO  # 辛
        assert result.element == HiddenStemType.CHUUGEN

    def test_ushi_day13_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.USHI]
        result = determine_active_hidden_stem(TwelveBranch.USHI, hs, 13)
        assert result.stem == TenStem.TSUCHINOTO  # 己
        assert result.element == HiddenStemType.HONGEN

    # --- 寅: 1-7初元(戊), 8-14中元(丙), 15+本元(甲) ---

    def test_tora_day7_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.TORA]
        result = determine_active_hidden_stem(TwelveBranch.TORA, hs, 7)
        assert result.stem == TenStem.TSUCHINOE  # 戊
        assert result.element == HiddenStemType.SHOGEN

    def test_tora_day8_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.TORA]
        result = determine_active_hidden_stem(TwelveBranch.TORA, hs, 8)
        assert result.stem == TenStem.HINOE  # 丙
        assert result.element == HiddenStemType.CHUUGEN

    def test_tora_day15_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.TORA]
        result = determine_active_hidden_stem(TwelveBranch.TORA, hs, 15)
        assert result.stem == TenStem.KINOE  # 甲
        assert result.element == HiddenStemType.HONGEN

    # --- 卯: 常に本元(乙) ---

    @pytest.mark.parametrize("days", [1, 10, 20, 30])
    def test_u_always_hongen(self, days: int) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.U]
        result = determine_active_hidden_stem(TwelveBranch.U, hs, days)
        assert result.stem == TenStem.KINOTO  # 乙
        assert result.element == HiddenStemType.HONGEN

    # --- 辰: 1-9初元(乙), 10-12中元(癸), 13+本元(戊) ---
    # 算命学体系: shogen=乙, chuugen=癸, hongen=戊

    def test_tatsu_day9_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.TATSU]
        result = determine_active_hidden_stem(TwelveBranch.TATSU, hs, 9)
        assert result.stem == TenStem.KINOTO  # 乙(shogen)
        assert result.element == HiddenStemType.SHOGEN

    def test_tatsu_day10_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.TATSU]
        result = determine_active_hidden_stem(TwelveBranch.TATSU, hs, 10)
        assert result.stem == TenStem.MIZUNOTO  # 癸(chuugen)
        assert result.element == HiddenStemType.CHUUGEN

    def test_tatsu_day13_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.TATSU]
        result = determine_active_hidden_stem(TwelveBranch.TATSU, hs, 13)
        assert result.stem == TenStem.TSUCHINOE  # 戊(hongen)
        assert result.element == HiddenStemType.HONGEN

    # --- 巳: 1-5初元(戊), 6-14中元(庚), 15+本元(丙) ---

    def test_mi_day5_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.MI]
        result = determine_active_hidden_stem(TwelveBranch.MI, hs, 5)
        assert result.stem == TenStem.TSUCHINOE  # 戊
        assert result.element == HiddenStemType.SHOGEN

    def test_mi_day6_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.MI]
        result = determine_active_hidden_stem(TwelveBranch.MI, hs, 6)
        assert result.stem == TenStem.KANOE  # 庚
        assert result.element == HiddenStemType.CHUUGEN

    def test_mi_day15_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.MI]
        result = determine_active_hidden_stem(TwelveBranch.MI, hs, 15)
        assert result.stem == TenStem.HINOE  # 丙
        assert result.element == HiddenStemType.HONGEN

    # --- 午: 1-19初元(己), 中元なし, 20+本元(丁) ---

    def test_uma_day1_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.UMA]
        result = determine_active_hidden_stem(TwelveBranch.UMA, hs, 1)
        assert result.stem == TenStem.TSUCHINOTO  # 己(shogen)
        assert result.element == HiddenStemType.SHOGEN

    def test_uma_day19_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.UMA]
        result = determine_active_hidden_stem(TwelveBranch.UMA, hs, 19)
        assert result.stem == TenStem.TSUCHINOTO  # 己(shogen)
        assert result.element == HiddenStemType.SHOGEN

    def test_uma_day20_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.UMA]
        result = determine_active_hidden_stem(TwelveBranch.UMA, hs, 20)
        assert result.stem == TenStem.HINOTO  # 丁(hongen)
        assert result.element == HiddenStemType.HONGEN

    # --- 未: 1-9初元(丁), 10-12中元(乙), 13+本元(己) ---
    # 算命学体系: shogen=丁, chuugen=乙, hongen=己

    def test_hitsuji_day9_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.HITSUJI]
        result = determine_active_hidden_stem(TwelveBranch.HITSUJI, hs, 9)
        assert result.stem == TenStem.HINOTO  # 丁(shogen)
        assert result.element == HiddenStemType.SHOGEN

    def test_hitsuji_day12_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.HITSUJI]
        result = determine_active_hidden_stem(TwelveBranch.HITSUJI, hs, 12)
        assert result.stem == TenStem.KINOTO  # 乙(chuugen)
        assert result.element == HiddenStemType.CHUUGEN

    def test_hitsuji_day13_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.HITSUJI]
        result = determine_active_hidden_stem(TwelveBranch.HITSUJI, hs, 13)
        assert result.stem == TenStem.TSUCHINOTO  # 己(hongen)
        assert result.element == HiddenStemType.HONGEN

    # --- 申: 1-10初元(戊), 11-13中元(壬), 14+本元(庚) ---

    def test_saru_day10_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.SARU]
        result = determine_active_hidden_stem(TwelveBranch.SARU, hs, 10)
        assert result.stem == TenStem.TSUCHINOE  # 戊
        assert result.element == HiddenStemType.SHOGEN

    def test_saru_day13_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.SARU]
        result = determine_active_hidden_stem(TwelveBranch.SARU, hs, 13)
        assert result.stem == TenStem.MIZUNOE  # 壬
        assert result.element == HiddenStemType.CHUUGEN

    def test_saru_day14_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.SARU]
        result = determine_active_hidden_stem(TwelveBranch.SARU, hs, 14)
        assert result.stem == TenStem.KANOE  # 庚
        assert result.element == HiddenStemType.HONGEN

    # --- 酉: 常に本元(辛) ---

    @pytest.mark.parametrize("days", [1, 10, 20, 30])
    def test_tori_always_hongen(self, days: int) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.TORI]
        result = determine_active_hidden_stem(TwelveBranch.TORI, hs, days)
        assert result.stem == TenStem.KANOTO  # 辛
        assert result.element == HiddenStemType.HONGEN

    # --- 戌: 1-9初元(辛), 10-12中元(丁), 13+本元(戊) ---
    # 算命学体系: shogen=辛, chuugen=丁, hongen=戊

    def test_inu_day9_shogen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.INU]
        result = determine_active_hidden_stem(TwelveBranch.INU, hs, 9)
        assert result.stem == TenStem.KANOTO  # 辛(shogen)
        assert result.element == HiddenStemType.SHOGEN

    def test_inu_day12_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.INU]
        result = determine_active_hidden_stem(TwelveBranch.INU, hs, 12)
        assert result.stem == TenStem.HINOTO  # 丁(chuugen)
        assert result.element == HiddenStemType.CHUUGEN

    def test_inu_day13_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.INU]
        result = determine_active_hidden_stem(TwelveBranch.INU, hs, 13)
        assert result.stem == TenStem.TSUCHINOE  # 戊(hongen)
        assert result.element == HiddenStemType.HONGEN

    # --- 亥: 初元なし, 1-12中元(甲), 13+本元(壬) ---

    def test_i_day1_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.I]
        result = determine_active_hidden_stem(TwelveBranch.I, hs, 1)
        assert result.stem == TenStem.KINOE  # 甲
        assert result.element == HiddenStemType.CHUUGEN

    def test_i_day12_chuugen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.I]
        result = determine_active_hidden_stem(TwelveBranch.I, hs, 12)
        assert result.stem == TenStem.KINOE  # 甲
        assert result.element == HiddenStemType.CHUUGEN

    def test_i_day13_hongen(self) -> None:
        hs = STANDARD_HIDDEN_STEMS[TwelveBranch.I]
        result = determine_active_hidden_stem(TwelveBranch.I, hs, 13)
        assert result.stem == TenStem.MIZUNOE  # 壬
        assert result.element == HiddenStemType.HONGEN
