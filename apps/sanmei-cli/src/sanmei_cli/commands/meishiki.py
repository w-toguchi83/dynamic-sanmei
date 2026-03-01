"""meishiki サブコマンド."""

from __future__ import annotations

from datetime import datetime

import click
from sanmei_core import MeishikiCalculator, SanmeiError

from sanmei_cli.formatters.json_fmt import to_json
from sanmei_cli.formatters.text import format_meishiki
from sanmei_cli.main import build_datetime, cli


@cli.command()
@click.argument("birthdate", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--time", "birth_time", default="00:00", help="出生時刻 (HH:MM)")
@click.pass_context
def meishiki(ctx: click.Context, birthdate: datetime, birth_time: str) -> None:
    """命式を算出して表示する."""
    try:
        dt = build_datetime(birthdate, birth_time)
        school = ctx.obj["school"]
        calc = MeishikiCalculator(school)
        result = calc.calculate(dt)

        if ctx.obj["json"]:
            click.echo(to_json(result))
        else:
            click.echo(format_meishiki(result, dt))
    except SanmeiError as e:
        click.echo(f"エラー: {e}", err=True)
        ctx.exit(1)
