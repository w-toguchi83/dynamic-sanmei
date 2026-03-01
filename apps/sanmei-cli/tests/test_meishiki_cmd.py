import json

from click.testing import CliRunner

from sanmei_cli.main import cli


class TestMeishikiCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_basic(self):
        result = self.runner.invoke(cli, ["meishiki", "2000-01-15"])
        assert result.exit_code == 0
        assert "=== 命式 ===" in result.output

    def test_with_time(self):
        result = self.runner.invoke(cli, ["meishiki", "2000-01-15", "--time", "14:30"])
        assert result.exit_code == 0
        assert "14:30" in result.output

    def test_json_output(self):
        result = self.runner.invoke(cli, ["--json", "meishiki", "2000-01-15"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "pillars" in data

    def test_invalid_date(self):
        result = self.runner.invoke(cli, ["meishiki", "not-a-date"])
        assert result.exit_code != 0

    def test_out_of_range_date(self):
        result = self.runner.invoke(cli, ["meishiki", "1800-01-01"])
        assert result.exit_code != 0
        assert "エラー" in result.output

    def test_help(self):
        result = self.runner.invoke(cli, ["meishiki", "--help"])
        assert result.exit_code == 0
        assert "%Y-%m-%d" in result.output
