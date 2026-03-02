"""大運・年運算出のテスト."""

from __future__ import annotations

from datetime import UTC, datetime

from sanmei_core.calculators.fortune import (
    calculate_nenun,
    calculate_taiun,
    determine_direction,
)
from sanmei_core.constants import JST
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.fortune import Gender
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.meishiki import (
    MajorStarChart,
    Meishiki,
    SubsidiaryStarChart,
)
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType


class MockSetsuiriProvider:
    """テスト用: 固定の節入り日データを返す."""

    def __init__(self, data: dict[int, list[SetsuiriDate]]) -> None:
        self._data = data

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        return self._data.get(year, [])

    def get_risshun(self, year: int) -> SetsuiriDate:
        dates = self.get_setsuiri_dates(year)
        return next(d for d in dates if d.solar_term == SolarTerm.RISSHUN)


def _make_setsuiri(year: int, month: int, day: int, term: SolarTerm) -> SetsuiriDate:
    return SetsuiriDate(
        year=year,
        month=1,
        datetime_utc=datetime(year, month, day, 0, 0, tzinfo=UTC),
        solar_term=term,
    )


def _make_mock_provider_2024() -> MockSetsuiriProvider:
    """2024年の節入り日データ（簡略版）."""
    return MockSetsuiriProvider(
        {
            2024: [
                _make_setsuiri(2024, 2, 4, SolarTerm.RISSHUN),
                _make_setsuiri(2024, 3, 5, SolarTerm.KEICHITSU),
                _make_setsuiri(2024, 4, 4, SolarTerm.SEIMEI),
                _make_setsuiri(2024, 5, 5, SolarTerm.RIKKA),
                _make_setsuiri(2024, 6, 5, SolarTerm.BOUSHU),
                _make_setsuiri(2024, 7, 6, SolarTerm.SHOUSHO),
                _make_setsuiri(2024, 8, 7, SolarTerm.RISSHUU),
                _make_setsuiri(2024, 9, 7, SolarTerm.HAKURO),
                _make_setsuiri(2024, 10, 8, SolarTerm.KANRO),
                _make_setsuiri(2024, 11, 7, SolarTerm.RITTOU),
                _make_setsuiri(2024, 12, 7, SolarTerm.TAISETSU),
                _make_setsuiri(2025, 1, 5, SolarTerm.SHOUKAN),
            ],
            2025: [
                _make_setsuiri(2025, 2, 3, SolarTerm.RISSHUN),
                _make_setsuiri(2025, 3, 5, SolarTerm.KEICHITSU),
                _make_setsuiri(2025, 4, 4, SolarTerm.SEIMEI),
                _make_setsuiri(2025, 5, 5, SolarTerm.RIKKA),
                _make_setsuiri(2025, 6, 5, SolarTerm.BOUSHU),
                _make_setsuiri(2025, 7, 7, SolarTerm.SHOUSHO),
                _make_setsuiri(2025, 8, 7, SolarTerm.RISSHUU),
                _make_setsuiri(2025, 9, 7, SolarTerm.HAKURO),
                _make_setsuiri(2025, 10, 8, SolarTerm.KANRO),
                _make_setsuiri(2025, 11, 7, SolarTerm.RITTOU),
                _make_setsuiri(2025, 12, 7, SolarTerm.TAISETSU),
                _make_setsuiri(2026, 1, 5, SolarTerm.SHOUKAN),
            ],
        }
    )


def _make_dummy_gogyo_balance() -> GoGyoBalance:
    """テスト用ダミー五行バランス."""
    count = GoGyoCount(wood=1, fire=1, earth=1, metal=1, water=1)
    return GoGyoBalance(
        stem_count=count,
        branch_count=count,
        total_count=count,
        dominant=GoGyo.WOOD,
        lacking=(),
        day_stem_gogyo=GoGyo.WOOD,
    )


def _make_meishiki(
    month_kanshi_index: int,
    day_stem: TenStem = TenStem.KINOE,
) -> Meishiki:
    """テスト用の最小限の命式."""
    return Meishiki(
        pillars=ThreePillars(
            year=Kanshi.from_index(0),
            month=Kanshi.from_index(month_kanshi_index),
            day=Kanshi(stem=day_stem, branch=TwelveBranch.NE, index=0),
        ),
        hidden_stems={
            "year": HiddenStems(hongen=TenStem.MIZUNOTO),
            "month": HiddenStems(hongen=TenStem.MIZUNOTO),
            "day": HiddenStems(hongen=TenStem.MIZUNOTO),
        },
        major_stars=MajorStarChart(
            north=MajorStar.KANSAKU,
            east=MajorStar.KANSAKU,
            center=MajorStar.KANSAKU,
            west=MajorStar.KANSAKU,
            south=MajorStar.KANSAKU,
        ),
        subsidiary_stars=SubsidiaryStarChart(
            year=SubsidiaryStar.TENPOU,
            month=SubsidiaryStar.TENPOU,
            day=SubsidiaryStar.TENPOU,
        ),
        tenchuusatsu=Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        ),
        shukumei_chuusatsu=(),
        gogyo_balance=_make_dummy_gogyo_balance(),
    )


class TestDetermineDirection:
    def test_you_male_forward(self) -> None:
        """陽干＋男性 -> 順行."""
        assert determine_direction(TenStem.KINOE, Gender.MALE) == "順行"

    def test_in_female_forward(self) -> None:
        """陰干＋女性 -> 順行."""
        assert determine_direction(TenStem.KINOTO, Gender.FEMALE) == "順行"

    def test_in_male_reverse(self) -> None:
        """陰干＋男性 -> 逆行."""
        assert determine_direction(TenStem.KINOTO, Gender.MALE) == "逆行"

    def test_you_female_reverse(self) -> None:
        """陽干＋女性 -> 逆行."""
        assert determine_direction(TenStem.KINOE, Gender.FEMALE) == "逆行"


class TestCalculateTaiun:
    def test_forward_periods(self) -> None:
        """順行: 月柱から六十干支を順に辿る."""
        provider = _make_mock_provider_2024()
        meishiki = _make_meishiki(month_kanshi_index=14, day_stem=TenStem.KINOE)
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        chart = calculate_taiun(meishiki, birth_dt, Gender.MALE, provider, rounding="floor", num_periods=3)
        assert chart.direction == "順行"
        assert len(chart.periods) == 3
        assert chart.periods[0].kanshi.index == 15
        assert chart.periods[1].kanshi.index == 16
        assert chart.periods[2].kanshi.index == 17

    def test_reverse_periods(self) -> None:
        """逆行: 月柱から六十干支を逆に辿る."""
        provider = _make_mock_provider_2024()
        meishiki = _make_meishiki(month_kanshi_index=14, day_stem=TenStem.KINOTO)
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        chart = calculate_taiun(meishiki, birth_dt, Gender.MALE, provider, rounding="floor", num_periods=3)
        assert chart.direction == "逆行"
        assert chart.periods[0].kanshi.index == 13
        assert chart.periods[1].kanshi.index == 12
        assert chart.periods[2].kanshi.index == 11

    def test_start_age_calculated(self) -> None:
        """起算年齢が正しく計算される."""
        provider = _make_mock_provider_2024()
        meishiki = _make_meishiki(month_kanshi_index=14, day_stem=TenStem.KINOE)
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        chart = calculate_taiun(meishiki, birth_dt, Gender.MALE, provider, rounding="floor", num_periods=1)
        assert chart.start_age == 5
        assert chart.periods[0].start_age == 5
        assert chart.periods[0].end_age == 14

    def test_period_ages_sequential(self) -> None:
        """各期間の年齢が10年刻みで連続する."""
        provider = _make_mock_provider_2024()
        meishiki = _make_meishiki(month_kanshi_index=14, day_stem=TenStem.KINOE)
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        chart = calculate_taiun(meishiki, birth_dt, Gender.MALE, provider, rounding="floor", num_periods=3)
        for i in range(1, len(chart.periods)):
            assert chart.periods[i].start_age == chart.periods[i - 1].end_age + 1


class TestCalculateNenun:
    def test_basic_range(self) -> None:
        """指定年範囲の年運を算出."""
        provider = _make_mock_provider_2024()
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        result = calculate_nenun(birth_dt, provider, year_range=(2024, 2026))
        assert len(result) == 3
        assert result[0].year == 2024
        assert result[1].year == 2025
        assert result[2].year == 2026

    def test_age_calculated(self) -> None:
        """年齢が正しく計算される."""
        provider = _make_mock_provider_2024()
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        result = calculate_nenun(birth_dt, provider, year_range=(2024, 2025))
        assert result[0].age == 0
        assert result[1].age == 1

    def test_kanshi_is_year_kanshi(self) -> None:
        """年運の干支はその年の年柱干支."""
        provider = _make_mock_provider_2024()
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        result = calculate_nenun(birth_dt, provider, year_range=(2024, 2024))
        assert result[0].kanshi.index == 40
