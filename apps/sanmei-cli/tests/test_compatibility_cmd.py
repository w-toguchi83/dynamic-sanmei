"""compatibility サブコマンドのテスト."""

import json

from click.testing import CliRunner

from sanmei_cli.main import cli


class TestCompatibilityCommand:
    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_basic(self) -> None:
        result = self.runner.invoke(cli, ["compatibility", "2000-01-15", "1990-05-20"])
        assert result.exit_code == 0
        assert "=== 相性鑑定 ===" in result.output

    def test_with_times(self) -> None:
        result = self.runner.invoke(
            cli,
            [
                "compatibility",
                "2000-01-15",
                "1990-05-20",
                "--time-a",
                "14:30",
                "--time-b",
                "10:00",
            ],
        )
        assert result.exit_code == 0
        assert "=== 相性鑑定 ===" in result.output

    def test_json_output(self) -> None:
        result = self.runner.invoke(
            cli, ["--json", "compatibility", "2000-01-15", "1990-05-20"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "nikkan_relation" in data
        assert "day_pillar_relation" in data
        assert "gogyo_complement" in data
        assert "tenchuusatsu_compatibility" in data
        assert "cross_isouhou" in data

    def test_help(self) -> None:
        result = self.runner.invoke(cli, ["compatibility", "--help"])
        assert result.exit_code == 0

    def test_output_contains_nikkan(self) -> None:
        result = self.runner.invoke(cli, ["compatibility", "2000-01-15", "1990-05-20"])
        assert "【日干の関係】" in result.output

    def test_output_contains_gogyo(self) -> None:
        result = self.runner.invoke(cli, ["compatibility", "2000-01-15", "1990-05-20"])
        assert "【五行の補完】" in result.output

    def test_output_contains_tenchuusatsu(self) -> None:
        result = self.runner.invoke(cli, ["compatibility", "2000-01-15", "1990-05-20"])
        assert "【天中殺の相性】" in result.output

    def test_output_contains_day_pillar(self) -> None:
        result = self.runner.invoke(cli, ["compatibility", "2000-01-15", "1990-05-20"])
        assert "【日柱の関係】" in result.output

    def test_output_contains_cross_isouhou(self) -> None:
        result = self.runner.invoke(cli, ["compatibility", "2000-01-15", "1990-05-20"])
        assert "【クロスチャート位相法】" in result.output
