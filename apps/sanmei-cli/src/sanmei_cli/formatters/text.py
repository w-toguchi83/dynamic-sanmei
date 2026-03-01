"""テキスト形式フォーマッター."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanmei_core import (
        GoGyoBalance,
        Meishiki,
    )

_STEM_KANJI = "甲乙丙丁戊己庚辛壬癸"
_BRANCH_KANJI = "子丑寅卯辰巳午未申酉戌亥"


def _stem(stem_val: int) -> str:
    return _STEM_KANJI[stem_val]


def _branch(branch_val: int) -> str:
    return _BRANCH_KANJI[branch_val]


def format_meishiki(meishiki: Meishiki, dt: datetime) -> str:
    """命式をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 命式 ===")
    lines.append(
        f"生年月日: {dt.year}年{dt.month}月{dt.day}日 {dt.strftime('%H:%M')} (JST)"
    )
    lines.append("")

    # 三柱
    p = meishiki.pillars
    lines.append("【三柱】")
    lines.append(f"{'':8s}{'年柱':10s}{'月柱':10s}{'日柱':10s}")
    lines.append(
        f"{'天干':8s}{_stem(p.year.stem.value):10s}{_stem(p.month.stem.value):10s}{_stem(p.day.stem.value):10s}"
    )
    lines.append(
        f"{'地支':8s}"
        f"{_branch(p.year.branch.value):10s}"
        f"{_branch(p.month.branch.value):10s}"
        f"{_branch(p.day.branch.value):10s}"
    )
    lines.append("")

    # 十大主星
    ms = meishiki.major_stars
    lines.append("【十大主星】")
    lines.append(f"        北: {ms.north.value}")
    lines.append(f"西: {ms.west.value}  中: {ms.center.value}  東: {ms.east.value}")
    lines.append(f"        南: {ms.south.value}")
    lines.append("")

    # 十二大従星
    ss = meishiki.subsidiary_stars
    lines.append("【十二大従星】")
    lines.append(f"年: {ss.year.value}    月: {ss.month.value}    日: {ss.day.value}")
    lines.append("")

    # 天中殺
    lines.append(f"【天中殺】 {meishiki.tenchuusatsu.type.value}")
    lines.append("")

    # 宿命中殺
    if meishiki.shukumei_chuusatsu:
        positions = ", ".join(sc.position.value for sc in meishiki.shukumei_chuusatsu)
        lines.append(f"【宿命中殺】 {positions}")
    else:
        lines.append("【宿命中殺】 なし")
    lines.append("")

    # 五行バランス
    _append_gogyo_balance(lines, meishiki.gogyo_balance)

    return "\n".join(lines)


def _append_gogyo_balance(lines: list[str], gb: GoGyoBalance) -> None:
    tc = gb.total_count
    lines.append("【五行バランス】")
    lines.append(
        f"木: {tc.wood}  火: {tc.fire}  土: {tc.earth}  金: {tc.metal}  水: {tc.water}"
    )
    lacking_str = ", ".join(g.kanji for g in gb.lacking) if gb.lacking else "なし"
    lines.append(f"主: {gb.dominant.kanji}  欠: {lacking_str}")
    lines.append(f"日主五行: {gb.day_stem_gogyo.kanji}")
