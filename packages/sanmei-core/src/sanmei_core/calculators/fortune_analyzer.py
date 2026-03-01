"""命式×運勢の相互作用分析."""

from __future__ import annotations

from sanmei_core.calculators.isouhou import (
    analyze_branch_interactions,
    analyze_stem_interactions,
)
from sanmei_core.domain.fortune import FortuneInteraction
from sanmei_core.domain.isouhou import IsouhouResult
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.meishiki import Meishiki


def analyze_fortune_interaction(
    meishiki: Meishiki,
    period_kanshi: Kanshi,
) -> FortuneInteraction:
    """大運/年運の干支と命式の相互作用を分析.

    命式の三柱の天干・地支と大運/年運の天干・地支の間で
    合冲刑害を検出する。命式内部の相互作用は除外し、
    大運/年運との相互作用のみを返す。
    """
    # 命式の天干 + 大運天干
    all_stems = [
        meishiki.pillars.year.stem,
        meishiki.pillars.month.stem,
        meishiki.pillars.day.stem,
        period_kanshi.stem,
    ]
    stem_interactions = analyze_stem_interactions(all_stems)

    # 命式の地支 + 大運地支
    all_branches = [
        meishiki.pillars.year.branch,
        meishiki.pillars.month.branch,
        meishiki.pillars.day.branch,
        period_kanshi.branch,
    ]
    branch_interactions = analyze_branch_interactions(all_branches)

    # 命式内部の相互作用は除外（大運/年運との相互作用のみ）
    # → period_kanshi の stem/branch が含まれるもののみフィルタ
    filtered_stems = [si for si in stem_interactions if period_kanshi.stem in si.stems]
    filtered_branches = [bi for bi in branch_interactions if period_kanshi.branch in bi.branches]

    return FortuneInteraction(
        period_kanshi=period_kanshi,
        isouhou=IsouhouResult(
            stem_interactions=tuple(filtered_stems),
            branch_interactions=tuple(filtered_branches),
        ),
        affected_stars=None,
    )
