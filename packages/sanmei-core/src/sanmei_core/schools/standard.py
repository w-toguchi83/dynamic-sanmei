"""標準流派の実装."""

from __future__ import annotations

from typing import Literal

from sanmei_core.calculators.solar_longitude import MeeusSetsuiriProvider
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar
from sanmei_core.protocols.setsuiri import SetsuiriProvider
from sanmei_core.tables.gogyo import GoGyoRelation, get_relation, is_same_polarity
from sanmei_core.tables.hidden_stems import STANDARD_HIDDEN_STEMS

_TEIOU_MAP: dict[TenStem, TwelveBranch] = {
    TenStem.KINOE: TwelveBranch.U,
    TenStem.KINOTO: TwelveBranch.U,
    TenStem.HINOE: TwelveBranch.UMA,
    TenStem.HINOTO: TwelveBranch.UMA,
    TenStem.TSUCHINOE: TwelveBranch.INU,
    TenStem.TSUCHINOTO: TwelveBranch.HITSUJI,
    TenStem.KANOE: TwelveBranch.TORI,
    TenStem.KANOTO: TwelveBranch.TORI,
    TenStem.MIZUNOE: TwelveBranch.NE,
    TenStem.MIZUNOTO: TwelveBranch.NE,
}

# 五行関係 + 陰陽 → 十大主星
_STAR_MAP: dict[tuple[GoGyoRelation, bool], MajorStar] = {
    (GoGyoRelation.HIKAKU, True): MajorStar.KANSAKU,
    (GoGyoRelation.HIKAKU, False): MajorStar.SEKIMON,
    (GoGyoRelation.SHOKUSHOU, True): MajorStar.HOUKAKU,
    (GoGyoRelation.SHOKUSHOU, False): MajorStar.CHOUJYO,
    (GoGyoRelation.ZAISEI, True): MajorStar.ROKUZON,
    (GoGyoRelation.ZAISEI, False): MajorStar.SHIROKU,
    (GoGyoRelation.KANSEI, False): MajorStar.SHAKI,
    (GoGyoRelation.KANSEI, True): MajorStar.KENGYU,
    (GoGyoRelation.INJYU, False): MajorStar.RYUKOU,
    (GoGyoRelation.INJYU, True): MajorStar.GYOKUDO,
}


class StandardSchool:
    """標準流派.

    蔵干: docs/domain/02_Chapter2 準拠
    陰陽判定: docs/domain/04_Chapter4 準拠
    土性帝旺: 戊→戌, 己→未
    節入り: MeeusSetsuiriProvider
    """

    @property
    def name(self) -> str:
        """流派名."""
        return "standard"

    def get_hidden_stems(self, branch: TwelveBranch) -> HiddenStems:
        """地支から蔵干を取得."""
        return STANDARD_HIDDEN_STEMS[branch]

    def determine_major_star(self, day_stem: TenStem, target_stem: TenStem) -> MajorStar:
        """日干と対象干から十大主星を判定."""
        relation = get_relation(day_stem, target_stem)
        same_pol = is_same_polarity(day_stem, target_stem)
        return _STAR_MAP[(relation, same_pol)]

    def get_teiou_branch(self, stem: TenStem) -> TwelveBranch:
        """十干の帝旺支を取得."""
        return _TEIOU_MAP[stem]

    def get_setsuiri_provider(self) -> SetsuiriProvider:
        """節入り日プロバイダを取得."""
        return MeeusSetsuiriProvider()

    def get_taiun_start_age_rounding(self) -> Literal["floor", "round"]:
        """大運起算年齢の端数処理: 切り捨て."""
        return "floor"
