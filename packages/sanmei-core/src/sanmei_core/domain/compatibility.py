"""相性鑑定（そうしょうかんてい）のドメインモデル.

二人の命式を比較して相性を分析する。
docs/domain/09_Chapter9_Appraisal_Techniques.md 9.2 準拠。
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.isouhou import BranchInteraction, StemInteraction
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.tenchuusatsu import TenchuusatsuType


class NikkanRelationType(Enum):
    """日干同士の関係タイプ."""

    HIKAKU = "比和"  # 同五行
    SOUGOU = "相生"  # 生じる関係
    SOUKOKU = "相剋"  # 剋す関係
    KANGOU = "干合"  # 干合


class NikkanRelation(BaseModel, frozen=True):
    """日干同士の関係."""

    stem_a: TenStem
    stem_b: TenStem
    gogyo_a: GoGyo
    gogyo_b: GoGyo
    relation_type: NikkanRelationType
    kangou_gogyo: GoGyo | None = None


class DayPillarRelation(BaseModel, frozen=True):
    """日柱同士の関係（配偶者位置の相性）.

    天地徳合: 日干が干合かつ日支が六合
    天剋地冲: 日干が相剋かつ日支が六冲
    """

    has_tenchi_tokugou: bool
    tokugou_stem_gogyo: GoGyo | None = None
    tokugou_branch_gogyo: GoGyo | None = None
    has_tenkoku_chichuu: bool


class GoGyoComplement(BaseModel, frozen=True):
    """五行の補完関係."""

    lacking_a: tuple[GoGyo, ...]
    lacking_b: tuple[GoGyo, ...]
    complemented_by_b: tuple[GoGyo, ...]
    complemented_by_a: tuple[GoGyo, ...]


class TenchuusatsuRelation(Enum):
    """天中殺の組み合わせタイプ."""

    SAME = "同中殺"
    OPPOSING = "対冲天中殺"
    OTHER = "異中殺"


class TenchuusatsuCompatibility(BaseModel, frozen=True):
    """天中殺の相性."""

    type_a: TenchuusatsuType
    type_b: TenchuusatsuType
    relation: TenchuusatsuRelation
    a_branches_in_b: tuple[TwelveBranch, ...]
    b_branches_in_a: tuple[TwelveBranch, ...]


class CrossIsouhou(BaseModel, frozen=True):
    """二人の命式間の位相法（クロスチャート分析）."""

    stem_interactions: tuple[StemInteraction, ...]
    branch_interactions: tuple[BranchInteraction, ...]


class CompatibilityResult(BaseModel, frozen=True):
    """相性鑑定の総合結果."""

    nikkan_relation: NikkanRelation
    day_pillar_relation: DayPillarRelation
    gogyo_complement: GoGyoComplement
    tenchuusatsu_compatibility: TenchuusatsuCompatibility
    cross_isouhou: CrossIsouhou
