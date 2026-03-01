"""日柱計算のテスト."""

from datetime import UTC, datetime, timedelta, timezone

from sanmei_core.calculators.day_pillar import day_pillar
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

JST = timezone(timedelta(hours=9))


class TestDayPillar:
    def test_reference_date_1900_01_01(self) -> None:
        """基準日: 1900-01-01 = 甲戌 (index 10)."""
        k = day_pillar(datetime(1900, 1, 1, tzinfo=JST))
        assert k.index == 10
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.INU

    def test_sixty_day_cycle(self) -> None:
        """60日後は同じ干支に戻る."""
        k1 = day_pillar(datetime(1900, 1, 1, tzinfo=JST))
        k2 = day_pillar(datetime(1900, 3, 2, tzinfo=JST))
        assert k1.index == k2.index

    def test_next_day(self) -> None:
        """1900-01-02 = 乙亥 (index 11)."""
        k = day_pillar(datetime(1900, 1, 2, tzinfo=JST))
        assert k.index == 11

    def test_year_2000_jan_1(self) -> None:
        """2000-01-01 の日柱.

        1900-01-01 から 36524 日後。
        (10 + 36524) % 60 = 36534 % 60 = 54
        """
        k = day_pillar(datetime(2000, 1, 1, tzinfo=JST))
        assert k.index == 54

    def test_date_before_reference(self) -> None:
        """1899-12-31 = 癸酉 (index 9)."""
        k = day_pillar(datetime(1899, 12, 31, tzinfo=JST))
        assert k.index == 9

    def test_timezone_affects_date(self) -> None:
        """UTC 23:30 は JST で翌日。異なる日柱になりうる."""
        # UTC 2000-01-01 23:30 = JST 2000-01-02 08:30
        k_utc = day_pillar(datetime(2000, 1, 1, 23, 30, tzinfo=UTC), tz=UTC)
        k_jst = day_pillar(datetime(2000, 1, 1, 23, 30, tzinfo=UTC), tz=JST)
        # JST では翌日扱いなので index が 1 違う
        assert (k_jst.index - k_utc.index) % 60 == 1
