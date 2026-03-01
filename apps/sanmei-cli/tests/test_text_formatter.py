from datetime import datetime, timedelta, timezone

from sanmei_cli.formatters.text import format_meishiki, format_nenun, format_taiun

JST = timezone(timedelta(hours=9))
BIRTH_DT = datetime(2000, 1, 15, 14, 30, tzinfo=JST)


class TestFormatMeishiki:
    def test_contains_header(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "=== 命式 ===" in result

    def test_contains_birthdate(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "2000年1月15日 14:30" in result

    def test_contains_pillars_section(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【三柱】" in result
        assert "天干" in result
        assert "地支" in result
        assert "年柱" in result
        assert "月柱" in result
        assert "日柱" in result

    def test_contains_major_stars(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【十大主星】" in result
        assert "北:" in result
        assert "中:" in result

    def test_contains_subsidiary_stars(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【十二大従星】" in result
        assert "年:" in result
        assert "月:" in result
        assert "日:" in result

    def test_contains_tenchuusatsu(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【天中殺】" in result
        assert "天中殺" in result

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
