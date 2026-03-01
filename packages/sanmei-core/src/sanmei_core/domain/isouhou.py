"""位相法（合冲刑害）のドメインモデル."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.kanshi import TenStem, TwelveBranch


class StemInteractionType(Enum):
    """十干の相互作用."""

    GOU = "合"


class BranchInteractionType(Enum):
    """十二支の相互作用."""

    RIKUGOU = "六合"
    SANGOU = "三合局"
    ROKUCHUU = "六冲"
    KEI = "刑"
    JIKEI = "自刑"
    RIKUGAI = "六害"


class StemInteraction(BaseModel, frozen=True):
    """十干の相互作用結果."""

    type: StemInteractionType
    stems: tuple[TenStem, TenStem]
    result_gogyo: GoGyo


class BranchInteraction(BaseModel, frozen=True):
    """十二支の相互作用結果."""

    type: BranchInteractionType
    branches: tuple[TwelveBranch, ...]  # 2支 or 3支
    result_gogyo: GoGyo | None  # 合の場合のみ


class IsouhouResult(BaseModel, frozen=True):
    """位相法の分析結果."""

    stem_interactions: tuple[StemInteraction, ...]
    branch_interactions: tuple[BranchInteraction, ...]
