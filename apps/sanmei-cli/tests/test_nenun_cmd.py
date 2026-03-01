import json

from click.testing import CliRunner

from sanmei_cli.main import cli


class TestNenunCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_basic(self):
        result = self.runner.invoke(
            cli, ["nenun", "2000-01-15", "--from", "2020", "--to", "2025"]
        )
        assert result.exit_code == 0
        assert "=== 年運 ===" in result.output
        assert "2020" in result.output
        assert "2025" in result.output

    def test_json_output(self):
        result = self.runner.invoke(
            cli, ["--json", "nenun", "2000-01-15", "--from", "2020", "--to", "2022"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 3

    def test_missing_from(self):
        result = self.runner.invoke(cli, ["nenun", "2000-01-15", "--to", "2025"])
        assert result.exit_code != 0

    def test_missing_to(self):
        result = self.runner.invoke(cli, ["nenun", "2000-01-15", "--from", "2020"])
        assert result.exit_code != 0

    def test_help(self):
        result = self.runner.invoke(cli, ["nenun", "--help"])
        assert result.exit_code == 0
        assert "--from" in result.output
        assert "--to" in result.output
