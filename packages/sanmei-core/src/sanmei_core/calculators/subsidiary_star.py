"""十二大従星の算出."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.meishiki import SubsidiaryStarChart
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import SubsidiaryStar

if TYPE_CHECKING:
    from sanmei_core.protocols.school import SchoolProtocol

JUUNIUN_ORDER: tuple[SubsidiaryStar, ...] = (
    SubsidiaryStar.TENSHOU,  # 帝旺 (0)
    SubsidiaryStar.TENDOU,  # 衰   (1)
    SubsidiaryStar.TENKO,  # 病   (2)
    SubsidiaryStar.TENKYOKU,  # 死   (3)
    SubsidiaryStar.TENKU,  # 墓   (4)
    SubsidiaryStar.TENCHI,  # 絶   (5)
    SubsidiaryStar.TENPOU,  # 胎   (6)
    SubsidiaryStar.TENIN,  # 養   (7)
    SubsidiaryStar.TENKI,  # 長生 (8)
    SubsidiaryStar.TENKOU,  # 沐浴 (9)
    SubsidiaryStar.TENNAN,  # 冠帯 (10)
    SubsidiaryStar.TENROKU,  # 建禄 (11)
)


def calculate_subsidiary_star(
    day_stem: TenStem,
    target_branch: TwelveBranch,
    school: SchoolProtocol,
) -> SubsidiaryStar:
    """日干と対象地支から十二大従星を算出.

    帝旺支から対象地支までの順方向距離で十二運を決定。
    """
    teiou = school.get_teiou_branch(day_stem)
    distance = (target_branch.value - teiou.value) % 12
    return JUUNIUN_ORDER[distance]


def calculate_subsidiary_star_chart(
    pillars: ThreePillars,
    day_stem: TenStem,
    school: SchoolProtocol,
) -> SubsidiaryStarChart:
    """三柱から十二大従星3つを算出."""
    return SubsidiaryStarChart(
        year=calculate_subsidiary_star(day_stem, pillars.year.branch, school),
        month=calculate_subsidiary_star(day_stem, pillars.month.branch, school),
        day=calculate_subsidiary_star(day_stem, pillars.day.branch, school),
    )
