"""算命学CLI エントリポイント."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import click
from sanmei_core import SanmeiError, SchoolRegistry

JST = timezone(timedelta(hours=9))


def build_datetime(birthdate: datetime, birth_time: str) -> datetime:
    """日付と時刻文字列を結合してJST datetimeを生成."""
    t = datetime.strptime(birth_time, "%H:%M").time()
    return datetime.combine(birthdate.date(), t, tzinfo=JST)


@click.group(invoke_without_command=True)
@click.option(
    "--json", "output_json", is_flag=True, default=False, help="JSON形式で出力"
)
@click.option(
    "--school", "school_name", default="standard", help="流派名 (デフォルト: standard)"
)
@click.pass_context
def cli(ctx: click.Context, output_json: bool, school_name: str) -> None:
    """算命学CLI - 開発者向け動作確認ツール."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = output_json
    ctx.obj["school_name"] = school_name

    try:
        registry = SchoolRegistry.create_default()
        ctx.obj["school"] = registry.get(school_name)
    except SanmeiError as e:
        click.echo(f"エラー: {e}", err=True)
        ctx.exit(1)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
