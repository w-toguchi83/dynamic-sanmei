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


def _is_yin_stem(stem: TenStem) -> bool:
    """陰干かを判定."""
    return stem.value % 2 == 1


def calculate_subsidiary_star(
    day_stem: TenStem,
    target_branch: TwelveBranch,
    school: SchoolProtocol,
) -> SubsidiaryStar:
    """日干と対象地支から十二大従星を算出.

    陽干: 帝旺支から順方向（増）に十二運を割り当て。
    陰干: 帝旺支から逆方向（減）に十二運を割り当て。
    """
    teiou = school.get_teiou_branch(day_stem)
    if _is_yin_stem(day_stem):
        distance = (teiou.value - target_branch.value) % 12
    else:
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
