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
    TenStem.KINOE: TwelveBranch.U,  # 甲 → 卯
    TenStem.KINOTO: TwelveBranch.TORA,  # 乙 → 寅 (陰干: 逆行)
    TenStem.HINOE: TwelveBranch.UMA,  # 丙 → 午
    TenStem.HINOTO: TwelveBranch.MI,  # 丁 → 巳 (陰干: 逆行)
    TenStem.TSUCHINOE: TwelveBranch.UMA,  # 戊 → 午 (丙に準ずる)
    TenStem.TSUCHINOTO: TwelveBranch.MI,  # 己 → 巳 (丁に準ずる)
    TenStem.KANOE: TwelveBranch.TORI,  # 庚 → 酉
    TenStem.KANOTO: TwelveBranch.SARU,  # 辛 → 申 (陰干: 逆行)
    TenStem.MIZUNOE: TwelveBranch.NE,  # 壬 → 子
    TenStem.MIZUNOTO: TwelveBranch.I,  # 癸 → 亥 (陰干: 逆行)
}

# 五行関係 + 陰陽 → 十大主星
_STAR_MAP: dict[tuple[GoGyoRelation, bool], MajorStar] = {
    (GoGyoRelation.HIKAKU, True): MajorStar.KANSAKU,
    (GoGyoRelation.HIKAKU, False): MajorStar.SEKIMON,
    (GoGyoRelation.SHOKUSHOU, True): MajorStar.HOUKAKU,
    (GoGyoRelation.SHOKUSHOU, False): MajorStar.CHOUJYO,
    (GoGyoRelation.ZAISEI, True): MajorStar.ROKUZON,
    (GoGyoRelation.ZAISEI, False): MajorStar.SHIROKU,
    (GoGyoRelation.KANSEI, True): MajorStar.SHAKI,  # 官星・同陰陽 → 車騎星
    (GoGyoRelation.KANSEI, False): MajorStar.KENGYU,  # 官星・異陰陽 → 牽牛星
    (GoGyoRelation.INJYU, True): MajorStar.RYUKOU,  # 印綬・同陰陽 → 龍高星
    (GoGyoRelation.INJYU, False): MajorStar.GYOKUDO,  # 印綬・異陰陽 → 玉堂星
}


class StandardSchool:
    """標準流派.

    蔵干: docs/domain/02_Chapter2 準拠
    陰陽判定: 書籍テーブル準拠（官星/印綬: 同陰陽→陽版, 異陰陽→陰版）
    帝旺: 陽干は正位, 陰干は逆行位（乙→寅, 丁→巳, 己→巳, 辛→申, 癸→亥）
    土性: 丙/丁に準ずる（戊→午, 己→巳）
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
