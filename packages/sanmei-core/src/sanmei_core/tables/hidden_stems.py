"""蔵干テーブル（標準流派・算命学二十八元）.

算命学の二十八元体系に基づく。中元は三合会局で決定。
docs/domain/02_Chapter2_Basics_of_Kanshi.md Section 2.4 準拠。
"""

from __future__ import annotations

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

STANDARD_HIDDEN_STEMS: dict[TwelveBranch, HiddenStems] = {
    TwelveBranch.NE: HiddenStems(hongen=TenStem.MIZUNOTO),
    TwelveBranch.USHI: HiddenStems(hongen=TenStem.TSUCHINOTO, chuugen=TenStem.KANOTO, shogen=TenStem.MIZUNOTO),
    TwelveBranch.TORA: HiddenStems(hongen=TenStem.KINOE, chuugen=TenStem.HINOE, shogen=TenStem.TSUCHINOE),
    TwelveBranch.U: HiddenStems(hongen=TenStem.KINOTO),
    TwelveBranch.TATSU: HiddenStems(hongen=TenStem.TSUCHINOE, chuugen=TenStem.MIZUNOTO, shogen=TenStem.KINOTO),
    TwelveBranch.MI: HiddenStems(hongen=TenStem.HINOE, chuugen=TenStem.KANOE, shogen=TenStem.TSUCHINOE),
    TwelveBranch.UMA: HiddenStems(hongen=TenStem.HINOTO, shogen=TenStem.TSUCHINOTO),
    TwelveBranch.HITSUJI: HiddenStems(hongen=TenStem.TSUCHINOTO, chuugen=TenStem.KINOTO, shogen=TenStem.HINOTO),
    TwelveBranch.SARU: HiddenStems(hongen=TenStem.KANOE, chuugen=TenStem.MIZUNOE, shogen=TenStem.TSUCHINOE),
    TwelveBranch.TORI: HiddenStems(hongen=TenStem.KANOTO),
    TwelveBranch.INU: HiddenStems(hongen=TenStem.TSUCHINOE, chuugen=TenStem.HINOTO, shogen=TenStem.KANOTO),
    TwelveBranch.I: HiddenStems(hongen=TenStem.MIZUNOE, chuugen=TenStem.KINOE),
}
