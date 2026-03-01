import json

from click.testing import CliRunner

from sanmei_cli.main import cli


class TestIsouhouCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_basic(self):
        result = self.runner.invoke(cli, ["isouhou", "2000-01-15"])
        assert result.exit_code == 0
        assert "=== 位相法" in result.output

    def test_json_output(self):
        result = self.runner.invoke(cli, ["--json", "isouhou", "2000-01-15"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "stem_interactions" in data
        assert "branch_interactions" in data

    def test_help(self):
        result = self.runner.invoke(cli, ["isouhou", "--help"])
        assert result.exit_code == 0
