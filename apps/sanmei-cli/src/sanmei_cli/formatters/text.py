"""テキスト形式フォーマッター."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanmei_core import (
        CompatibilityResult,
        GoGyoBalance,
        IsouhouResult,
        Meishiki,
        TaiunChart,
    )
    from sanmei_core.domain.fortune import Nenun
    from sanmei_core.domain.hidden_stems import HiddenStems
    from sanmei_core.domain.kanshi import TenStem
    from sanmei_core.domain.taiun_shiki import TaiunShikiChart
    from sanmei_core.domain.zoukan_tokutei import ZoukanTokutei

_STEM_KANJI = "甲乙丙丁戊己庚辛壬癸"
_BRANCH_KANJI = "子丑寅卯辰巳午未申酉戌亥"


def _cjk_ljust(text: str, width: int) -> str:
    """全角文字の表示幅を考慮した左寄せパディング."""
    display_width = sum(2 if ord(c) > 0x7F else 1 for c in text)
    return text + " " * max(0, width - display_width)


def _stem(stem_val: int) -> str:
    return _STEM_KANJI[stem_val]


def _branch(branch_val: int) -> str:
    return _BRANCH_KANJI[branch_val]


def _stem_or_dash(stem: TenStem | None) -> str:
    """蔵干の表示（漢字のみ、Noneはダッシュ）."""
    if stem is None:
        return "-"
    return _STEM_KANJI[stem.value]


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
    lines.append(
        f"{_cjk_ljust('', 8)}{_cjk_ljust('日', 10)}"
        f"{_cjk_ljust('月', 10)}{_cjk_ljust('年', 10)}"
    )
    lines.append(
        f"{_cjk_ljust('天干', 8)}{_cjk_ljust(_stem(p.day.stem.value), 10)}"
        f"{_cjk_ljust(_stem(p.month.stem.value), 10)}"
        f"{_cjk_ljust(_stem(p.year.stem.value), 10)}"
    )
    lines.append(
        f"{_cjk_ljust('地支', 8)}"
        f"{_cjk_ljust(_branch(p.day.branch.value), 10)}"
        f"{_cjk_ljust(_branch(p.month.branch.value), 10)}"
        f"{_cjk_ljust(_branch(p.year.branch.value), 10)}"
    )
    lines.append("")

    # 蔵干
    _append_hidden_stems(lines, meishiki.hidden_stems, meishiki.zoukan_tokutei)
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


def format_taiun(chart: TaiunChart, month_kanshi_kanji: str) -> str:
    """大運をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 大運 ===")
    lines.append(f"方向: {chart.direction}  立運: {chart.start_age}歳")
    lines.append("")
    lines.append(f" {_cjk_ljust('', 10)}{'干支':<8s}{'年齢'}")

    # 月干支行（大運前の期間）
    if chart.start_age >= 2:
        age_str = f"0-{chart.start_age - 1}歳"
    else:
        age_str = "0歳"
    lines.append(f" {_cjk_ljust('月干支', 10)}{month_kanshi_kanji:<8s}{age_str}")

    for i, period in enumerate(chart.periods, 1):
        label = f"第{i}句"
        lines.append(
            f" {_cjk_ljust(label, 10)}{period.kanshi.kanji:<8s}"
            f"{period.start_age}-{period.end_age}歳"
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


def _append_hidden_stems(
    lines: list[str],
    hs: dict[str, HiddenStems],
    zoukan_tokutei: ZoukanTokutei,
) -> None:
    """蔵干セクション（日/月/年順）+ 蔵干特定値."""
    label_w = 10
    col_w = 10
    lines.append(f"【蔵干】(節入り日から{zoukan_tokutei.days_from_setsuiri}日目)")
    lines.append(
        f"{_cjk_ljust('', label_w)}{_cjk_ljust('日', col_w)}"
        f"{_cjk_ljust('月', col_w)}{_cjk_ljust('年', col_w)}"
    )
    day, month, year = hs["day"], hs["month"], hs["year"]
    lines.append(
        f"{_cjk_ljust('初元', label_w)}"
        f"{_cjk_ljust(_stem_or_dash(day.shogen), col_w)}"
        f"{_cjk_ljust(_stem_or_dash(month.shogen), col_w)}"
        f"{_cjk_ljust(_stem_or_dash(year.shogen), col_w)}"
    )
    lines.append(
        f"{_cjk_ljust('中元', label_w)}"
        f"{_cjk_ljust(_stem_or_dash(day.chuugen), col_w)}"
        f"{_cjk_ljust(_stem_or_dash(month.chuugen), col_w)}"
        f"{_cjk_ljust(_stem_or_dash(year.chuugen), col_w)}"
    )
    lines.append(
        f"{_cjk_ljust('本元', label_w)}"
        f"{_cjk_ljust(_stem(day.hongen.value), col_w)}"
        f"{_cjk_ljust(_stem(month.hongen.value), col_w)}"
        f"{_cjk_ljust(_stem(year.hongen.value), col_w)}"
    )
    # 蔵干特定: 選択された蔵干を表示
    zt = zoukan_tokutei
    lines.append(
        f"{_cjk_ljust('蔵干特定', label_w)}"
        f"{_cjk_ljust(f'{_STEM_KANJI[zt.day.stem.value]}({zt.day.element.value})', col_w)}"
        f"{_cjk_ljust(f'{_STEM_KANJI[zt.month.stem.value]}({zt.month.element.value})', col_w)}"
        f"{_cjk_ljust(f'{_STEM_KANJI[zt.year.stem.value]}({zt.year.element.value})', col_w)}"
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


def format_taiun_shiki(chart: TaiunShikiChart) -> str:
    """大運四季表をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 大運四季表 ===")
    lines.append(f"方向: {chart.direction}  立運: {chart.start_age}歳")
    lines.append("")

    # 列幅定義
    w_season = 6  # 季節
    w_age = 12  # 年齢
    w_label = 10  # 大運
    w_kanshi = 6  # 干支
    w_zoukan = 12  # 蔵干
    w_major = 10  # 十大主星
    w_sub = 10  # 十二大従星

    # ヘッダー
    lines.append(
        f"{_cjk_ljust('季節', w_season)}"
        f"{_cjk_ljust('年齢', w_age)}"
        f"{_cjk_ljust('大運', w_label)}"
        f"{_cjk_ljust('干支', w_kanshi)}"
        f"{_cjk_ljust('蔵干', w_zoukan)}"
        f"{_cjk_ljust('十大主星', w_major)}"
        f"{_cjk_ljust('十二大従星', w_sub)}"
        f"サイクル"
    )

    for entry in chart.entries:
        # 蔵干を「・」区切りで列挙（hongen, chuugen, shogenの順、Noneは省略）
        stems = [_STEM_KANJI[entry.hidden_stems.hongen.value]]
        if entry.hidden_stems.chuugen is not None:
            stems.append(_STEM_KANJI[entry.hidden_stems.chuugen.value])
        if entry.hidden_stems.shogen is not None:
            stems.append(_STEM_KANJI[entry.hidden_stems.shogen.value])
        zoukan_str = "・".join(stems)

        # 年齢
        age_str = f"{entry.start_age}-{entry.end_age}歳"

        lines.append(
            f"{_cjk_ljust(entry.season.value, w_season)}"
            f"{_cjk_ljust(age_str, w_age)}"
            f"{_cjk_ljust(entry.label, w_label)}"
            f"{_cjk_ljust(entry.kanshi.kanji, w_kanshi)}"
            f"{_cjk_ljust(zoukan_str, w_zoukan)}"
            f"{_cjk_ljust(entry.major_star.value, w_major)}"
            f"{_cjk_ljust(entry.subsidiary_star.value, w_sub)}"
            f"{entry.life_cycle.value}"
        )

    return "\n".join(lines)


def format_compatibility(
    result: CompatibilityResult,
    dt_a: datetime,
    dt_b: datetime,
) -> str:
    """相性鑑定結果をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 相性鑑定 ===")
    lines.append(
        f"人物A: {dt_a.year}年{dt_a.month}月{dt_a.day}日  "
        f"人物B: {dt_b.year}年{dt_b.month}月{dt_b.day}日"
    )
    lines.append("")

    # 日干関係
    nr = result.nikkan_relation
    s_a = _STEM_KANJI[nr.stem_a.value]
    s_b = _STEM_KANJI[nr.stem_b.value]
    lines.append("【日干の関係】")
    lines.append(f"A: {s_a}({nr.gogyo_a.kanji})  B: {s_b}({nr.gogyo_b.kanji})")
    if nr.kangou_gogyo is not None:
        lines.append(f"関係: {nr.relation_type.value} → {nr.kangou_gogyo.kanji}")
    else:
        lines.append(f"関係: {nr.relation_type.value}")
    lines.append("")

    # 五行補完
    gc = result.gogyo_complement
    lines.append("【五行の補完】")
    lack_a = ", ".join(g.kanji for g in gc.lacking_a) if gc.lacking_a else "なし"
    lack_b = ", ".join(g.kanji for g in gc.lacking_b) if gc.lacking_b else "なし"
    lines.append(f"Aの欠: {lack_a}")
    lines.append(f"Bの欠: {lack_b}")
    comp_b = (
        ", ".join(g.kanji for g in gc.complemented_by_b)
        if gc.complemented_by_b
        else "なし"
    )
    comp_a = (
        ", ".join(g.kanji for g in gc.complemented_by_a)
        if gc.complemented_by_a
        else "なし"
    )
    lines.append(f"BがAを補う: {comp_b}")
    lines.append(f"AがBを補う: {comp_a}")
    lines.append("")

    # 天中殺の相性
    tc = result.tenchuusatsu_compatibility
    lines.append("【天中殺の相性】")
    lines.append(f"A: {tc.type_a.value}  B: {tc.type_b.value}")
    if tc.a_branches_in_b:
        br_str = ", ".join(_BRANCH_KANJI[b.value] for b in tc.a_branches_in_b)
        lines.append(f"Aの天中殺支がBに: {br_str}")
    if tc.b_branches_in_a:
        br_str = ", ".join(_BRANCH_KANJI[b.value] for b in tc.b_branches_in_a)
        lines.append(f"Bの天中殺支がAに: {br_str}")
    if not tc.a_branches_in_b and not tc.b_branches_in_a:
        lines.append("相互の天中殺支の影響なし")
    lines.append("")

    # クロスチャート位相法
    ci = result.cross_isouhou
    lines.append("【クロスチャート位相法】")
    if not ci.stem_interactions and not ci.branch_interactions:
        lines.append("相互作用なし")
    else:
        if ci.stem_interactions:
            lines.append("")
            lines.append("天干の合:")
            for si in ci.stem_interactions:
                sa = _STEM_KANJI[si.stems[0].value]
                sb = _STEM_KANJI[si.stems[1].value]
                lines.append(f"  {sa}-{sb} {si.type.value} → {si.result_gogyo.kanji}")

        if ci.branch_interactions:
            lines.append("")
            lines.append("地支の関係:")
            for bi in ci.branch_interactions:
                branches_str = "-".join(_BRANCH_KANJI[b.value] for b in bi.branches)
                if bi.result_gogyo is not None:
                    lines.append(
                        f"  {branches_str} {bi.type.value} → {bi.result_gogyo.kanji}"
                    )
                else:
                    lines.append(f"  {branches_str} {bi.type.value}")

    return "\n".join(lines)
