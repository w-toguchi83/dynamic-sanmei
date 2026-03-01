"""蔵干テーブル（標準流派）.

docs/domain/02_Chapter2_Basics_of_Kanshi.md Section 2.4 準拠。
"""

from __future__ import annotations

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

STANDARD_HIDDEN_STEMS: dict[TwelveBranch, HiddenStems] = {
    TwelveBranch.NE: HiddenStems(main=TenStem.MIZUNOTO),
    TwelveBranch.USHI: HiddenStems(main=TenStem.TSUCHINOTO, middle=TenStem.KANOTO, minor=TenStem.MIZUNOTO),
    TwelveBranch.TORA: HiddenStems(main=TenStem.KINOE, middle=TenStem.HINOE, minor=TenStem.TSUCHINOE),
    TwelveBranch.U: HiddenStems(main=TenStem.KINOTO),
    TwelveBranch.TATSU: HiddenStems(main=TenStem.TSUCHINOE, middle=TenStem.KINOTO, minor=TenStem.MIZUNOTO),
    TwelveBranch.MI: HiddenStems(main=TenStem.HINOE, middle=TenStem.KANOE, minor=TenStem.TSUCHINOE),
    TwelveBranch.UMA: HiddenStems(main=TenStem.HINOTO, middle=TenStem.TSUCHINOTO),
    TwelveBranch.HITSUJI: HiddenStems(main=TenStem.TSUCHINOTO, middle=TenStem.HINOTO, minor=TenStem.KINOTO),
    TwelveBranch.SARU: HiddenStems(main=TenStem.KANOE, middle=TenStem.MIZUNOE, minor=TenStem.TSUCHINOE),
    TwelveBranch.TORI: HiddenStems(main=TenStem.KANOTO),
    TwelveBranch.INU: HiddenStems(main=TenStem.TSUCHINOE, middle=TenStem.KANOTO, minor=TenStem.HINOTO),
    TwelveBranch.I: HiddenStems(main=TenStem.MIZUNOE, middle=TenStem.KINOE),
}
