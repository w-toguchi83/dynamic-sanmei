"""MeishikiCalculator — 命式算出の統合ファサード."""

from __future__ import annotations

from datetime import datetime, tzinfo

from sanmei_core.calculators.major_star import calculate_major_star_chart
from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.subsidiary_star import calculate_subsidiary_star_chart
from sanmei_core.calculators.tenchuusatsu import calculate_tenchuusatsu
from sanmei_core.constants import JST
from sanmei_core.domain.meishiki import Meishiki
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
        major_stars = calculate_major_star_chart(pillars, hidden_stems, self._school)
        subsidiary_stars = calculate_subsidiary_star_chart(pillars, pillars.day.stem, self._school)
        tenchuusatsu = calculate_tenchuusatsu(pillars.day)
        return Meishiki(
            pillars=pillars,
            hidden_stems=hidden_stems,
            major_stars=major_stars,
            subsidiary_stars=subsidiary_stars,
            tenchuusatsu=tenchuusatsu,
        )
