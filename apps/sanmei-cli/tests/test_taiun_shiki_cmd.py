"""taiun-shiki サブコマンドのテスト."""

import json

from click.testing import CliRunner

from sanmei_cli.main import cli


class TestTaiunShikiCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_basic(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15", "--gender", "m"])
        assert result.exit_code == 0
        assert "=== 大運四季表 ===" in result.output

    def test_contains_column_headers(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15", "--gender", "m"])
        assert "季節" in result.output
        assert "サイクル" in result.output

    def test_contains_month_kanshi(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15", "--gender", "m"])
        assert "月干支" in result.output

    def test_contains_period_labels(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15", "--gender", "m"])
        assert "第1句" in result.output

    def test_female(self):
        result = self.runner.invoke(
            cli, ["taiun-shiki", "2000-01-15", "--gender", "female"]
        )
        assert result.exit_code == 0

    def test_json_output(self):
        result = self.runner.invoke(
            cli, ["--json", "taiun-shiki", "2000-01-15", "--gender", "男"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "direction" in data
        assert "entries" in data

    def test_missing_gender(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15"])
        assert result.exit_code != 0

    def test_custom_periods(self):
        result = self.runner.invoke(
            cli, ["taiun-shiki", "2000-01-15", "--gender", "m", "--periods", "5"]
        )
        assert result.exit_code == 0

    def test_help(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "--help"])
        assert result.exit_code == 0
        assert "--gender" in result.output
