"""taiun-shiki サブコマンド."""

from __future__ import annotations

from datetime import datetime

import click
from sanmei_core import (
    Gender,
    MeishikiCalculator,
    SanmeiError,
    calculate_taiun,
    calculate_taiun_shiki,
)

from sanmei_cli.formatters.json_fmt import to_json
from sanmei_cli.formatters.text import format_taiun_shiki
from sanmei_cli.main import build_datetime, cli
from sanmei_cli.types import GenderType


@cli.command("taiun-shiki")
@click.argument("birthdate", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--time", "birth_time", default="00:00", help="出生時刻 (HH:MM)")
@click.option(
    "--gender", required=True, type=GenderType(), help="性別 (男/male/m, 女/female/f)"
)
@click.option("--periods", default=10, type=int, help="大運の期間数 (デフォルト: 10)")
@click.pass_context
def taiun_shiki(
    ctx: click.Context,
    birthdate: datetime,
    birth_time: str,
    gender: Gender,
    periods: int,
) -> None:
    """大運四季表を算出して表示する."""
    try:
        dt = build_datetime(birthdate, birth_time)
        school = ctx.obj["school"]
        calc = MeishikiCalculator(school)
        meishiki = calc.calculate(dt)
        taiun_chart = calculate_taiun(
            meishiki,
            dt,
            gender,
            school.get_setsuiri_provider(),
            rounding=school.get_taiun_start_age_rounding(),
            num_periods=periods,
        )
        shiki_chart = calculate_taiun_shiki(meishiki, taiun_chart, school)

        if ctx.obj["json"]:
            click.echo(to_json(shiki_chart))
        else:
            click.echo(format_taiun_shiki(shiki_chart))
    except SanmeiError as e:
        click.echo(f"エラー: {e}", err=True)
        ctx.exit(1)
