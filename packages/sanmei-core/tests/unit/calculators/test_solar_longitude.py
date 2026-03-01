"""太陽黄経計算と MeeusSetsuiriProvider のテスト."""

from datetime import UTC, datetime, timedelta, timezone

from sanmei_core.calculators.solar_longitude import (
    MeeusSetsuiriProvider,
    datetime_to_jde,
    solar_longitude,
)
from sanmei_core.domain.calendar import SolarTerm

JST = timezone(timedelta(hours=9))


class TestSolarLongitude:
    def test_vernal_equinox_2024(self) -> None:
        """2024年春分 (3/20 12:06 UTC 付近) → 黄経 ≈ 0°."""
        dt = datetime(2024, 3, 20, 12, 0, tzinfo=UTC)
        jde = datetime_to_jde(dt)
        lon = solar_longitude(jde)
        assert abs(lon) < 0.5 or abs(lon - 360) < 0.5

    def test_summer_solstice_2024(self) -> None:
        """2024年夏至 (6/20 20:51 UTC 付近) → 黄経 ≈ 90°."""
        dt = datetime(2024, 6, 20, 21, 0, tzinfo=UTC)
        jde = datetime_to_jde(dt)
        lon = solar_longitude(jde)
        assert abs(lon - 90) < 0.5

    def test_risshun_2024(self) -> None:
        """2024年立春 (2/4 08:27 UTC 付近) → 黄経 ≈ 315°."""
        dt = datetime(2024, 2, 4, 8, 30, tzinfo=UTC)
        jde = datetime_to_jde(dt)
        lon = solar_longitude(jde)
        assert abs(lon - 315) < 0.5


class TestMeeusSetsuiriProvider:
    def test_risshun_2024(self) -> None:
        """2024年の立春は2月4日(JST)."""
        provider = MeeusSetsuiriProvider()
        risshun = provider.get_risshun(2024)
        risshun_jst = risshun.datetime_utc.astimezone(JST)
        assert risshun_jst.month == 2
        assert risshun_jst.day == 4
        assert risshun.solar_term == SolarTerm.RISSHUN

    def test_setsuiri_dates_count(self) -> None:
        """1年分の節入り日は12件."""
        provider = MeeusSetsuiriProvider()
        dates = provider.get_setsuiri_dates(2024)
        assert len(dates) == 12

    def test_setsuiri_dates_are_chronological(self) -> None:
        """節入り日は時系列順."""
        provider = MeeusSetsuiriProvider()
        dates = provider.get_setsuiri_dates(2024)
        for i in range(len(dates) - 1):
            assert dates[i].datetime_utc < dates[i + 1].datetime_utc

    def test_risshun_2024_hour_precision(self) -> None:
        """2024年立春の精度: ±1時間以内.

        実際の立春: 2024-02-04 17:27 JST = 08:27 UTC
        """
        provider = MeeusSetsuiriProvider()
        risshun = provider.get_risshun(2024)
        expected = datetime(2024, 2, 4, 8, 27, tzinfo=UTC)
        diff = abs((risshun.datetime_utc - expected).total_seconds())
        assert diff < 3600, f"Diff: {diff}s (expected < 3600s)"

    def test_supported_range(self) -> None:
        """1864-2100 の範囲で立春を計算可能."""
        provider = MeeusSetsuiriProvider()
        for year in [1864, 1900, 1950, 2000, 2024, 2050, 2100]:
            risshun = provider.get_risshun(year)
            risshun_jst = risshun.datetime_utc.astimezone(JST)
            # 立春は常に2月（±数日）
            assert risshun_jst.month == 2, f"Year {year}: month={risshun_jst.month}"
            assert 2 <= risshun_jst.day <= 5, f"Year {year}: day={risshun_jst.day}"
