"""宿命中殺の算出."""

from __future__ import annotations

from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.shukumei_chuusatsu import (
    ShukumeiChuusatsu,
    ShukumeiChuusatsuPosition,
)
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu


def calculate_shukumei_chuusatsu(
    pillars: ThreePillars,
    tenchuusatsu: Tenchuusatsu,
) -> list[ShukumeiChuusatsu]:
    """三柱と天中殺から宿命中殺を判定.

    判定ルール:
    - 年支/月支/日支が天中殺の2支に含まれれば → 支の中殺
    - 年柱/月柱の地支が天中殺支であれば → その天干も中殺
    - 日干中殺は存在しない（日柱が天中殺の算出元）
    """
    tc_branches = set(tenchuusatsu.branches)
    result: list[ShukumeiChuusatsu] = []

    if pillars.year.branch in tc_branches:
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.YEAR_BRANCH))
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.YEAR_STEM))

    if pillars.month.branch in tc_branches:
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.MONTH_BRANCH))
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.MONTH_STEM))

    if pillars.day.branch in tc_branches:
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.DAY_BRANCH))

    return result
