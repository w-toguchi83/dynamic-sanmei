"""MeishikiCalculator — 命式算出の統合ファサード."""

from __future__ import annotations

from datetime import datetime, tzinfo

from sanmei_core.calculators.gogyo_balance import calculate_gogyo_balance
from sanmei_core.calculators.major_star import calculate_major_star_chart
from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.shimeisei import calculate_shimeisei
from sanmei_core.calculators.shukumei_chuusatsu import calculate_shukumei_chuusatsu
from sanmei_core.calculators.subsidiary_star import calculate_subsidiary_star_chart
from sanmei_core.calculators.tenchuusatsu import calculate_tenchuusatsu
from sanmei_core.calculators.zoukan_tokutei import determine_active_hidden_stem
from sanmei_core.constants import JST
from sanmei_core.domain.meishiki import Meishiki
from sanmei_core.domain.zoukan_tokutei import ZoukanTokutei
from sanmei_core.protocols.school import SchoolProtocol


class MeishikiCalculator:
    """西暦日時から完全な命式を算出する統合ファサード."""

    def __init__(
        self,
        school: SchoolProtocol,
        *,
        tz: tzinfo | None = None,
    ) -> None:
        self._school = school
        self._tz = tz or JST
        self._calendar = SanmeiCalendar(school.get_setsuiri_provider(), tz=self._tz)

    def calculate(self, dt: datetime) -> Meishiki:
        """西暦日時から完全な命式を算出."""
        pillars = self._calendar.three_pillars(dt)
        hidden_stems = {
            "year": self._school.get_hidden_stems(pillars.year.branch),
            "month": self._school.get_hidden_stems(pillars.month.branch),
            "day": self._school.get_hidden_stems(pillars.day.branch),
        }

        # 蔵干特定: 節入り日からの経過日数で蔵干を特定
        setsuiri_date = self._calendar.get_setsuiri_for_date(dt)
        local_dt = dt.astimezone(self._tz)
        setsuiri_local = setsuiri_date.datetime_utc.astimezone(self._tz)
        days_from_setsuiri = (local_dt.date() - setsuiri_local.date()).days + 1
        zoukan_tokutei = ZoukanTokutei(
            days_from_setsuiri=days_from_setsuiri,
            year=determine_active_hidden_stem(
                pillars.year.branch,
                hidden_stems["year"],
                days_from_setsuiri,
            ),
            month=determine_active_hidden_stem(
                pillars.month.branch,
                hidden_stems["month"],
                days_from_setsuiri,
            ),
            day=determine_active_hidden_stem(
                pillars.day.branch,
                hidden_stems["day"],
                days_from_setsuiri,
            ),
        )

        major_stars = calculate_major_star_chart(pillars, hidden_stems, self._school)
        subsidiary_stars = calculate_subsidiary_star_chart(pillars, pillars.day.stem, self._school)
        shimeisei = calculate_shimeisei(pillars.day.stem, pillars.year.stem, self._school)
        tenchuusatsu = calculate_tenchuusatsu(pillars.day)
        shukumei_chuusatsu = tuple(calculate_shukumei_chuusatsu(pillars, tenchuusatsu))
        gogyo_balance = calculate_gogyo_balance(pillars, hidden_stems)
        return Meishiki(
            pillars=pillars,
            hidden_stems=hidden_stems,
            zoukan_tokutei=zoukan_tokutei,
            major_stars=major_stars,
            subsidiary_stars=subsidiary_stars,
            shimeisei=shimeisei,
            tenchuusatsu=tenchuusatsu,
            shukumei_chuusatsu=shukumei_chuusatsu,
            gogyo_balance=gogyo_balance,
        )
