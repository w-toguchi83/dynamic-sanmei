"""年柱計算のテスト."""

from datetime import UTC, datetime, timedelta, timezone

from sanmei_core.calculators.year_pillar import year_pillar
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

JST = timezone(timedelta(hours=9))


def _risshun(year: int, month: int, day: int, hour: int) -> SetsuiriDate:
    """テスト用ヘルパー: 立春の SetsuiriDate を JST 時刻から作成."""
    jst_dt = datetime(year, month, day, hour, 0, tzinfo=JST)
    return SetsuiriDate(
        year=year,
        month=1,
        datetime_utc=jst_dt.astimezone(UTC),
        solar_term=SolarTerm.RISSHUN,
    )


class TestYearPillar:
    def test_2024_after_risshun(self) -> None:
        """2024年立春(2/4 17:27 JST)後 → 甲辰.

        (2024 - 4) % 10 = 0 = 甲, (2024 - 4) % 12 = 4 = 辰
        """
        risshun = _risshun(2024, 2, 4, 18)  # 立春の1時間後
        dt = datetime(2024, 3, 1, 12, 0, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.TATSU

    def test_2024_before_risshun(self) -> None:
        """2024年立春前 → 2023年 = 癸卯.

        (2023 - 4) % 10 = 9 = 癸, (2023 - 4) % 12 = 3 = 卯
        """
        risshun = _risshun(2024, 2, 4, 18)
        dt = datetime(2024, 1, 15, 12, 0, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.MIZUNOTO
        assert k.branch == TwelveBranch.U

    def test_risshun_boundary_exact(self) -> None:
        """立春の瞬間 → 当年の干支."""
        risshun = _risshun(2024, 2, 4, 17)
        dt = datetime(2024, 2, 4, 17, 0, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.KINOE  # 2024年

    def test_risshun_boundary_one_minute_before(self) -> None:
        """立春の1分前 → 前年の干支."""
        risshun = _risshun(2024, 2, 4, 17)
        dt = datetime(2024, 2, 4, 16, 59, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.MIZUNOTO  # 2023年

    def test_1864_kinoe_ne(self) -> None:
        """1864年 = 甲子 (六十干支の起点)."""
        risshun = _risshun(1864, 2, 4, 12)
        dt = datetime(1864, 6, 1, 12, 0, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.NE
        assert k.index == 0
