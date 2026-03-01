"""位相法テーブルのテスト."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.tables.isouhou import (
    JIKEI,
    RIKUGAI,
    RIKUGOU,
    ROKUCHUU,
    SANGOU,
    SANKEI,
    STEM_GOU,
)


class TestStemGou:
    def test_has_5_pairs(self) -> None:
        assert len(STEM_GOU) == 5

    def test_kinoe_tsuchinoto_earth(self) -> None:
        assert STEM_GOU[frozenset({TenStem.KINOE, TenStem.TSUCHINOTO})] == GoGyo.EARTH

    def test_kinoto_kanoe_metal(self) -> None:
        assert STEM_GOU[frozenset({TenStem.KINOTO, TenStem.KANOE})] == GoGyo.METAL

    def test_hinoe_kanoto_water(self) -> None:
        assert STEM_GOU[frozenset({TenStem.HINOE, TenStem.KANOTO})] == GoGyo.WATER

    def test_hinoto_mizunoe_wood(self) -> None:
        assert STEM_GOU[frozenset({TenStem.HINOTO, TenStem.MIZUNOE})] == GoGyo.WOOD

    def test_tsuchinoe_mizunoto_fire(self) -> None:
        assert STEM_GOU[frozenset({TenStem.TSUCHINOE, TenStem.MIZUNOTO})] == GoGyo.FIRE


class TestRikugou:
    def test_has_6_pairs(self) -> None:
        assert len(RIKUGOU) == 6

    def test_ne_ushi_earth(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.NE, TwelveBranch.USHI})] == GoGyo.EARTH

    def test_tora_i_wood(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.TORA, TwelveBranch.I})] == GoGyo.WOOD

    def test_u_inu_fire(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.U, TwelveBranch.INU})] == GoGyo.FIRE

    def test_tatsu_tori_metal(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.TATSU, TwelveBranch.TORI})] == GoGyo.METAL

    def test_mi_saru_water(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.MI, TwelveBranch.SARU})] == GoGyo.WATER

    def test_uma_hitsuji_fire(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.UMA, TwelveBranch.HITSUJI})] == GoGyo.FIRE


class TestSangou:
    def test_has_4_sets(self) -> None:
        assert len(SANGOU) == 4

    def test_wood_i_u_hitsuji(self) -> None:
        wood_set = next((s, g) for s, g in SANGOU if g == GoGyo.WOOD)
        assert wood_set[0] == frozenset({TwelveBranch.I, TwelveBranch.U, TwelveBranch.HITSUJI})

    def test_fire_tora_uma_inu(self) -> None:
        fire_set = next((s, g) for s, g in SANGOU if g == GoGyo.FIRE)
        assert fire_set[0] == frozenset({TwelveBranch.TORA, TwelveBranch.UMA, TwelveBranch.INU})

    def test_metal_mi_tori_ushi(self) -> None:
        metal_set = next((s, g) for s, g in SANGOU if g == GoGyo.METAL)
        assert metal_set[0] == frozenset({TwelveBranch.MI, TwelveBranch.TORI, TwelveBranch.USHI})

    def test_water_saru_ne_tatsu(self) -> None:
        water_set = next((s, g) for s, g in SANGOU if g == GoGyo.WATER)
        assert water_set[0] == frozenset({TwelveBranch.SARU, TwelveBranch.NE, TwelveBranch.TATSU})


class TestRokuchuu:
    def test_has_6_pairs(self) -> None:
        assert len(ROKUCHUU) == 6

    def test_ne_uma(self) -> None:
        assert frozenset({TwelveBranch.NE, TwelveBranch.UMA}) in ROKUCHUU

    def test_ushi_hitsuji(self) -> None:
        assert frozenset({TwelveBranch.USHI, TwelveBranch.HITSUJI}) in ROKUCHUU

    def test_tora_saru(self) -> None:
        assert frozenset({TwelveBranch.TORA, TwelveBranch.SARU}) in ROKUCHUU

    def test_u_tori(self) -> None:
        assert frozenset({TwelveBranch.U, TwelveBranch.TORI}) in ROKUCHUU

    def test_tatsu_inu(self) -> None:
        assert frozenset({TwelveBranch.TATSU, TwelveBranch.INU}) in ROKUCHUU

    def test_mi_i(self) -> None:
        assert frozenset({TwelveBranch.MI, TwelveBranch.I}) in ROKUCHUU


class TestSankei:
    def test_has_2_groups(self) -> None:
        assert len(SANKEI) == 2

    def test_tora_mi_saru(self) -> None:
        assert frozenset({TwelveBranch.TORA, TwelveBranch.MI, TwelveBranch.SARU}) in SANKEI

    def test_ushi_inu_hitsuji(self) -> None:
        assert frozenset({TwelveBranch.USHI, TwelveBranch.INU, TwelveBranch.HITSUJI}) in SANKEI


class TestJikei:
    def test_has_4_branches(self) -> None:
        assert len(JIKEI) == 4

    def test_members(self) -> None:
        assert TwelveBranch.TATSU in JIKEI
        assert TwelveBranch.UMA in JIKEI
        assert TwelveBranch.TORI in JIKEI
        assert TwelveBranch.I in JIKEI


class TestRikugai:
    def test_has_6_pairs(self) -> None:
        assert len(RIKUGAI) == 6

    def test_ne_hitsuji(self) -> None:
        assert frozenset({TwelveBranch.NE, TwelveBranch.HITSUJI}) in RIKUGAI

    def test_ushi_uma(self) -> None:
        assert frozenset({TwelveBranch.USHI, TwelveBranch.UMA}) in RIKUGAI

    def test_tora_mi(self) -> None:
        assert frozenset({TwelveBranch.TORA, TwelveBranch.MI}) in RIKUGAI

    def test_u_tatsu(self) -> None:
        assert frozenset({TwelveBranch.U, TwelveBranch.TATSU}) in RIKUGAI

    def test_saru_i(self) -> None:
        assert frozenset({TwelveBranch.SARU, TwelveBranch.I}) in RIKUGAI

    def test_tori_inu(self) -> None:
        assert frozenset({TwelveBranch.TORI, TwelveBranch.INU}) in RIKUGAI
