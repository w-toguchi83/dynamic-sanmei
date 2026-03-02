"""テキスト形式フォーマッター."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanmei_core import (
        GoGyoBalance,
        IsouhouResult,
        Meishiki,
        TaiunChart,
    )
    from sanmei_core.domain.fortune import Nenun
    from sanmei_core.domain.hidden_stems import HiddenStems

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

    # 干支
    p = meishiki.pillars
    lines.append("【干支】")
    lines.append(f"{'':8s}{'日':10s}{'月':10s}{'年':10s}")
    lines.append(
        f"{'天干':8s}{_stem(p.day.stem.value):10s}{_stem(p.month.stem.value):10s}{_stem(p.year.stem.value):10s}"
    )
    lines.append(
        f"{'地支':8s}"
        f"{_branch(p.day.branch.value):10s}"
        f"{_branch(p.month.branch.value):10s}"
        f"{_branch(p.year.branch.value):10s}"
    )
    lines.append("")

    # 蔵干
    _append_hidden_stems(
        lines,
        meishiki.hidden_stems,
        branches=(p.day.branch.value, p.month.branch.value, p.year.branch.value),
    )
    lines.append("")

    # 使命星
    lines.append(f"【使命星】 {meishiki.shimeisei.value}")
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
    lines.append(f"日: {ss.day.value}    月: {ss.month.value}    年: {ss.year.value}")
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


def format_taiun(chart: TaiunChart) -> str:
    """大運をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 大運 ===")
    lines.append(f"方向: {chart.direction}  開始年齢: {chart.start_age}歳")
    lines.append("")
    lines.append(f" {'期間':<8s}{'干支':<8s}{'年齢'}")
    for i, period in enumerate(chart.periods, 1):
        lines.append(
            f" {i:<8d}{period.kanshi.kanji:<8s}{period.start_age}-{period.end_age}歳"
        )
    return "\n".join(lines)


def format_nenun(nenuns: list[Nenun]) -> str:
    """年運をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 年運 ===")
    lines.append(f" {'年':<8s}{'干支':<8s}{'年齢'}")
    for nenun in nenuns:
        lines.append(f" {nenun.year:<8d}{nenun.kanshi.kanji:<8s}{nenun.age}歳")
    return "\n".join(lines)


def format_isouhou(result: IsouhouResult) -> str:
    """位相法分析結果をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 位相法（命式内） ===")

    if not result.stem_interactions and not result.branch_interactions:
        lines.append("")
        lines.append("相互作用なし")
        return "\n".join(lines)

    if result.stem_interactions:
        lines.append("")
        lines.append("【天干の合】")
        for si in result.stem_interactions:
            s1 = _stem(si.stems[0].value)
            s2 = _stem(si.stems[1].value)
            lines.append(f"{s1}-{s2} {si.type.value} → {si.result_gogyo.kanji}")

    if result.branch_interactions:
        lines.append("")
        lines.append("【地支の関係】")
        for bi in result.branch_interactions:
            branches_str = "-".join(_branch(b.value) for b in bi.branches)
            if bi.result_gogyo is not None:
                lines.append(
                    f"{branches_str} {bi.type.value} → {bi.result_gogyo.kanji}"
                )
            else:
                lines.append(f"{branches_str} {bi.type.value}")

    return "\n".join(lines)


def _stem_debug(stem: int | None) -> str:
    """蔵干のデバッグ表示（漢字+enum値）."""
    if stem is None:
        return "-"
    return f"{_STEM_KANJI[stem]}({stem})"


def _branch_debug(branch_val: int) -> str:
    return f"{_BRANCH_KANJI[branch_val]}({branch_val})"


def _append_hidden_stems(
    lines: list[str],
    hs: dict[str, HiddenStems],
    branches: tuple[int, int, int],
) -> None:
    """蔵干セクション（日/月/年順、デバッグ数値付き）.

    branches: (day_branch, month_branch, year_branch) の enum 値タプル。
    """
    lines.append("【蔵干】")
    lines.append(f"{'':8s}{'日':10s}{'月':10s}{'年':10s}")
    day, month, year = hs["day"], hs["month"], hs["year"]
    day_b, month_b, year_b = branches
    lines.append(
        f"{'地支':8s}"
        f"{_branch_debug(day_b):10s}"
        f"{_branch_debug(month_b):10s}"
        f"{_branch_debug(year_b):10s}"
    )
    lines.append(
        f"{'初元':8s}"
        f"{_stem_debug(day.shogen.value if day.shogen is not None else None):10s}"
        f"{_stem_debug(month.shogen.value if month.shogen is not None else None):10s}"
        f"{_stem_debug(year.shogen.value if year.shogen is not None else None):10s}"
    )
    lines.append(
        f"{'中元':8s}"
        f"{_stem_debug(day.chuugen.value if day.chuugen is not None else None):10s}"
        f"{_stem_debug(month.chuugen.value if month.chuugen is not None else None):10s}"
        f"{_stem_debug(year.chuugen.value if year.chuugen is not None else None):10s}"
    )
    lines.append(
        f"{'本元':8s}"
        f"{_stem_debug(day.hongen.value):10s}"
        f"{_stem_debug(month.hongen.value):10s}"
        f"{_stem_debug(year.hongen.value):10s}"
    )


def _append_gogyo_balance(lines: list[str], gb: GoGyoBalance) -> None:
    tc = gb.total_count
    lines.append("【五行バランス】")
    lines.append(
        f"木: {tc.wood}  火: {tc.fire}  土: {tc.earth}  金: {tc.metal}  水: {tc.water}"
    )
    lacking_str = ", ".join(g.kanji for g in gb.lacking) if gb.lacking else "なし"
    lines.append(f"主: {gb.dominant.kanji}  欠: {lacking_str}")
    lines.append(f"日主五行: {gb.day_stem_gogyo.kanji}")
