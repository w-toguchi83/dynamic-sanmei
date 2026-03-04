"""大運四季表のドメインモデル."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.star import MajorStar, SubsidiaryStar


class Season(Enum):
    """四季."""

    SPRING = "春"  # 寅・卯・辰
    SUMMER = "夏"  # 巳・午・未
    AUTUMN = "秋"  # 申・酉・戌
    WINTER = "冬"  # 亥・子・丑


class LifeCycle(Enum):
    """一生の運気サイクル（十二大従星に対応）."""

    TAIJI = "胎児"  # 天報星
    AKAGO = "赤子"  # 天印星
    JIDOU = "児童"  # 天貴星
    SEISHONEN = "青少年"  # 天恍星
    SEINEN = "青年"  # 天南星
    SOUNEN = "壮年"  # 天禄星
    KACHOU = "家長"  # 天将星
    ROUJIN = "老人"  # 天堂星
    BYOUNIN = "病人"  # 天胡星
    SHININ = "死人"  # 天極星
    NYUUBO = "入墓"  # 天庫星
    ANOYO = "あの世"  # 天馳星


class TaiunShikiEntry(BaseModel, frozen=True):
    """大運四季表の1行."""

    label: str
    kanshi: Kanshi
    start_age: int
    end_age: int
    season: Season
    hidden_stems: HiddenStems
    major_star: MajorStar
    subsidiary_star: SubsidiaryStar
    life_cycle: LifeCycle


class TaiunShikiChart(BaseModel, frozen=True):
    """大運四季表."""

    direction: Literal["順行", "逆行"]
    start_age: int
    entries: tuple[TaiunShikiEntry, ...]
