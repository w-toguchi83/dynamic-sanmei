from click.testing import CliRunner
from sanmei_cli.main import cli


class TestCLIGroup:
    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_help(self) -> None:
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "算命学CLI" in result.output

    def test_no_args_shows_help(self) -> None:
        result = self.runner.invoke(cli, [])
        assert result.exit_code == 0
