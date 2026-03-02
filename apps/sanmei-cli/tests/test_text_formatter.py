from datetime import datetime, timedelta, timezone

from sanmei_core import IsouhouResult

from sanmei_cli.formatters.text import (
    format_isouhou,
    format_meishiki,
    format_nenun,
    format_taiun,
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

    def test_hidden_stems_shows_branch_debug(self, meishiki):
        """蔵干セクションに地支のデバッグ情報（漢字+enum値）がある."""
        result = format_meishiki(meishiki, BIRTH_DT)
        section = result[result.index("【蔵干】") :]
        assert "地支" in section
        # enum値が括弧付きで表示される
        for key in ("day", "month", "year"):
            branch_val = getattr(meishiki.pillars, key).branch.value
            assert f"({branch_val})" in section

    def test_hidden_stems_hongen_always_present(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        # 本元は全柱に必ず存在し、漢字(enum値)の形式で表示される
        for key in ("year", "month", "day"):
            hs = meishiki.hidden_stems[key]
            stem_kanji = "甲乙丙丁戊己庚辛壬癸"[hs.hongen.value]
            assert f"{stem_kanji}({hs.hongen.value})" in result

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
    def test_contains_header(self, taiun_chart):
        result = format_taiun(taiun_chart)
        assert "=== 大運 ===" in result

    def test_contains_direction(self, taiun_chart):
        result = format_taiun(taiun_chart)
        assert taiun_chart.direction in result

    def test_contains_start_age(self, taiun_chart):
        result = format_taiun(taiun_chart)
        assert f"{taiun_chart.start_age}歳" in result

    def test_contains_period_kanshi(self, taiun_chart):
        result = format_taiun(taiun_chart)
        for period in taiun_chart.periods:
            assert period.kanshi.kanji in result

    def test_contains_age_range(self, taiun_chart):
        result = format_taiun(taiun_chart)
        first = taiun_chart.periods[0]
        assert f"{first.start_age}-{first.end_age}歳" in result


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
