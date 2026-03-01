"""五行関係テーブルのテスト."""

from __future__ import annotations

import pytest
from sanmei_core.domain.gogyo import GoGyo, InYou
from sanmei_core.domain.kanshi import TenStem
from sanmei_core.tables.gogyo import (
    SOUGOU,
    SOUKOKU,
    STEM_TO_GOGYO,
    STEM_TO_INYOU,
    GoGyoRelation,
    get_relation,
    is_same_polarity,
)


class TestStemMappings:
    def test_stem_to_gogyo_count(self) -> None:
        assert len(STEM_TO_GOGYO) == 10

    @pytest.mark.parametrize(
        ("stem", "expected"),
        [
            (TenStem.KINOE, GoGyo.WOOD),
            (TenStem.KINOTO, GoGyo.WOOD),
            (TenStem.HINOE, GoGyo.FIRE),
            (TenStem.HINOTO, GoGyo.FIRE),
            (TenStem.TSUCHINOE, GoGyo.EARTH),
            (TenStem.TSUCHINOTO, GoGyo.EARTH),
            (TenStem.KANOE, GoGyo.METAL),
            (TenStem.KANOTO, GoGyo.METAL),
            (TenStem.MIZUNOE, GoGyo.WATER),
            (TenStem.MIZUNOTO, GoGyo.WATER),
        ],
    )
    def test_stem_to_gogyo(self, stem: TenStem, expected: GoGyo) -> None:
        assert STEM_TO_GOGYO[stem] == expected

    @pytest.mark.parametrize(
        ("stem", "expected"),
        [
            (TenStem.KINOE, InYou.YOU),
            (TenStem.KINOTO, InYou.IN),
            (TenStem.HINOE, InYou.YOU),
            (TenStem.HINOTO, InYou.IN),
        ],
    )
    def test_stem_to_inyou(self, stem: TenStem, expected: InYou) -> None:
        assert STEM_TO_INYOU[stem] == expected


class TestCycles:
    def test_sougou_production_cycle(self) -> None:
        """木→火→土→金→水→木."""
        assert SOUGOU[GoGyo.WOOD] == GoGyo.FIRE
        assert SOUGOU[GoGyo.FIRE] == GoGyo.EARTH
        assert SOUGOU[GoGyo.EARTH] == GoGyo.METAL
        assert SOUGOU[GoGyo.METAL] == GoGyo.WATER
        assert SOUGOU[GoGyo.WATER] == GoGyo.WOOD

    def test_soukoku_control_cycle(self) -> None:
        """木→土→水→火→金→木."""
        assert SOUKOKU[GoGyo.WOOD] == GoGyo.EARTH
        assert SOUKOKU[GoGyo.EARTH] == GoGyo.WATER
        assert SOUKOKU[GoGyo.WATER] == GoGyo.FIRE
        assert SOUKOKU[GoGyo.FIRE] == GoGyo.METAL
        assert SOUKOKU[GoGyo.METAL] == GoGyo.WOOD


class TestIsSamePolarity:
    def test_same_yang(self) -> None:
        assert is_same_polarity(TenStem.KINOE, TenStem.HINOE) is True

    def test_same_yin(self) -> None:
        assert is_same_polarity(TenStem.KINOTO, TenStem.HINOTO) is True

    def test_different(self) -> None:
        assert is_same_polarity(TenStem.KINOE, TenStem.KINOTO) is False


class TestGetRelation:
    def test_hikaku_same_element(self) -> None:
        """甲 vs 甲 = 比劫（同五行）."""
        assert get_relation(TenStem.KINOE, TenStem.KINOE) == GoGyoRelation.HIKAKU

    def test_hikaku_different_polarity(self) -> None:
        """甲 vs 乙 = 比劫（同五行・異陰陽）."""
        assert get_relation(TenStem.KINOE, TenStem.KINOTO) == GoGyoRelation.HIKAKU

    def test_shokushou_day_produces(self) -> None:
        """甲(木) vs 丙(火) = 食傷（木生火）."""
        assert get_relation(TenStem.KINOE, TenStem.HINOE) == GoGyoRelation.SHOKUSHOU

    def test_zaisei_day_conquers(self) -> None:
        """甲(木) vs 戊(土) = 財星（木剋土）."""
        assert get_relation(TenStem.KINOE, TenStem.TSUCHINOE) == GoGyoRelation.ZAISEI

    def test_kansei_target_conquers(self) -> None:
        """甲(木) vs 庚(金) = 官星（金剋木）."""
        assert get_relation(TenStem.KINOE, TenStem.KANOE) == GoGyoRelation.KANSEI

    def test_injyu_target_produces(self) -> None:
        """甲(木) vs 壬(水) = 印綬（水生木）."""
        assert get_relation(TenStem.KINOE, TenStem.MIZUNOE) == GoGyoRelation.INJYU
