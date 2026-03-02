"""五行バランスの算出."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.tables.gogyo import STEM_TO_GOGYO


def _count_stems(stems: list[TenStem]) -> GoGyoCount:
    """十干リストから五行カウントを算出."""
    counts = {g: 0 for g in GoGyo}
    for stem in stems:
        counts[STEM_TO_GOGYO[stem]] += 1
    return GoGyoCount(
        wood=counts[GoGyo.WOOD],
        fire=counts[GoGyo.FIRE],
        earth=counts[GoGyo.EARTH],
        metal=counts[GoGyo.METAL],
        water=counts[GoGyo.WATER],
    )


def _collect_hidden_stems(hidden_stems: dict[str, HiddenStems]) -> list[TenStem]:
    """蔵干から全ての十干を収集."""
    result: list[TenStem] = []
    for hs in hidden_stems.values():
        result.append(hs.hongen)
        if hs.chuugen is not None:
            result.append(hs.chuugen)
        if hs.shogen is not None:
            result.append(hs.shogen)
    return result


def _add_counts(a: GoGyoCount, b: GoGyoCount) -> GoGyoCount:
    """2つの GoGyoCount を合算."""
    return GoGyoCount(
        wood=a.wood + b.wood,
        fire=a.fire + b.fire,
        earth=a.earth + b.earth,
        metal=a.metal + b.metal,
        water=a.water + b.water,
    )


def calculate_gogyo_balance(
    pillars: ThreePillars,
    hidden_stems: dict[str, HiddenStems],
) -> GoGyoBalance:
    """三柱と蔵干から五行バランスを算出."""
    stem_list = [pillars.year.stem, pillars.month.stem, pillars.day.stem]
    stem_count = _count_stems(stem_list)

    branch_stems = _collect_hidden_stems(hidden_stems)
    branch_count = _count_stems(branch_stems)

    total_count = _add_counts(stem_count, branch_count)

    # dominant: 最多の五行（同数の場合は GoGyo の定義順で最初）
    dominant = max(GoGyo, key=lambda g: total_count.get(g))

    # lacking: カウント0の五行
    lacking = tuple(g for g in GoGyo if total_count.get(g) == 0)

    day_stem_gogyo = STEM_TO_GOGYO[pillars.day.stem]

    return GoGyoBalance(
        stem_count=stem_count,
        branch_count=branch_count,
        total_count=total_count,
        dominant=dominant,
        lacking=lacking,
        day_stem_gogyo=day_stem_gogyo,
    )
