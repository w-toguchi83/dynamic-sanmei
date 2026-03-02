"""SanmeiCalendar — 三柱算出の統合エントリポイント."""

from __future__ import annotations

from datetime import datetime, tzinfo

from sanmei_core.calculators.day_pillar import day_pillar
from sanmei_core.calculators.month_pillar import month_pillar
from sanmei_core.calculators.year_pillar import year_pillar
from sanmei_core.constants import JST
from sanmei_core.domain.calendar import SetsuiriDate
from sanmei_core.domain.errors import DateOutOfRangeError
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.protocols.setsuiri import SetsuiriProvider

_MIN_YEAR = 1864
_MAX_YEAR = 2100


class SanmeiCalendar:
    """西暦日付から三柱干支を算出する統合エントリポイント.

    SetsuiriProvider を注入することで、流派ごとの節入り日データに対応。
    """

    def __init__(
        self,
        setsuiri_provider: SetsuiriProvider,
        *,
        tz: tzinfo | None = None,
    ) -> None:
        self._provider = setsuiri_provider
        self._tz = tz or JST

    def three_pillars(self, dt: datetime) -> ThreePillars:
        """三柱を一括算出."""
        self._validate_range(dt)
        return ThreePillars(
            year=self._year_pillar(dt),
            month=self._month_pillar(dt),
            day=self._day_pillar(dt),
        )

    def year_pillar(self, dt: datetime) -> Kanshi:
        """年柱を算出."""
        self._validate_range(dt)
        return self._year_pillar(dt)

    def month_pillar(self, dt: datetime) -> Kanshi:
        """月柱を算出."""
        self._validate_range(dt)
        return self._month_pillar(dt)

    def day_pillar(self, dt: datetime) -> Kanshi:
        """日柱を算出."""
        self._validate_range(dt)
        return self._day_pillar(dt)

    def get_setsuiri_for_date(self, dt: datetime) -> SetsuiriDate:
        """指定日時が属する算命学月の節入り日を取得する."""
        self._validate_range(dt)
        local_dt = dt.astimezone(self._tz)
        risshun = self._provider.get_risshun(local_dt.year)
        risshun_local = risshun.datetime_utc.astimezone(self._tz)

        if local_dt < risshun_local:
            setsuiri_dates = self._provider.get_setsuiri_dates(local_dt.year - 1)
        else:
            setsuiri_dates = self._provider.get_setsuiri_dates(local_dt.year)

        sorted_dates = sorted(setsuiri_dates, key=lambda s: s.datetime_utc)
        for sd in reversed(sorted_dates):
            setsuiri_local = sd.datetime_utc.astimezone(self._tz)
            if local_dt >= setsuiri_local:
                return sd

        # 全節入り日より前 → 前年の最後の節入り日を取得
        prev_dates = self._provider.get_setsuiri_dates(local_dt.year - 1)
        return max(prev_dates, key=lambda s: s.datetime_utc)

    def _year_pillar(self, dt: datetime) -> Kanshi:
        local_dt = dt.astimezone(self._tz)
        risshun = self._provider.get_risshun(local_dt.year)
        return year_pillar(dt, risshun, tz=self._tz)

    def _month_pillar(self, dt: datetime) -> Kanshi:
        local_dt = dt.astimezone(self._tz)
        year_k = self._year_pillar(dt)

        # 年柱の年で節入り日を取得
        risshun = self._provider.get_risshun(local_dt.year)
        risshun_local = risshun.datetime_utc.astimezone(self._tz)

        if local_dt < risshun_local:
            # 立春前 → 前年の節入り日データを使用
            setsuiri_dates = self._provider.get_setsuiri_dates(local_dt.year - 1)
        else:
            setsuiri_dates = self._provider.get_setsuiri_dates(local_dt.year)

        return month_pillar(dt, setsuiri_dates, year_k.stem, tz=self._tz)

    def _day_pillar(self, dt: datetime) -> Kanshi:
        return day_pillar(dt, tz=self._tz)

    def _validate_range(self, dt: datetime) -> None:
        local_dt = dt.astimezone(self._tz)
        if local_dt.year < _MIN_YEAR or local_dt.year > _MAX_YEAR:
            raise DateOutOfRangeError(local_dt.year)
