"""蔵干特定（ぞうかんとくてい）のドメインモデル.

節入り日からの経過日数により、各地支の蔵干（初元/中元/本元）から
実際に適用される蔵干を特定する。
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from sanmei_core.domain.kanshi import TenStem


class HiddenStemType(StrEnum):
    """蔵干の区分."""

    SHOGEN = "初元"
    CHUUGEN = "中元"
    HONGEN = "本元"


class ActiveHiddenStem(BaseModel, frozen=True):
    """蔵干特定結果 — 日数で選ばれた蔵干."""

    stem: TenStem
    element: HiddenStemType


class ZoukanTokutei(BaseModel, frozen=True):
    """蔵干特定 — 三柱の蔵干特定結果."""

    days_from_setsuiri: int
    year: ActiveHiddenStem
    month: ActiveHiddenStem
    day: ActiveHiddenStem
