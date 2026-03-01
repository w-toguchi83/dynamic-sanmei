"""五行関係テーブル."""

from __future__ import annotations

from enum import Enum

from sanmei_core.domain.gogyo import GoGyo, InYou
from sanmei_core.domain.kanshi import TenStem

STEM_TO_GOGYO: dict[TenStem, GoGyo] = {
    TenStem.KINOE: GoGyo.WOOD,
    TenStem.KINOTO: GoGyo.WOOD,
    TenStem.HINOE: GoGyo.FIRE,
    TenStem.HINOTO: GoGyo.FIRE,
    TenStem.TSUCHINOE: GoGyo.EARTH,
    TenStem.TSUCHINOTO: GoGyo.EARTH,
    TenStem.KANOE: GoGyo.METAL,
    TenStem.KANOTO: GoGyo.METAL,
    TenStem.MIZUNOE: GoGyo.WATER,
    TenStem.MIZUNOTO: GoGyo.WATER,
}

STEM_TO_INYOU: dict[TenStem, InYou] = {
    TenStem.KINOE: InYou.YOU,
    TenStem.KINOTO: InYou.IN,
    TenStem.HINOE: InYou.YOU,
    TenStem.HINOTO: InYou.IN,
    TenStem.TSUCHINOE: InYou.YOU,
    TenStem.TSUCHINOTO: InYou.IN,
    TenStem.KANOE: InYou.YOU,
    TenStem.KANOTO: InYou.IN,
    TenStem.MIZUNOE: InYou.YOU,
    TenStem.MIZUNOTO: InYou.IN,
}

SOUGOU: dict[GoGyo, GoGyo] = {
    GoGyo.WOOD: GoGyo.FIRE,
    GoGyo.FIRE: GoGyo.EARTH,
    GoGyo.EARTH: GoGyo.METAL,
    GoGyo.METAL: GoGyo.WATER,
    GoGyo.WATER: GoGyo.WOOD,
}
"""相生（そうしょう）: 木→火→土→金→水→木."""

SOUKOKU: dict[GoGyo, GoGyo] = {
    GoGyo.WOOD: GoGyo.EARTH,
    GoGyo.EARTH: GoGyo.WATER,
    GoGyo.WATER: GoGyo.FIRE,
    GoGyo.FIRE: GoGyo.METAL,
    GoGyo.METAL: GoGyo.WOOD,
}
"""相剋（そうこく）: 木→土→水→火→金→木."""


class GoGyoRelation(Enum):
    """日干から見た五行関係."""

    HIKAKU = "比劫"
    SHOKUSHOU = "食傷"
    ZAISEI = "財星"
    KANSEI = "官星"
    INJYU = "印綬"


def get_relation(day_stem: TenStem, target_stem: TenStem) -> GoGyoRelation:
    """日干と対象干の五行関係を判定."""
    day_g = STEM_TO_GOGYO[day_stem]
    target_g = STEM_TO_GOGYO[target_stem]
    if day_g == target_g:
        return GoGyoRelation.HIKAKU
    if SOUGOU[day_g] == target_g:
        return GoGyoRelation.SHOKUSHOU
    if SOUKOKU[day_g] == target_g:
        return GoGyoRelation.ZAISEI
    if SOUKOKU[target_g] == day_g:
        return GoGyoRelation.KANSEI
    return GoGyoRelation.INJYU


def is_same_polarity(stem_a: TenStem, stem_b: TenStem) -> bool:
    """同陰陽かを判定."""
    return STEM_TO_INYOU[stem_a] == STEM_TO_INYOU[stem_b]
