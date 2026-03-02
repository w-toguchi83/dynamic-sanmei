"""十大主星の算出."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.meishiki import MajorStarChart
from sanmei_core.domain.pillar import ThreePillars

if TYPE_CHECKING:
    from sanmei_core.protocols.school import SchoolProtocol


def calculate_major_star_chart(
    pillars: ThreePillars,
    hidden_stems: dict[str, HiddenStems],
    school: SchoolProtocol,
) -> MajorStarChart:
    """三柱+蔵干から人体図の十大主星5星を算出."""
    day_stem = pillars.day.stem
    return MajorStarChart(
        north=school.determine_major_star(day_stem, pillars.year.stem),
        east=school.determine_major_star(day_stem, pillars.month.stem),
        center=school.determine_major_star(day_stem, hidden_stems["day"].hongen),
        west=school.determine_major_star(day_stem, hidden_stems["month"].hongen),
        south=school.determine_major_star(day_stem, hidden_stems["year"].hongen),
    )
