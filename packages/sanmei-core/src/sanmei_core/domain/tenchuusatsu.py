"""天中殺（てんちゅうさつ）のドメインモデル."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from sanmei_core.domain.kanshi import TwelveBranch


class TenchuusatsuType(Enum):
    """天中殺の六種類."""

    NE_USHI = "子丑天中殺"
    TORA_U = "寅卯天中殺"
    TATSU_MI = "辰巳天中殺"
    UMA_HITSUJI = "午未天中殺"
    SARU_TORI = "申酉天中殺"
    INU_I = "戌亥天中殺"


class Tenchuusatsu(BaseModel, frozen=True):
    """天中殺."""

    type: TenchuusatsuType
    branches: tuple[TwelveBranch, TwelveBranch]
