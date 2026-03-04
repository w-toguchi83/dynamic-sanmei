"""大運四季表の算出."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.calculators.subsidiary_star import calculate_subsidiary_star
from sanmei_core.domain.taiun_shiki import TaiunShikiChart, TaiunShikiEntry
from sanmei_core.tables.hidden_stems import STANDARD_HIDDEN_STEMS
from sanmei_core.tables.taiun_shiki import BRANCH_TO_SEASON, SUBSIDIARY_STAR_TO_LIFE_CYCLE

if TYPE_CHECKING:
    from sanmei_core.domain.fortune import TaiunChart
    from sanmei_core.domain.meishiki import Meishiki
    from sanmei_core.protocols.school import SchoolProtocol


def calculate_taiun_shiki(
    meishiki: Meishiki,
    taiun_chart: TaiunChart,
    school: SchoolProtocol,
) -> TaiunShikiChart:
    """命式と大運表から大運四季表を算出."""
    day_stem = meishiki.pillars.day.stem
    entries: list[TaiunShikiEntry] = []

    # 月干支行
    month_kanshi = meishiki.pillars.month
    month_sub = calculate_subsidiary_star(day_stem, month_kanshi.branch, school)
    entries.append(
        TaiunShikiEntry(
            label="月干支",
            kanshi=month_kanshi,
            start_age=0,
            end_age=max(0, taiun_chart.start_age - 1),
            season=BRANCH_TO_SEASON[month_kanshi.branch],
            hidden_stems=STANDARD_HIDDEN_STEMS[month_kanshi.branch],
            major_star=school.determine_major_star(day_stem, month_kanshi.stem),
            subsidiary_star=month_sub,
            life_cycle=SUBSIDIARY_STAR_TO_LIFE_CYCLE[month_sub],
        )
    )

    # 各大運期間
    for i, period in enumerate(taiun_chart.periods, 1):
        sub = calculate_subsidiary_star(day_stem, period.kanshi.branch, school)
        entries.append(
            TaiunShikiEntry(
                label=f"第{i}句",
                kanshi=period.kanshi,
                start_age=period.start_age,
                end_age=period.end_age,
                season=BRANCH_TO_SEASON[period.kanshi.branch],
                hidden_stems=STANDARD_HIDDEN_STEMS[period.kanshi.branch],
                major_star=school.determine_major_star(day_stem, period.kanshi.stem),
                subsidiary_star=sub,
                life_cycle=SUBSIDIARY_STAR_TO_LIFE_CYCLE[sub],
            )
        )

    return TaiunShikiChart(
        direction=taiun_chart.direction,
        start_age=taiun_chart.start_age,
        entries=tuple(entries),
    )
