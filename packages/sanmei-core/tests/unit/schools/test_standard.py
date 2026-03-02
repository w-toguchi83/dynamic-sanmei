"""標準流派のテスト."""

from __future__ import annotations

import pytest
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar
from sanmei_core.schools.standard import StandardSchool


class TestStandardSchoolName:
    def test_name(self) -> None:
        school = StandardSchool()
        assert school.name == "standard"


class TestHiddenStems:
    def test_ne_main_is_mizunoto(self) -> None:
        school = StandardSchool()
        hs = school.get_hidden_stems(TwelveBranch.NE)
        assert hs.hongen == TenStem.MIZUNOTO

    def test_tora_all_three(self) -> None:
        school = StandardSchool()
        hs = school.get_hidden_stems(TwelveBranch.TORA)
        assert hs.hongen == TenStem.KINOE
        assert hs.chuugen == TenStem.HINOE
        assert hs.shogen == TenStem.TSUCHINOE


class TestDetermineMajorStar:
    """書籍の十大主星表を検証."""

    @pytest.mark.parametrize(
        ("day", "target", "expected"),
        [
            # 比劫: 同五行・同陰陽 → 貫索星
            (TenStem.KINOE, TenStem.KINOE, MajorStar.KANSAKU),
            # 比劫: 同五行・異陰陽 → 石門星
            (TenStem.KINOE, TenStem.KINOTO, MajorStar.SEKIMON),
            # 食傷: 日干が生む・同陰陽 → 鳳閣星
            (TenStem.KINOE, TenStem.HINOE, MajorStar.HOUKAKU),
            # 食傷: 日干が生む・異陰陽 → 調舒星
            (TenStem.KINOE, TenStem.HINOTO, MajorStar.CHOUJYO),
            # 財星: 日干が剋す・同陰陽 → 禄存星
            (TenStem.KINOE, TenStem.TSUCHINOE, MajorStar.ROKUZON),
            # 財星: 日干が剋す・異陰陽 → 司禄星
            (TenStem.KINOE, TenStem.TSUCHINOTO, MajorStar.SHIROKU),
            # 官星: 日干を剋す・同陰陽 → 車騎星
            (TenStem.KINOE, TenStem.KANOE, MajorStar.SHAKI),
            # 官星: 日干を剋す・異陰陽 → 牽牛星
            (TenStem.KINOE, TenStem.KANOTO, MajorStar.KENGYU),
            # 印綬: 日干を生む・同陰陽 → 龍高星
            (TenStem.KINOE, TenStem.MIZUNOE, MajorStar.RYUKOU),
            # 印綬: 日干を生む・異陰陽 → 玉堂星
            (TenStem.KINOE, TenStem.MIZUNOTO, MajorStar.GYOKUDO),
        ],
    )
    def test_kinoe_vs_all(self, day: TenStem, target: TenStem, expected: MajorStar) -> None:
        school = StandardSchool()
        assert school.determine_major_star(day, target) == expected

    def test_hinoe_vs_mizunoe(self) -> None:
        """丙(火) vs 壬(水): 官星・同陰陽 → 車騎星."""
        school = StandardSchool()
        assert school.determine_major_star(TenStem.HINOE, TenStem.MIZUNOE) == MajorStar.SHAKI


class TestGetTeiouBranch:
    @pytest.mark.parametrize(
        ("stem", "expected"),
        [
            (TenStem.KINOE, TwelveBranch.U),  # 甲 → 卯
            (TenStem.KINOTO, TwelveBranch.TORA),  # 乙 → 寅
            (TenStem.HINOE, TwelveBranch.UMA),  # 丙 → 午
            (TenStem.HINOTO, TwelveBranch.MI),  # 丁 → 巳
            (TenStem.TSUCHINOE, TwelveBranch.UMA),  # 戊 → 午
            (TenStem.TSUCHINOTO, TwelveBranch.MI),  # 己 → 巳
            (TenStem.KANOE, TwelveBranch.TORI),  # 庚 → 酉
            (TenStem.KANOTO, TwelveBranch.SARU),  # 辛 → 申
            (TenStem.MIZUNOE, TwelveBranch.NE),  # 壬 → 子
            (TenStem.MIZUNOTO, TwelveBranch.I),  # 癸 → 亥
        ],
    )
    def test_teiou_branch(self, stem: TenStem, expected: TwelveBranch) -> None:
        school = StandardSchool()
        assert school.get_teiou_branch(stem) == expected


class TestGetTaiunStartAgeRounding:
    def test_get_taiun_start_age_rounding(self) -> None:
        """標準流派は切り捨て."""
        school = StandardSchool()
        assert school.get_taiun_start_age_rounding() == "floor"


class TestGetSetsuiriProvider:
    def test_returns_provider(self) -> None:
        school = StandardSchool()
        provider = school.get_setsuiri_provider()
        dates = provider.get_setsuiri_dates(2024)
        assert len(dates) == 12
