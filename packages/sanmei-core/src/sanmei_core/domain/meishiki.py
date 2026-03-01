"""命式（めいしき）の複合ドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.shukumei_chuusatsu import ShukumeiChuusatsu
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu


class MajorStarChart(BaseModel, frozen=True):
    """十大主星の人体図（5位置）."""

    north: MajorStar
    east: MajorStar
    center: MajorStar
    west: MajorStar
    south: MajorStar


class SubsidiaryStarChart(BaseModel, frozen=True):
    """十二大従星（3位置）."""

    year: SubsidiaryStar
    month: SubsidiaryStar
    day: SubsidiaryStar


class Meishiki(BaseModel, frozen=True):
    """完全な命式."""

    pillars: ThreePillars
    hidden_stems: dict[str, HiddenStems]
    major_stars: MajorStarChart
    subsidiary_stars: SubsidiaryStarChart
    tenchuusatsu: Tenchuusatsu
    shukumei_chuusatsu: tuple[ShukumeiChuusatsu, ...]
