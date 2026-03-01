import json

from sanmei_cli.formatters.json_fmt import to_json


class TestToJson:
    def test_meishiki_json(self, meishiki):
        result = to_json(meishiki)
        data = json.loads(result)
        assert "pillars" in data
        assert "major_stars" in data
        assert "tenchuusatsu" in data
        assert "gogyo_balance" in data

    def test_taiun_json(self, taiun_chart):
        result = to_json(taiun_chart)
        data = json.loads(result)
        assert "direction" in data
        assert "periods" in data

    def test_nenun_list_json(self, nenun_list):
        result = to_json(nenun_list)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "year" in data[0]
        assert "kanshi" in data[0]

    def test_isouhou_json(self, isouhou_result):
        result = to_json(isouhou_result)
        data = json.loads(result)
        assert "stem_interactions" in data
        assert "branch_interactions" in data

    def test_japanese_preserved(self, meishiki):
        result = to_json(meishiki)
        # ensure_ascii=False なので日本語がそのまま
        assert "天中殺" in result or "tenchuusatsu" in result
