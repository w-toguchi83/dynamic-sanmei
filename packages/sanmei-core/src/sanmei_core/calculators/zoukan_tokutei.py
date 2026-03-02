"""蔵干特定 — 節入り日からの日数で蔵干を特定する."""

from __future__ import annotations

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TwelveBranch
from sanmei_core.domain.zoukan_tokutei import ActiveHiddenStem, HiddenStemType
from sanmei_core.tables.zoukan_tokutei import ZOUKAN_BOUNDARIES


def determine_active_hidden_stem(
    branch: TwelveBranch,
    hidden_stems: HiddenStems,
    days_from_setsuiri: int,
) -> ActiveHiddenStem:
    """地支の蔵干から日数で選択された蔵干を特定する.

    HiddenStems の hongen/chuugen/shogen は 本元/中元/初元 に対応。
    日数境界テーブルに基づき、該当する区分の蔵干を返す。

    Args:
        branch: 地支
        hidden_stems: その地支の蔵干（hongen/chuugen/shogen）
        days_from_setsuiri: 節入り日からの経過日数（節入り日含む、1始まり）

    Returns:
        選択された蔵干と区分
    """
    boundary = ZOUKAN_BOUNDARIES[branch]

    # 初元: shogen_end が設定されていて、日数がその範囲内
    if boundary.shogen_end is not None and days_from_setsuiri <= boundary.shogen_end:
        assert hidden_stems.shogen is not None
        return ActiveHiddenStem(
            stem=hidden_stems.shogen,
            element=HiddenStemType.SHOGEN,
        )

    # 中元: chuugen_end が設定されていて、日数がその範囲内
    if boundary.chuugen_end is not None and days_from_setsuiri <= boundary.chuugen_end:
        assert hidden_stems.chuugen is not None
        return ActiveHiddenStem(
            stem=hidden_stems.chuugen,
            element=HiddenStemType.CHUUGEN,
        )

    # 本元: それ以外
    return ActiveHiddenStem(stem=hidden_stems.hongen, element=HiddenStemType.HONGEN)
