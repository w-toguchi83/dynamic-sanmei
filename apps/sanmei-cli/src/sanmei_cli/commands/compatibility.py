"""compatibility サブコマンド."""

from __future__ import annotations

from datetime import datetime

import click
from sanmei_core import MeishikiCalculator, SanmeiError, analyze_compatibility

from sanmei_cli.formatters.json_fmt import to_json
from sanmei_cli.formatters.text import format_compatibility
from sanmei_cli.main import build_datetime, cli


@cli.command()
@click.argument("birthdate_a", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument("birthdate_b", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option(
    "--time-a", "birth_time_a", default="00:00", help="人物Aの出生時刻 (HH:MM)"
)
@click.option(
    "--time-b", "birth_time_b", default="00:00", help="人物Bの出生時刻 (HH:MM)"
)
@click.pass_context
def compatibility(
    ctx: click.Context,
    birthdate_a: datetime,
    birthdate_b: datetime,
    birth_time_a: str,
    birth_time_b: str,
) -> None:
    """二人の命式を比較して相性を鑑定する."""
    try:
        dt_a = build_datetime(birthdate_a, birth_time_a)
        dt_b = build_datetime(birthdate_b, birth_time_b)
        school = ctx.obj["school"]
        calc = MeishikiCalculator(school)
        meishiki_a = calc.calculate(dt_a)
        meishiki_b = calc.calculate(dt_b)
        result = analyze_compatibility(meishiki_a, meishiki_b)

        if ctx.obj["json"]:
            click.echo(to_json(result))
        else:
            click.echo(format_compatibility(result, dt_a, dt_b))
    except SanmeiError as e:
        click.echo(f"エラー: {e}", err=True)
        ctx.exit(1)
