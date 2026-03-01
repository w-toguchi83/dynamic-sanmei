"""位相法テーブル（合・冲・刑・害）.

docs/domain/08_Chapter8_Gou_Chuu_Kei_Gai.md 準拠。
"""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

# --- 十干合 ---
STEM_GOU: dict[frozenset[TenStem], GoGyo] = {
    frozenset({TenStem.KINOE, TenStem.TSUCHINOTO}): GoGyo.EARTH,
    frozenset({TenStem.KINOTO, TenStem.KANOE}): GoGyo.METAL,
    frozenset({TenStem.HINOE, TenStem.KANOTO}): GoGyo.WATER,
    frozenset({TenStem.HINOTO, TenStem.MIZUNOE}): GoGyo.WOOD,
    frozenset({TenStem.TSUCHINOE, TenStem.MIZUNOTO}): GoGyo.FIRE,
}

# --- 六合 ---
RIKUGOU: dict[frozenset[TwelveBranch], GoGyo] = {
    frozenset({TwelveBranch.NE, TwelveBranch.USHI}): GoGyo.EARTH,
    frozenset({TwelveBranch.TORA, TwelveBranch.I}): GoGyo.WOOD,
    frozenset({TwelveBranch.U, TwelveBranch.INU}): GoGyo.FIRE,
    frozenset({TwelveBranch.TATSU, TwelveBranch.TORI}): GoGyo.METAL,
    frozenset({TwelveBranch.MI, TwelveBranch.SARU}): GoGyo.WATER,
    frozenset({TwelveBranch.UMA, TwelveBranch.HITSUJI}): GoGyo.FIRE,
}

# --- 三合局 ---
SANGOU: list[tuple[frozenset[TwelveBranch], GoGyo]] = [
    (frozenset({TwelveBranch.I, TwelveBranch.U, TwelveBranch.HITSUJI}), GoGyo.WOOD),
    (frozenset({TwelveBranch.TORA, TwelveBranch.UMA, TwelveBranch.INU}), GoGyo.FIRE),
    (frozenset({TwelveBranch.MI, TwelveBranch.TORI, TwelveBranch.USHI}), GoGyo.METAL),
    (frozenset({TwelveBranch.SARU, TwelveBranch.NE, TwelveBranch.TATSU}), GoGyo.WATER),
]

# --- 六冲 ---
ROKUCHUU: set[frozenset[TwelveBranch]] = {
    frozenset({TwelveBranch.NE, TwelveBranch.UMA}),
    frozenset({TwelveBranch.USHI, TwelveBranch.HITSUJI}),
    frozenset({TwelveBranch.TORA, TwelveBranch.SARU}),
    frozenset({TwelveBranch.U, TwelveBranch.TORI}),
    frozenset({TwelveBranch.TATSU, TwelveBranch.INU}),
    frozenset({TwelveBranch.MI, TwelveBranch.I}),
}

# --- 三刑 ---
SANKEI: list[frozenset[TwelveBranch]] = [
    frozenset({TwelveBranch.TORA, TwelveBranch.MI, TwelveBranch.SARU}),
    frozenset({TwelveBranch.USHI, TwelveBranch.INU, TwelveBranch.HITSUJI}),
]

# --- 自刑 ---
JIKEI: set[TwelveBranch] = {
    TwelveBranch.TATSU,
    TwelveBranch.UMA,
    TwelveBranch.TORI,
    TwelveBranch.I,
}

# --- 六害 ---
RIKUGAI: set[frozenset[TwelveBranch]] = {
    frozenset({TwelveBranch.NE, TwelveBranch.HITSUJI}),
    frozenset({TwelveBranch.USHI, TwelveBranch.UMA}),
    frozenset({TwelveBranch.TORA, TwelveBranch.MI}),
    frozenset({TwelveBranch.U, TwelveBranch.TATSU}),
    frozenset({TwelveBranch.SARU, TwelveBranch.I}),
    frozenset({TwelveBranch.TORI, TwelveBranch.INU}),
}
