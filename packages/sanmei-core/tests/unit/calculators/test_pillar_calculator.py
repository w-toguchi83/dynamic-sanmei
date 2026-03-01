# packages/sanmei-core/tests/unit/calculators/test_pillar_calculator.py
from datetime import datetime, timedelta, timezone

import pytest
from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.solar_longitude import MeeusSetsuiriProvider
from sanmei_core.domain.errors import DateOutOfRangeError
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

JST = timezone(timedelta(hours=9))


class TestSanmeiCalendar:
    def test_three_pillars_returns_all(self) -> None:
        """三柱が全て返される."""
        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        pillars = cal.three_pillars(datetime(2024, 6, 15, 12, 0, tzinfo=JST))
        assert pillars.year is not None
        assert pillars.month is not None
        assert pillars.day is not None

    def test_day_pillar_consistency(self) -> None:
        """ファサード経由の日柱が個別関数と一致."""
        from sanmei_core.calculators.day_pillar import day_pillar

        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        assert cal.day_pillar(dt) == day_pillar(dt, tz=JST)

    def test_date_out_of_range_raises(self) -> None:
        """範囲外の日付でエラー."""
        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        with pytest.raises(DateOutOfRangeError):
            cal.three_pillars(datetime(1800, 1, 1, tzinfo=JST))

    def test_date_out_of_range_future(self) -> None:
        """未来すぎる日付でエラー."""
        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        with pytest.raises(DateOutOfRangeError):
            cal.three_pillars(datetime(2200, 1, 1, tzinfo=JST))


class TestSanmeiCalendarWithMeeus:
    """MeeusSetsuiriProvider を使った統合テスト."""

    def test_2024_06_15(self) -> None:
        """2024年6月15日(JST) の三柱.

        年柱: 2024年 → (2024-4)%60=0 → 甲辰 (立春後)
        月柱: 芒種(6/5)後、小暑(7/6)前 → 午月(5月)
              甲年の午月天干: 丙+4 = 庚
        日柱: (10 + days_since_1900)%60 を計算
        """
        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        pillars = cal.three_pillars(datetime(2024, 6, 15, 12, 0, tzinfo=JST))

        # 年柱: 甲辰
        assert pillars.year.stem == TenStem.KINOE
        assert pillars.year.branch == TwelveBranch.TATSU

        # 月柱: 庚午
        assert pillars.month.stem == TenStem.KANOE
        assert pillars.month.branch == TwelveBranch.UMA
