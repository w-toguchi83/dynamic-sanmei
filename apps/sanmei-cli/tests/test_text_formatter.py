from datetime import datetime, timedelta, timezone

from sanmei_core import IsouhouResult

from sanmei_cli.formatters.text import (
    format_isouhou,
    format_meishiki,
    format_nenun,
    format_taiun,
    format_taiun_shiki,
)

JST = timezone(timedelta(hours=9))
BIRTH_DT = datetime(2000, 1, 15, 14, 30, tzinfo=JST)


class TestFormatMeishiki:
    def test_contains_header(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "=== 命式 ===" in result

    def test_contains_birthdate(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "2000年1月15日 14:30" in result

    def test_contains_kanshi_section(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【干支】" in result
        assert "天干" in result
        assert "地支" in result

    def test_kanshi_day_month_year_order(self, meishiki):
        """干支セクションの列順が日→月→年であること."""
        result = format_meishiki(meishiki, BIRTH_DT)
        # ヘッダー行で日が月より左にある
        kanshi_section = result[result.index("【干支】") :]
        header_line = kanshi_section.split("\n")[1]
        assert (
            header_line.index("日") < header_line.index("月") < header_line.index("年")
        )

    def test_contains_major_stars(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【十大主星】" in result
        assert "北:" in result
        assert "中:" in result

    def test_contains_subsidiary_stars(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【十二大従星】" in result
        assert "日:" in result
        assert "月:" in result
        assert "年:" in result

    def test_subsidiary_stars_day_month_year_order(self, meishiki):
        """十二大従星の表示順が日→月→年であること."""
        result = format_meishiki(meishiki, BIRTH_DT)
        section = result[result.index("【十二大従星】") :]
        stars_line = section.split("\n")[1]
        assert (
            stars_line.index("日:") < stars_line.index("月:") < stars_line.index("年:")
        )

    def test_contains_tenchuusatsu(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【天中殺】" in result
        assert "天中殺" in result

    def test_contains_hidden_stems_section(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【蔵干】" in result
        assert "本元" in result

    def test_hidden_stems_shows_day_month_year_header(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        section = result[result.index("【蔵干】") :]
        header_line = section.split("\n")[1]
        assert (
            header_line.index("日") < header_line.index("月") < header_line.index("年")
        )

    def test_hidden_stems_no_branch_row(self, meishiki):
        """蔵干セクションに地支行がないこと."""
        result = format_meishiki(meishiki, BIRTH_DT)
        section = result[result.index("【蔵干】") :]
        # 蔵干セクション内で次のセクションまでを切り出す
        next_section = section.index("【使命星】")
        zoukan_section = section[:next_section]
        # 地支行がないことを確認
        for line in zoukan_section.split("\n"):
            assert not line.startswith("地支")

    def test_hidden_stems_no_debug_numbers(self, meishiki):
        """蔵干セクションにデバッグ数字(N)が表示されないこと."""
        result = format_meishiki(meishiki, BIRTH_DT)
        section = result[result.index("【蔵干】") :]
        next_section = section.index("【使命星】")
        zoukan_section = section[:next_section]
        # 括弧付き数字がないことを確認
        import re

        assert not re.search(r"\(\d+\)", zoukan_section)

    def test_hidden_stems_hongen_always_present(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        # 本元は全柱に必ず存在し、漢字のみで表示される
        for key in ("year", "month", "day"):
            hs = meishiki.hidden_stems[key]
            stem_kanji = "甲乙丙丁戊己庚辛壬癸"[hs.hongen.value]
            assert stem_kanji in result

    def test_hidden_stems_none_shown_as_dash(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        # chuugen/shogen が None の柱があればダッシュ表示
        has_none = any(
            meishiki.hidden_stems[k].chuugen is None
            or meishiki.hidden_stems[k].shogen is None
            for k in ("year", "month", "day")
        )
        if has_none:
            assert "-" in result

    def test_zoukan_tokutei_days_shown(self, meishiki):
        """蔵干セクションヘッダーに節入り日からの日数が表示される."""
        result = format_meishiki(meishiki, BIRTH_DT)
        days = meishiki.zoukan_tokutei.days_from_setsuiri
        assert f"節入り日から{days}日目" in result

    def test_zoukan_tokutei_row_shown(self, meishiki):
        """蔵干特定行が表示される."""
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "蔵干特定" in result
        zt = meishiki.zoukan_tokutei
        # 各柱の選択された蔵干と区分が表示される
        assert zt.day.element.value in result
        assert zt.month.element.value in result
        assert zt.year.element.value in result

    def test_contains_shimeisei(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【使命星】" in result
        assert meishiki.shimeisei.value in result

    def test_shimeisei_after_hidden_stems(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        hidden_pos = result.index("【蔵干】")
        shimeisei_pos = result.index("【使命星】")
        major_pos = result.index("【十大主星】")
        assert hidden_pos < shimeisei_pos < major_pos

    def test_contains_gogyo_balance(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【五行バランス】" in result
        assert "木:" in result
        assert "火:" in result
        assert "土:" in result
        assert "金:" in result
        assert "水:" in result
        assert "日主五行:" in result


class TestFormatTaiun:
    def test_contains_header(self, taiun_chart, month_kanshi_kanji):
        result = format_taiun(taiun_chart, month_kanshi_kanji)
        assert "=== 大運 ===" in result

    def test_contains_direction(self, taiun_chart, month_kanshi_kanji):
        result = format_taiun(taiun_chart, month_kanshi_kanji)
        assert taiun_chart.direction in result

    def test_contains_start_age(self, taiun_chart, month_kanshi_kanji):
        result = format_taiun(taiun_chart, month_kanshi_kanji)
        assert f"立運: {taiun_chart.start_age}歳" in result

    def test_contains_period_kanshi(self, taiun_chart, month_kanshi_kanji):
        result = format_taiun(taiun_chart, month_kanshi_kanji)
        for period in taiun_chart.periods:
            assert period.kanshi.kanji in result

    def test_contains_age_range(self, taiun_chart, month_kanshi_kanji):
        result = format_taiun(taiun_chart, month_kanshi_kanji)
        first = taiun_chart.periods[0]
        assert f"{first.start_age}-{first.end_age}歳" in result

    def test_period_label_format(self, taiun_chart, month_kanshi_kanji):
        result = format_taiun(taiun_chart, month_kanshi_kanji)
        assert "第1句" in result
        assert "第2句" in result

    def test_month_kanshi_row(self, taiun_chart, month_kanshi_kanji):
        result = format_taiun(taiun_chart, month_kanshi_kanji)
        assert "月干支" in result
        assert month_kanshi_kanji in result

    def test_month_kanshi_age_range(self, taiun_chart, month_kanshi_kanji):
        result = format_taiun(taiun_chart, month_kanshi_kanji)
        if taiun_chart.start_age >= 2:
            assert f"0-{taiun_chart.start_age - 1}歳" in result
        else:
            assert "0歳" in result


class TestFormatNenun:
    def test_contains_header(self, nenun_list):
        result = format_nenun(nenun_list)
        assert "=== 年運 ===" in result

    def test_contains_years(self, nenun_list):
        result = format_nenun(nenun_list)
        for nenun in nenun_list:
            assert str(nenun.year) in result

    def test_contains_kanshi(self, nenun_list):
        result = format_nenun(nenun_list)
        for nenun in nenun_list:
            assert nenun.kanshi.kanji in result

    def test_contains_age(self, nenun_list):
        result = format_nenun(nenun_list)
        for nenun in nenun_list:
            assert f"{nenun.age}歳" in result


class TestFormatIsouhou:
    def test_contains_header(self, isouhou_result):
        result = format_isouhou(isouhou_result)
        assert "=== 位相法" in result

    def test_stem_interactions_shown(self, isouhou_result):
        result = format_isouhou(isouhou_result)
        if isouhou_result.stem_interactions:
            assert "【天干の合】" in result
            for si in isouhou_result.stem_interactions:
                assert si.type.value in result

    def test_branch_interactions_shown(self, isouhou_result):
        result = format_isouhou(isouhou_result)
        if isouhou_result.branch_interactions:
            assert "【地支の関係】" in result
            for bi in isouhou_result.branch_interactions:
                assert bi.type.value in result

    def test_no_interactions(self):
        empty = IsouhouResult(stem_interactions=(), branch_interactions=())
        result = format_isouhou(empty)
        assert "相互作用なし" in result


class TestFormatTaiunShiki:
    def test_contains_header(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert "=== 大運四季表 ===" in result

    def test_contains_direction(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert shiki_chart.direction in result

    def test_contains_start_age(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert f"立運: {shiki_chart.start_age}歳" in result

    def test_column_headers(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert "季節" in result
        assert "年齢" in result
        assert "大運" in result
        assert "干支" in result
        assert "蔵干" in result
        assert "十大主星" in result
        assert "十二大従星" in result
        assert "サイクル" in result

    def test_column_order(self, shiki_chart):
        """列順: 季節→年齢→大運→干支→蔵干→十大主星→十二大従星→サイクル."""
        result = format_taiun_shiki(shiki_chart)
        header_line = [
            line for line in result.split("\n") if "季節" in line and "サイクル" in line
        ][0]
        assert header_line.index("季節") < header_line.index("年齢")
        assert header_line.index("年齢") < header_line.index("大運")
        assert header_line.index("大運") < header_line.index("干支")
        assert header_line.index("干支") < header_line.index("蔵干")
        assert header_line.index("蔵干") < header_line.index("十大主星")
        assert header_line.index("十大主星") < header_line.index("十二大従星")
        assert header_line.index("十二大従星") < header_line.index("サイクル")

    def test_contains_month_kanshi_label(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert "月干支" in result

    def test_contains_period_labels(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert "第1句" in result

    def test_contains_season_values(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.season.value in result

    def test_contains_kanshi_kanji(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.kanshi.kanji in result

    def test_contains_major_star(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.major_star.value in result

    def test_contains_subsidiary_star(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.subsidiary_star.value in result

    def test_contains_life_cycle(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.life_cycle.value in result

    def test_hidden_stems_dot_separated(self, shiki_chart):
        """蔵干が「・」区切りで表示される."""
        result = format_taiun_shiki(shiki_chart)
        has_multi = any(
            e.hidden_stems.chuugen is not None or e.hidden_stems.shogen is not None
            for e in shiki_chart.entries
        )
        if has_multi:
            assert "・" in result
