"""大運四季表マッピングテーブルのテスト."""

from sanmei_core.domain.kanshi import TwelveBranch
from sanmei_core.domain.star import SubsidiaryStar
from sanmei_core.domain.taiun_shiki import LifeCycle, Season
from sanmei_core.tables.taiun_shiki import (
    BRANCH_TO_SEASON,
    SUBSIDIARY_STAR_TO_LIFE_CYCLE,
)


class TestBranchToSeason:
    def test_all_twelve_branches_mapped(self) -> None:
        assert len(BRANCH_TO_SEASON) == 12
        for branch in TwelveBranch:
            assert branch in BRANCH_TO_SEASON

    def test_spring(self) -> None:
        assert BRANCH_TO_SEASON[TwelveBranch.TORA] == Season.SPRING
        assert BRANCH_TO_SEASON[TwelveBranch.U] == Season.SPRING
        assert BRANCH_TO_SEASON[TwelveBranch.TATSU] == Season.SPRING

    def test_summer(self) -> None:
        assert BRANCH_TO_SEASON[TwelveBranch.MI] == Season.SUMMER
        assert BRANCH_TO_SEASON[TwelveBranch.UMA] == Season.SUMMER
        assert BRANCH_TO_SEASON[TwelveBranch.HITSUJI] == Season.SUMMER

    def test_autumn(self) -> None:
        assert BRANCH_TO_SEASON[TwelveBranch.SARU] == Season.AUTUMN
        assert BRANCH_TO_SEASON[TwelveBranch.TORI] == Season.AUTUMN
        assert BRANCH_TO_SEASON[TwelveBranch.INU] == Season.AUTUMN

    def test_winter(self) -> None:
        assert BRANCH_TO_SEASON[TwelveBranch.I] == Season.WINTER
        assert BRANCH_TO_SEASON[TwelveBranch.NE] == Season.WINTER
        assert BRANCH_TO_SEASON[TwelveBranch.USHI] == Season.WINTER


class TestSubsidiaryStarToLifeCycle:
    def test_all_twelve_stars_mapped(self) -> None:
        assert len(SUBSIDIARY_STAR_TO_LIFE_CYCLE) == 12
        for star in SubsidiaryStar:
            assert star in SUBSIDIARY_STAR_TO_LIFE_CYCLE

    def test_first_last(self) -> None:
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENPOU] == LifeCycle.TAIJI
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENCHI] == LifeCycle.ANOYO

    def test_middle_mappings(self) -> None:
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENNAN] == LifeCycle.SEINEN
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENSHOU] == LifeCycle.KACHOU
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENDOU] == LifeCycle.ROUJIN
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENKO] == LifeCycle.BYOUNIN
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENKYOKU] == LifeCycle.SHININ
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENKU] == LifeCycle.NYUUBO
