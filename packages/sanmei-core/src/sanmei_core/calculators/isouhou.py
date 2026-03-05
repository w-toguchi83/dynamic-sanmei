"""位相法（合・冲・刑・害・半会・方三位・破）の判定."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations

from sanmei_core.domain.isouhou import (
    BranchInteraction,
    BranchInteractionType,
    IsouhouResult,
    StemInteraction,
    StemInteractionType,
)
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.tables.isouhou import (
    HA,
    HANKAI,
    HOUSANI,
    JIKEI,
    RIKUGAI,
    RIKUGOU,
    ROKUCHUU,
    SANGOU,
    SANKEI,
    STEM_GOU,
)


def analyze_stem_interactions(
    stems: Sequence[TenStem],
) -> list[StemInteraction]:
    """天干の組み合わせから合を検出."""
    result: list[StemInteraction] = []
    for a, b in combinations(stems, 2):
        key = frozenset({a, b})
        if key in STEM_GOU:
            result.append(
                StemInteraction(
                    type=StemInteractionType.GOU,
                    stems=(a, b),
                    result_gogyo=STEM_GOU[key],
                )
            )
    return result


def analyze_branch_interactions(
    branches: Sequence[TwelveBranch],
) -> list[BranchInteraction]:
    """地支の組み合わせから六合・三合・半会・方三位・冲・刑・害・破を検出."""
    result: list[BranchInteraction] = []
    branch_set = frozenset(branches)

    # 六合（2支ペア）
    for a, b in combinations(branches, 2):
        key = frozenset({a, b})
        if key in RIKUGOU:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.RIKUGOU,
                    branches=(a, b),
                    result_gogyo=RIKUGOU[key],
                )
            )

    # 三合局（3支）
    sangou_found: set[frozenset[TwelveBranch]] = set()
    for sangou_set, gogyo in SANGOU:
        if sangou_set <= branch_set:
            sangou_found.add(sangou_set)
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.SANGOU,
                    branches=tuple(sangou_set),
                    result_gogyo=gogyo,
                )
            )

    # 半会（三合局の2支ペア、完全な三合局が成立していない場合のみ）
    for hankai_set, gogyo in HANKAI:
        if hankai_set <= branch_set:
            # この半会ペアが既に成立した三合局の部分でないか確認
            is_part_of_sangou = any(hankai_set <= s for s in sangou_found)
            if not is_part_of_sangou:
                result.append(
                    BranchInteraction(
                        type=BranchInteractionType.HANKAI,
                        branches=tuple(hankai_set),
                        result_gogyo=gogyo,
                    )
                )

    # 方三位（季節の3支）
    for housani_set, gogyo in HOUSANI:
        if housani_set <= branch_set:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.HOUSANI,
                    branches=tuple(housani_set),
                    result_gogyo=gogyo,
                )
            )

    # 六冲（2支ペア）
    for a, b in combinations(branches, 2):
        key = frozenset({a, b})
        if key in ROKUCHUU:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.ROKUCHUU,
                    branches=(a, b),
                    result_gogyo=None,
                )
            )

    # 三刑（3支）
    for sankei_set in SANKEI:
        if sankei_set <= branch_set:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.KEI,
                    branches=tuple(sankei_set),
                    result_gogyo=None,
                )
            )

    # 自刑（同じ支が2つ以上）
    for branch in branches:
        if branch in JIKEI and branches.count(branch) >= 2:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.JIKEI,
                    branches=(branch, branch),
                    result_gogyo=None,
                )
            )
            break  # 同一自刑は1回だけ

    # 六害（2支ペア）
    for a, b in combinations(branches, 2):
        key = frozenset({a, b})
        if key in RIKUGAI:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.RIKUGAI,
                    branches=(a, b),
                    result_gogyo=None,
                )
            )

    # 破（2支ペア）
    for a, b in combinations(branches, 2):
        key = frozenset({a, b})
        if key in HA:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.HA,
                    branches=(a, b),
                    result_gogyo=None,
                )
            )

    return result


def analyze_isouhou(pillars: ThreePillars) -> IsouhouResult:
    """命式の三柱に対して位相法を適用."""
    stems = [pillars.year.stem, pillars.month.stem, pillars.day.stem]
    branches = [pillars.year.branch, pillars.month.branch, pillars.day.branch]

    return IsouhouResult(
        stem_interactions=tuple(analyze_stem_interactions(stems)),
        branch_interactions=tuple(analyze_branch_interactions(branches)),
    )
