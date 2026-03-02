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
    """三柱+蔵干から人体図の十大主星5星を算出.

    配置（書籍 p.53 準拠）:
      ①北(頭)=日干×年干, ②南(腹)=日干×月干,
      ③東=日干×年支蔵干, ④中央(胸)=日干×月支蔵干, ⑤西=日干×日支蔵干
    """
    day_stem = pillars.day.stem
    return MajorStarChart(
        north=school.determine_major_star(day_stem, pillars.year.stem),  # ① 年干
        south=school.determine_major_star(day_stem, pillars.month.stem),  # ② 月干
        east=school.determine_major_star(day_stem, hidden_stems["year"].hongen),  # ③ 年支蔵干
        center=school.determine_major_star(day_stem, hidden_stems["month"].hongen),  # ④ 月支蔵干
        west=school.determine_major_star(day_stem, hidden_stems["day"].hongen),  # ⑤ 日支蔵干
    )
