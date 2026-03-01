import json

from click.testing import CliRunner

from sanmei_cli.main import cli


class TestTaiunCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_basic(self):
        result = self.runner.invoke(cli, ["taiun", "2000-01-15", "--gender", "m"])
        assert result.exit_code == 0
        assert "=== 大運 ===" in result.output

    def test_female(self):
        result = self.runner.invoke(cli, ["taiun", "2000-01-15", "--gender", "female"])
        assert result.exit_code == 0

    def test_json_output(self):
        result = self.runner.invoke(
            cli, ["--json", "taiun", "2000-01-15", "--gender", "男"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "direction" in data
        assert "periods" in data

    def test_missing_gender(self):
        result = self.runner.invoke(cli, ["taiun", "2000-01-15"])
        assert result.exit_code != 0

    def test_custom_periods(self):
        result = self.runner.invoke(
            cli, ["taiun", "2000-01-15", "--gender", "m", "--periods", "5"]
        )
        assert result.exit_code == 0

    def test_help(self):
        result = self.runner.invoke(cli, ["taiun", "--help"])
        assert result.exit_code == 0
        assert "--gender" in result.output
