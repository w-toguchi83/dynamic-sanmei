"""蔵干特定テーブル — 蔵干表の日数境界.

節入り日からの経過日数に基づき、初元/中元/本元のいずれが適用されるかを
決定するための境界値テーブル。書籍の蔵干表に準拠。
"""

from __future__ import annotations

from typing import NamedTuple

from sanmei_core.domain.kanshi import TwelveBranch


class ZoukanBoundary(NamedTuple):
    """蔵干の日数境界.

    shogen_end: 初元の最終日（この日以下なら初元）。None は初元なし。
    chuugen_end: 中元の最終日（この日以下なら中元）。None は中元なし。
    本元はそれ以降の全日。
    """

    shogen_end: int | None
    chuugen_end: int | None


ZOUKAN_BOUNDARIES: dict[TwelveBranch, ZoukanBoundary] = {
    TwelveBranch.NE: ZoukanBoundary(None, None),  # 子: always 本元(癸)
    TwelveBranch.USHI: ZoukanBoundary(9, 12),  # 丑: 1-9初元, 10-12中元, 13+本元
    TwelveBranch.TORA: ZoukanBoundary(7, 14),  # 寅: 1-7初元, 8-14中元, 15+本元
    TwelveBranch.U: ZoukanBoundary(None, None),  # 卯: always 本元(乙)
    TwelveBranch.TATSU: ZoukanBoundary(9, 12),  # 辰: 1-9初元, 10-12中元, 13+本元
    TwelveBranch.MI: ZoukanBoundary(5, 14),  # 巳: 1-5初元, 6-14中元, 15+本元
    TwelveBranch.UMA: ZoukanBoundary(19, None),  # 午: 1-19初元, 中元なし, 20+本元
    TwelveBranch.HITSUJI: ZoukanBoundary(9, 12),  # 未: 1-9初元, 10-12中元, 13+本元
    TwelveBranch.SARU: ZoukanBoundary(10, 13),  # 申: 1-10初元, 11-13中元, 14+本元
    TwelveBranch.TORI: ZoukanBoundary(None, None),  # 酉: always 本元(辛)
    TwelveBranch.INU: ZoukanBoundary(9, 12),  # 戌: 1-9初元, 10-12中元, 13+本元
    TwelveBranch.I: ZoukanBoundary(None, 12),  # 亥: 初元なし, 1-12中元, 13+本元
}
