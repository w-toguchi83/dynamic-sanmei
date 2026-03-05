"""相性鑑定（二人の命式の比較分析）.

docs/domain/09_Chapter9_Appraisal_Techniques.md 9.2 準拠。
"""

from __future__ import annotations

from sanmei_core.calculators.isouhou import (
    analyze_branch_interactions,
    analyze_stem_interactions,
)
from sanmei_core.domain.compatibility import (
    CompatibilityResult,
    CrossIsouhou,
    DayPillarRelation,
    GoGyoComplement,
    NikkanRelation,
    NikkanRelationType,
    TenchuusatsuCompatibility,
    TenchuusatsuRelation,
)
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.meishiki import Meishiki
from sanmei_core.domain.tenchuusatsu import TenchuusatsuType
from sanmei_core.tables.gogyo import SOUGOU, SOUKOKU, STEM_TO_GOGYO
from sanmei_core.tables.isouhou import RIKUGOU, ROKUCHUU, STEM_GOU

# 対冲天中殺ペア: 子丑⟺午未, 寅卯⟺申酉, 辰巳⟺戌亥
_OPPOSING_TENCHUU: set[frozenset[TenchuusatsuType]] = {
    frozenset({TenchuusatsuType.NE_USHI, TenchuusatsuType.UMA_HITSUJI}),
    frozenset({TenchuusatsuType.TORA_U, TenchuusatsuType.SARU_TORI}),
    frozenset({TenchuusatsuType.TATSU_MI, TenchuusatsuType.INU_I}),
}


def _analyze_nikkan(stem_a: TenStem, stem_b: TenStem) -> NikkanRelation:
    """日干同士の関係を分析."""
    gogyo_a = STEM_TO_GOGYO[stem_a]
    gogyo_b = STEM_TO_GOGYO[stem_b]

    # 干合チェック
    key = frozenset({stem_a, stem_b})
    if key in STEM_GOU:
        return NikkanRelation(
            stem_a=stem_a,
            stem_b=stem_b,
            gogyo_a=gogyo_a,
            gogyo_b=gogyo_b,
            relation_type=NikkanRelationType.KANGOU,
            kangou_gogyo=STEM_GOU[key],
        )

    # 五行関係
    if gogyo_a == gogyo_b:
        rel = NikkanRelationType.HIKAKU
    elif SOUGOU[gogyo_a] == gogyo_b or SOUGOU[gogyo_b] == gogyo_a:
        rel = NikkanRelationType.SOUGOU
    elif SOUKOKU[gogyo_a] == gogyo_b or SOUKOKU[gogyo_b] == gogyo_a:
        rel = NikkanRelationType.SOUKOKU
    else:
        # 相生でも相剋でもない場合（通常到達しない）
        rel = NikkanRelationType.HIKAKU

    return NikkanRelation(
        stem_a=stem_a,
        stem_b=stem_b,
        gogyo_a=gogyo_a,
        gogyo_b=gogyo_b,
        relation_type=rel,
    )


def _analyze_day_pillar(meishiki_a: Meishiki, meishiki_b: Meishiki) -> DayPillarRelation:
    """日柱同士の関係を分析.

    天地徳合: 日干が干合かつ日支が六合
    天剋地冲: 日干が相剋かつ日支が六冲
    """
    stem_a = meishiki_a.pillars.day.stem
    stem_b = meishiki_b.pillars.day.stem
    branch_a = meishiki_a.pillars.day.branch
    branch_b = meishiki_b.pillars.day.branch

    stem_key = frozenset({stem_a, stem_b})
    branch_key = frozenset({branch_a, branch_b})

    # 天地徳合: 干合 + 六合
    has_kangou = stem_key in STEM_GOU
    has_rikugou = branch_key in RIKUGOU
    has_tokugou = has_kangou and has_rikugou

    tokugou_stem_gogyo = STEM_GOU[stem_key] if has_tokugou else None
    tokugou_branch_gogyo = RIKUGOU[branch_key] if has_tokugou else None

    # 天剋地冲: 相剋 + 六冲
    gogyo_a = STEM_TO_GOGYO[stem_a]
    gogyo_b = STEM_TO_GOGYO[stem_b]
    has_soukoku = SOUKOKU[gogyo_a] == gogyo_b or SOUKOKU[gogyo_b] == gogyo_a
    has_rokuchuu = branch_key in ROKUCHUU
    has_tenkoku = has_soukoku and has_rokuchuu

    return DayPillarRelation(
        has_tenchi_tokugou=has_tokugou,
        tokugou_stem_gogyo=tokugou_stem_gogyo,
        tokugou_branch_gogyo=tokugou_branch_gogyo,
        has_tenkoku_chichuu=has_tenkoku,
    )


def _analyze_gogyo_complement(meishiki_a: Meishiki, meishiki_b: Meishiki) -> GoGyoComplement:
    """五行バランスの補完関係を分析."""
    lacking_a = tuple(meishiki_a.gogyo_balance.lacking)
    lacking_b = tuple(meishiki_b.gogyo_balance.lacking)

    # Bが持つ五行でAの欠を補えるもの
    b_has = {g for g in GoGyo if g not in meishiki_b.gogyo_balance.lacking}
    complemented_by_b = tuple(g for g in lacking_a if g in b_has)

    # Aが持つ五行でBの欠を補えるもの
    a_has = {g for g in GoGyo if g not in meishiki_a.gogyo_balance.lacking}
    complemented_by_a = tuple(g for g in lacking_b if g in a_has)

    return GoGyoComplement(
        lacking_a=lacking_a,
        lacking_b=lacking_b,
        complemented_by_b=complemented_by_b,
        complemented_by_a=complemented_by_a,
    )


def _classify_tenchuu_relation(
    type_a: TenchuusatsuType,
    type_b: TenchuusatsuType,
) -> TenchuusatsuRelation:
    """天中殺の組み合わせタイプを判定."""
    if type_a == type_b:
        return TenchuusatsuRelation.SAME
    key = frozenset({type_a, type_b})
    if key in _OPPOSING_TENCHUU:
        return TenchuusatsuRelation.OPPOSING
    return TenchuusatsuRelation.OTHER


def _analyze_tenchuusatsu_compat(
    meishiki_a: Meishiki,
    meishiki_b: Meishiki,
) -> TenchuusatsuCompatibility:
    """天中殺の相性を分析.

    相手の命式の地支に自分の天中殺支が含まれるかチェック。
    同中殺/対冲天中殺も判定。
    """
    tc_a = meishiki_a.tenchuusatsu
    tc_b = meishiki_b.tenchuusatsu

    b_branches: set[TwelveBranch] = {
        meishiki_b.pillars.year.branch,
        meishiki_b.pillars.month.branch,
        meishiki_b.pillars.day.branch,
    }
    a_branches: set[TwelveBranch] = {
        meishiki_a.pillars.year.branch,
        meishiki_a.pillars.month.branch,
        meishiki_a.pillars.day.branch,
    }

    # Aの天中殺支がBの命式にあるか
    a_in_b = tuple(br for br in tc_a.branches if br in b_branches)
    # Bの天中殺支がAの命式にあるか
    b_in_a = tuple(br for br in tc_b.branches if br in a_branches)

    relation = _classify_tenchuu_relation(tc_a.type, tc_b.type)

    return TenchuusatsuCompatibility(
        type_a=tc_a.type,
        type_b=tc_b.type,
        relation=relation,
        a_branches_in_b=a_in_b,
        b_branches_in_a=b_in_a,
    )


def _analyze_cross_isouhou(meishiki_a: Meishiki, meishiki_b: Meishiki) -> CrossIsouhou:
    """二人の命式間でクロスチャートの位相法分析.

    双方の天干・地支を合わせて合・冲・刑・害・半会・方三位・破を検出。
    """
    stems_a = [
        meishiki_a.pillars.year.stem,
        meishiki_a.pillars.month.stem,
        meishiki_a.pillars.day.stem,
    ]
    stems_b = [
        meishiki_b.pillars.year.stem,
        meishiki_b.pillars.month.stem,
        meishiki_b.pillars.day.stem,
    ]

    branches_a = [
        meishiki_a.pillars.year.branch,
        meishiki_a.pillars.month.branch,
        meishiki_a.pillars.day.branch,
    ]
    branches_b = [
        meishiki_b.pillars.year.branch,
        meishiki_b.pillars.month.branch,
        meishiki_b.pillars.day.branch,
    ]

    all_stems = stems_a + stems_b
    all_branches = branches_a + branches_b

    return CrossIsouhou(
        stem_interactions=tuple(analyze_stem_interactions(all_stems)),
        branch_interactions=tuple(analyze_branch_interactions(all_branches)),
    )


def analyze_compatibility(meishiki_a: Meishiki, meishiki_b: Meishiki) -> CompatibilityResult:
    """二人の命式から相性を総合分析.

    Parameters
    ----------
    meishiki_a : Meishiki
        一人目の命式
    meishiki_b : Meishiki
        二人目の命式

    Returns
    -------
    CompatibilityResult
        相性鑑定結果

    """
    return CompatibilityResult(
        nikkan_relation=_analyze_nikkan(
            meishiki_a.pillars.day.stem,
            meishiki_b.pillars.day.stem,
        ),
        day_pillar_relation=_analyze_day_pillar(meishiki_a, meishiki_b),
        gogyo_complement=_analyze_gogyo_complement(meishiki_a, meishiki_b),
        tenchuusatsu_compatibility=_analyze_tenchuusatsu_compat(meishiki_a, meishiki_b),
        cross_isouhou=_analyze_cross_isouhou(meishiki_a, meishiki_b),
    )
