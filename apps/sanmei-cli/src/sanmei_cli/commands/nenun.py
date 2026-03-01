"""nenun サブコマンド."""

from __future__ import annotations

from datetime import datetime

import click
from sanmei_core import SanmeiError, calculate_nenun

from sanmei_cli.formatters.json_fmt import to_json
from sanmei_cli.formatters.text import format_nenun
from sanmei_cli.main import build_datetime, cli


@cli.command()
@click.argument("birthdate", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--time", "birth_time", default="00:00", help="出生時刻 (HH:MM)")
@click.option("--from", "from_year", required=True, type=int, help="開始年 (西暦)")
@click.option("--to", "to_year", required=True, type=int, help="終了年 (西暦)")
@click.pass_context
def nenun(
    ctx: click.Context,
    birthdate: datetime,
    birth_time: str,
    from_year: int,
    to_year: int,
) -> None:
    """年運を算出して表示する."""
    try:
        dt = build_datetime(birthdate, birth_time)
        school = ctx.obj["school"]
        result = calculate_nenun(
            dt,
            school.get_setsuiri_provider(),
            year_range=(from_year, to_year),
        )

        if ctx.obj["json"]:
            click.echo(to_json(result))
        else:
            click.echo(format_nenun(result))
    except SanmeiError as e:
        click.echo(f"エラー: {e}", err=True)
        ctx.exit(1)
