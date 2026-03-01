"""大運・年運のドメインモデル."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel

from sanmei_core.domain.isouhou import IsouhouResult
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.star import MajorStar


class Gender(Enum):
    """性別."""

    MALE = "男"
    FEMALE = "女"


class Taiun(BaseModel, frozen=True):
    """大運の1期間（10年）."""

    kanshi: Kanshi
    start_age: int
    end_age: int


class TaiunChart(BaseModel, frozen=True):
    """大運表."""

    direction: Literal["順行", "逆行"]
    start_age: int
    periods: tuple[Taiun, ...]


class Nenun(BaseModel, frozen=True):
    """年運（1年分）."""

    year: int
    kanshi: Kanshi
    age: int


class FortuneInteraction(BaseModel, frozen=True):
    """運勢と命式の相互作用."""

    period_kanshi: Kanshi
    isouhou: IsouhouResult
    affected_stars: tuple[MajorStar, ...] | None
