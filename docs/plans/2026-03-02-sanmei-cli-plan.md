# Sanmei CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a click-based CLI (`sanmei`) that exposes sanmei-core's full functionality for developer verification.

**Architecture:** Click group with 4 subcommands (meishiki, taiun, nenun, isouhou). Formatters (text/json) are separated from commands. Common options (--json, --school) on the group level.

**Tech Stack:** Python 3.14+, click, sanmei-core (workspace dep), pytest, ruff, mypy

---

### Task 1: Package Scaffold & Workspace Setup

**Files:**
- Create: `apps/sanmei-cli/pyproject.toml`
- Create: `apps/sanmei-cli/src/sanmei_cli/__init__.py`
- Create: `apps/sanmei-cli/src/sanmei_cli/main.py` (placeholder)
- Create: `apps/sanmei-cli/src/sanmei_cli/commands/__init__.py`
- Create: `apps/sanmei-cli/src/sanmei_cli/formatters/__init__.py`
- Modify: `pyproject.toml` (root workspace)
- Modify: `Justfile`

**Step 1: Create pyproject.toml**

```toml
# apps/sanmei-cli/pyproject.toml
[project]
name = "sanmei-cli"
version = "0.1.0"
description = "算命学CLI - 開発者向け動作確認ツール"
requires-python = ">=3.14"
dependencies = [
    "click>=8.1.0",
    "sanmei-core",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-cov>=6.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/sanmei_cli"]

[project.scripts]
sanmei = "sanmei_cli.main:cli"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 2: Create empty source files**

```python
# apps/sanmei-cli/src/sanmei_cli/__init__.py
"""算命学CLI - 開発者向け動作確認ツール."""
```

```python
# apps/sanmei-cli/src/sanmei_cli/main.py
"""CLI entry point (placeholder)."""
```

```python
# apps/sanmei-cli/src/sanmei_cli/commands/__init__.py
"""CLI subcommands."""
```

```python
# apps/sanmei-cli/src/sanmei_cli/formatters/__init__.py
"""Output formatters."""
```

**Step 3: Update root workspace**

In `pyproject.toml` (root), add `"apps/*"` to workspace members:

```toml
[tool.uv.workspace]
members = [
    "packages/*",
    "services/*",
    "apps/*",
]
```

**Step 4: Update Justfile**

Add sanmei-cli to test, lint, and typecheck targets:

```just
# 全パッケージのテスト実行
test:
    uv run --project packages/dynamic-ontology pytest packages/dynamic-ontology/tests -v
    uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v
    uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests -v

# NOTE: services/ を追加する場合はパスに追記すること
# 全パッケージのリント
lint:
    uv run ruff check packages/ apps/
    uv run ruff format --check packages/ apps/

# リントの自動修正
lint-fix:
    uv run ruff check --fix packages/ apps/
    uv run ruff format packages/ apps/

# 全パッケージの型チェック
typecheck:
    uv run mypy packages/dynamic-ontology/src
    uv run mypy packages/sanmei-core/src
    uv run mypy apps/sanmei-cli/src
```

**Step 5: Run uv sync and verify**

Run: `uv sync`
Expected: Dependencies resolve successfully, click is installed.

**Step 6: Commit**

```bash
git add apps/sanmei-cli/ pyproject.toml Justfile
git commit -m "chore(sanmei-cli): scaffold package and workspace setup"
```

---

### Task 2: Test Fixtures & Gender Type

**Files:**
- Create: `apps/sanmei-cli/tests/conftest.py`
- Create: `apps/sanmei-cli/tests/test_gender_type.py`
- Create: `apps/sanmei-cli/src/sanmei_cli/types.py`

**Step 1: Create test fixtures**

```python
# apps/sanmei-cli/tests/conftest.py
from datetime import datetime, timedelta, timezone

import pytest
from sanmei_core import (
    Gender,
    IsouhouResult,
    Meishiki,
    MeishikiCalculator,
    SchoolRegistry,
    TaiunChart,
    analyze_isouhou,
    calculate_nenun,
    calculate_taiun,
)
from sanmei_core.domain.fortune import Nenun

JST = timezone(timedelta(hours=9))
BIRTH_DT = datetime(2000, 1, 15, 14, 30, tzinfo=JST)


@pytest.fixture
def school():
    registry = SchoolRegistry.create_default()
    return registry.default()


@pytest.fixture
def meishiki(school):
    calc = MeishikiCalculator(school)
    return calc.calculate(BIRTH_DT)


@pytest.fixture
def taiun_chart(meishiki, school):
    return calculate_taiun(
        meishiki,
        BIRTH_DT,
        Gender.MALE,
        school.get_setsuiri_provider(),
        rounding=school.get_taiun_start_age_rounding(),
    )


@pytest.fixture
def nenun_list(school):
    return calculate_nenun(
        BIRTH_DT,
        school.get_setsuiri_provider(),
        year_range=(2020, 2025),
    )


@pytest.fixture
def isouhou_result(meishiki):
    return analyze_isouhou(meishiki.pillars)
```

**Step 2: Write Gender type tests**

```python
# apps/sanmei-cli/tests/test_gender_type.py
import pytest
from click import BadParameter
from sanmei_core import Gender

from sanmei_cli.types import GenderType


class TestGenderType:
    def setup_method(self):
        self.type = GenderType()

    @pytest.mark.parametrize(
        ("input_val", "expected"),
        [
            ("男", Gender.MALE),
            ("male", Gender.MALE),
            ("Male", Gender.MALE),
            ("MALE", Gender.MALE),
            ("m", Gender.MALE),
            ("M", Gender.MALE),
            ("女", Gender.FEMALE),
            ("female", Gender.FEMALE),
            ("Female", Gender.FEMALE),
            ("FEMALE", Gender.FEMALE),
            ("f", Gender.FEMALE),
            ("F", Gender.FEMALE),
        ],
    )
    def test_valid_gender(self, input_val, expected):
        assert self.type.convert(input_val, None, None) == expected

    def test_passthrough_gender_enum(self):
        assert self.type.convert(Gender.MALE, None, None) == Gender.MALE

    def test_invalid_gender(self):
        with pytest.raises(BadParameter):
            self.type.convert("invalid", None, None)
```

**Step 3: Run tests to verify they fail**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_gender_type.py -v`
Expected: FAIL (ModuleNotFoundError: sanmei_cli.types)

**Step 4: Implement Gender type**

```python
# apps/sanmei-cli/src/sanmei_cli/types.py
"""Click custom parameter types."""

from __future__ import annotations

from typing import Any

import click
from sanmei_core import Gender

_GENDER_MAP: dict[str, Gender] = {
    "男": Gender.MALE,
    "male": Gender.MALE,
    "m": Gender.MALE,
    "女": Gender.FEMALE,
    "female": Gender.FEMALE,
    "f": Gender.FEMALE,
}


class GenderType(click.ParamType):
    """Gender parameter accepting 男/male/m and 女/female/f."""

    name = "gender"

    def convert(
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> Gender:
        if isinstance(value, Gender):
            return value
        if not isinstance(value, str):
            self.fail(f"Expected string, got {type(value).__name__}", param, ctx)
        key = value.lower().strip()
        if key in _GENDER_MAP:
            return _GENDER_MAP[key]
        self.fail(
            f"'{value}' は無効な性別です。使用可能: 男/male/m, 女/female/f",
            param,
            ctx,
        )
```

**Step 5: Run tests to verify they pass**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_gender_type.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add apps/sanmei-cli/tests/ apps/sanmei-cli/src/sanmei_cli/types.py
git commit -m "feat(sanmei-cli): add Gender click type with aliases"
```

---

### Task 3: Main CLI Group

**Files:**
- Modify: `apps/sanmei-cli/src/sanmei_cli/main.py`
- Create: `apps/sanmei-cli/tests/test_main.py`

**Step 1: Write test for CLI group**

```python
# apps/sanmei-cli/tests/test_main.py
from click.testing import CliRunner

from sanmei_cli.main import cli


class TestCLIGroup:
    def setup_method(self):
        self.runner = CliRunner()

    def test_help(self):
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "算命学CLI" in result.output

    def test_no_args_shows_help(self):
        result = self.runner.invoke(cli, [])
        assert result.exit_code == 0
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_main.py -v`
Expected: FAIL

**Step 3: Implement main.py**

```python
# apps/sanmei-cli/src/sanmei_cli/main.py
"""算命学CLI エントリポイント."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import click
from sanmei_core import SanmeiError, SchoolRegistry

JST = timezone(timedelta(hours=9))


def build_datetime(birthdate: datetime, birth_time: str) -> datetime:
    """日付と時刻文字列を結合してJST datetimeを生成."""
    t = datetime.strptime(birth_time, "%H:%M").time()
    return datetime.combine(birthdate.date(), t, tzinfo=JST)


@click.group(invoke_without_command=True)
@click.option("--json", "output_json", is_flag=True, default=False, help="JSON形式で出力")
@click.option("--school", "school_name", default="standard", help="流派名 (デフォルト: standard)")
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_main.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/sanmei-cli/src/sanmei_cli/main.py apps/sanmei-cli/tests/test_main.py
git commit -m "feat(sanmei-cli): add main CLI group with common options"
```

---

### Task 4: Meishiki Text Formatter

**Files:**
- Create: `apps/sanmei-cli/src/sanmei_cli/formatters/text.py`
- Create: `apps/sanmei-cli/tests/test_text_formatter.py`

**Step 1: Write formatter test**

```python
# apps/sanmei-cli/tests/test_text_formatter.py
from datetime import datetime, timedelta, timezone

from sanmei_core import Meishiki

from sanmei_cli.formatters.text import format_meishiki

JST = timezone(timedelta(hours=9))
BIRTH_DT = datetime(2000, 1, 15, 14, 30, tzinfo=JST)


class TestFormatMeishiki:
    def test_contains_header(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "=== 命式 ===" in result

    def test_contains_birthdate(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "2000年1月15日 14:30" in result

    def test_contains_pillars_section(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【三柱】" in result
        assert "天干" in result
        assert "地支" in result
        assert "年柱" in result
        assert "月柱" in result
        assert "日柱" in result

    def test_contains_major_stars(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【十大主星】" in result
        assert "北:" in result
        assert "中:" in result

    def test_contains_subsidiary_stars(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【十二大従星】" in result
        assert "年:" in result
        assert "月:" in result
        assert "日:" in result

    def test_contains_tenchuusatsu(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【天中殺】" in result
        assert "天中殺" in result

    def test_contains_gogyo_balance(self, meishiki):
        result = format_meishiki(meishiki, BIRTH_DT)
        assert "【五行バランス】" in result
        assert "木:" in result
        assert "火:" in result
        assert "土:" in result
        assert "金:" in result
        assert "水:" in result
        assert "日主五行:" in result
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_text_formatter.py -v`
Expected: FAIL (ImportError)

**Step 3: Implement meishiki text formatter**

```python
# apps/sanmei-cli/src/sanmei_cli/formatters/text.py
"""テキスト形式フォーマッター."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanmei_core import (
        GoGyoBalance,
        IsouhouResult,
        Meishiki,
        TaiunChart,
    )
    from sanmei_core.domain.fortune import Nenun

_STEM_KANJI = "甲乙丙丁戊己庚辛壬癸"
_BRANCH_KANJI = "子丑寅卯辰巳午未申酉戌亥"


def _stem(stem_val: int) -> str:
    return _STEM_KANJI[stem_val]


def _branch(branch_val: int) -> str:
    return _BRANCH_KANJI[branch_val]


def format_meishiki(meishiki: Meishiki, dt: datetime) -> str:
    """命式をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 命式 ===")
    lines.append(f"生年月日: {dt.year}年{dt.month}月{dt.day}日 {dt.strftime('%H:%M')} (JST)")
    lines.append("")

    # 三柱
    p = meishiki.pillars
    lines.append("【三柱】")
    lines.append(f"{'':8s}{'年柱':10s}{'月柱':10s}{'日柱':10s}")
    lines.append(
        f"{'天干':8s}"
        f"{_stem(p.year.stem.value):10s}"
        f"{_stem(p.month.stem.value):10s}"
        f"{_stem(p.day.stem.value):10s}"
    )
    lines.append(
        f"{'地支':8s}"
        f"{_branch(p.year.branch.value):10s}"
        f"{_branch(p.month.branch.value):10s}"
        f"{_branch(p.day.branch.value):10s}"
    )
    lines.append("")

    # 十大主星
    ms = meishiki.major_stars
    lines.append("【十大主星】")
    lines.append(f"        北: {ms.north.value}")
    lines.append(f"西: {ms.west.value}  中: {ms.center.value}  東: {ms.east.value}")
    lines.append(f"        南: {ms.south.value}")
    lines.append("")

    # 十二大従星
    ss = meishiki.subsidiary_stars
    lines.append("【十二大従星】")
    lines.append(f"年: {ss.year.value}    月: {ss.month.value}    日: {ss.day.value}")
    lines.append("")

    # 天中殺
    lines.append(f"【天中殺】 {meishiki.tenchuusatsu.type.value}")
    lines.append("")

    # 宿命中殺
    if meishiki.shukumei_chuusatsu:
        positions = ", ".join(sc.position.value for sc in meishiki.shukumei_chuusatsu)
        lines.append(f"【宿命中殺】 {positions}")
    else:
        lines.append("【宿命中殺】 なし")
    lines.append("")

    # 五行バランス
    _append_gogyo_balance(lines, meishiki.gogyo_balance)

    return "\n".join(lines)


def _append_gogyo_balance(lines: list[str], gb: GoGyoBalance) -> None:
    tc = gb.total_count
    lines.append("【五行バランス】")
    lines.append(f"木: {tc.wood}  火: {tc.fire}  土: {tc.earth}  金: {tc.metal}  水: {tc.water}")
    lacking_str = ", ".join(g.kanji for g in gb.lacking) if gb.lacking else "なし"
    lines.append(f"主: {gb.dominant.kanji}  欠: {lacking_str}")
    lines.append(f"日主五行: {gb.day_stem_gogyo.kanji}")
```

**Step 4: Run tests to verify they pass**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_text_formatter.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/sanmei-cli/src/sanmei_cli/formatters/text.py apps/sanmei-cli/tests/test_text_formatter.py
git commit -m "feat(sanmei-cli): add meishiki text formatter"
```

---

### Task 5: JSON Formatter

**Files:**
- Create: `apps/sanmei-cli/src/sanmei_cli/formatters/json_fmt.py`
- Create: `apps/sanmei-cli/tests/test_json_formatter.py`

**Step 1: Write JSON formatter test**

```python
# apps/sanmei-cli/tests/test_json_formatter.py
import json

from sanmei_cli.formatters.json_fmt import to_json


class TestToJson:
    def test_meishiki_json(self, meishiki):
        result = to_json(meishiki)
        data = json.loads(result)
        assert "pillars" in data
        assert "major_stars" in data
        assert "tenchuusatsu" in data
        assert "gogyo_balance" in data

    def test_taiun_json(self, taiun_chart):
        result = to_json(taiun_chart)
        data = json.loads(result)
        assert "direction" in data
        assert "periods" in data

    def test_nenun_list_json(self, nenun_list):
        result = to_json(nenun_list)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "year" in data[0]
        assert "kanshi" in data[0]

    def test_isouhou_json(self, isouhou_result):
        result = to_json(isouhou_result)
        data = json.loads(result)
        assert "stem_interactions" in data
        assert "branch_interactions" in data

    def test_japanese_preserved(self, meishiki):
        result = to_json(meishiki)
        # ensure_ascii=False なので日本語がそのまま
        assert "天中殺" in result or "tenchuusatsu" in result
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_json_formatter.py -v`
Expected: FAIL (ImportError)

**Step 3: Implement JSON formatter**

```python
# apps/sanmei-cli/src/sanmei_cli/formatters/json_fmt.py
"""JSON形式フォーマッター."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def to_json(data: Any) -> str:
    """Pydantic モデルまたはリストをJSON文字列に変換."""
    if isinstance(data, BaseModel):
        raw = data.model_dump(mode="json")
    elif isinstance(data, list):
        raw = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in data
        ]
    else:
        raw = data
    return json.dumps(raw, ensure_ascii=False, indent=2, default=str)
```

**Step 4: Run tests to verify they pass**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_json_formatter.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/sanmei-cli/src/sanmei_cli/formatters/json_fmt.py apps/sanmei-cli/tests/test_json_formatter.py
git commit -m "feat(sanmei-cli): add JSON formatter"
```

---

### Task 6: Meishiki Command

**Files:**
- Create: `apps/sanmei-cli/src/sanmei_cli/commands/meishiki.py`
- Create: `apps/sanmei-cli/tests/test_meishiki_cmd.py`
- Modify: `apps/sanmei-cli/src/sanmei_cli/main.py` (register command)

**Step 1: Write integration tests**

```python
# apps/sanmei-cli/tests/test_meishiki_cmd.py
import json

from click.testing import CliRunner

from sanmei_cli.main import cli


class TestMeishikiCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_basic(self):
        result = self.runner.invoke(cli, ["meishiki", "2000-01-15"])
        assert result.exit_code == 0
        assert "=== 命式 ===" in result.output

    def test_with_time(self):
        result = self.runner.invoke(cli, ["meishiki", "2000-01-15", "--time", "14:30"])
        assert result.exit_code == 0
        assert "14:30" in result.output

    def test_json_output(self):
        result = self.runner.invoke(cli, ["--json", "meishiki", "2000-01-15"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "pillars" in data

    def test_invalid_date(self):
        result = self.runner.invoke(cli, ["meishiki", "not-a-date"])
        assert result.exit_code != 0

    def test_out_of_range_date(self):
        result = self.runner.invoke(cli, ["meishiki", "1800-01-01"])
        assert result.exit_code != 0
        assert "エラー" in result.output

    def test_help(self):
        result = self.runner.invoke(cli, ["meishiki", "--help"])
        assert result.exit_code == 0
        assert "BIRTHDATE" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_meishiki_cmd.py -v`
Expected: FAIL

**Step 3: Implement meishiki command**

```python
# apps/sanmei-cli/src/sanmei_cli/commands/meishiki.py
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
```

**Step 4: Register command in main.py**

Add at the bottom of `apps/sanmei-cli/src/sanmei_cli/main.py`:

```python
import sanmei_cli.commands.meishiki as _meishiki_cmd  # noqa: F401
```

**Step 5: Run tests to verify they pass**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_meishiki_cmd.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add apps/sanmei-cli/
git commit -m "feat(sanmei-cli): add meishiki command"
```

---

### Task 7: Taiun Formatter & Command

**Files:**
- Modify: `apps/sanmei-cli/src/sanmei_cli/formatters/text.py` (add format_taiun)
- Create: `apps/sanmei-cli/src/sanmei_cli/commands/taiun.py`
- Create: `apps/sanmei-cli/tests/test_taiun_cmd.py`
- Modify: `apps/sanmei-cli/tests/test_text_formatter.py` (add taiun tests)
- Modify: `apps/sanmei-cli/src/sanmei_cli/main.py` (register command)

**Step 1: Write taiun formatter test**

Add to `apps/sanmei-cli/tests/test_text_formatter.py`:

```python
from sanmei_cli.formatters.text import format_taiun


class TestFormatTaiun:
    def test_contains_header(self, taiun_chart):
        result = format_taiun(taiun_chart)
        assert "=== 大運 ===" in result

    def test_contains_direction(self, taiun_chart):
        result = format_taiun(taiun_chart)
        assert taiun_chart.direction in result

    def test_contains_start_age(self, taiun_chart):
        result = format_taiun(taiun_chart)
        assert f"{taiun_chart.start_age}歳" in result

    def test_contains_period_kanshi(self, taiun_chart):
        result = format_taiun(taiun_chart)
        for period in taiun_chart.periods:
            assert period.kanshi.kanji in result

    def test_contains_age_range(self, taiun_chart):
        result = format_taiun(taiun_chart)
        first = taiun_chart.periods[0]
        assert f"{first.start_age}-{first.end_age}歳" in result
```

**Step 2: Write taiun command integration test**

```python
# apps/sanmei-cli/tests/test_taiun_cmd.py
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
        result = self.runner.invoke(cli, ["--json", "taiun", "2000-01-15", "--gender", "男"])
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
```

**Step 3: Run tests to verify they fail**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_taiun_cmd.py apps/sanmei-cli/tests/test_text_formatter.py::TestFormatTaiun -v`
Expected: FAIL

**Step 4: Implement taiun text formatter**

Add to `apps/sanmei-cli/src/sanmei_cli/formatters/text.py`:

```python
def format_taiun(chart: TaiunChart) -> str:
    """大運をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 大運 ===")
    lines.append(f"方向: {chart.direction}  開始年齢: {chart.start_age}歳")
    lines.append("")
    lines.append(f" {'期間':<8s}{'干支':<8s}{'年齢'}")
    for i, period in enumerate(chart.periods, 1):
        lines.append(
            f" {i:<8d}{period.kanshi.kanji:<8s}{period.start_age}-{period.end_age}歳"
        )
    return "\n".join(lines)
```

**Step 5: Implement taiun command**

```python
# apps/sanmei-cli/src/sanmei_cli/commands/taiun.py
"""taiun サブコマンド."""

from __future__ import annotations

from datetime import datetime

import click
from sanmei_core import MeishikiCalculator, SanmeiError, calculate_taiun

from sanmei_cli.formatters.json_fmt import to_json
from sanmei_cli.formatters.text import format_taiun
from sanmei_cli.main import build_datetime, cli
from sanmei_cli.types import GenderType


@cli.command()
@click.argument("birthdate", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--time", "birth_time", default="00:00", help="出生時刻 (HH:MM)")
@click.option("--gender", required=True, type=GenderType(), help="性別 (男/male/m, 女/female/f)")
@click.option("--periods", default=10, type=int, help="大運の期間数 (デフォルト: 10)")
@click.pass_context
def taiun(
    ctx: click.Context,
    birthdate: datetime,
    birth_time: str,
    gender: click.Parameter,
    periods: int,
) -> None:
    """大運を算出して表示する."""
    try:
        dt = build_datetime(birthdate, birth_time)
        school = ctx.obj["school"]
        calc = MeishikiCalculator(school)
        meishiki = calc.calculate(dt)
        chart = calculate_taiun(
            meishiki,
            dt,
            gender,
            school.get_setsuiri_provider(),
            rounding=school.get_taiun_start_age_rounding(),
            num_periods=periods,
        )

        if ctx.obj["json"]:
            click.echo(to_json(chart))
        else:
            click.echo(format_taiun(chart))
    except SanmeiError as e:
        click.echo(f"エラー: {e}", err=True)
        ctx.exit(1)
```

**Step 6: Register command in main.py**

Add to bottom of `main.py`:

```python
import sanmei_cli.commands.taiun as _taiun_cmd  # noqa: F401
```

**Step 7: Run tests to verify they pass**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_taiun_cmd.py apps/sanmei-cli/tests/test_text_formatter.py::TestFormatTaiun -v`
Expected: All PASS

**Step 8: Commit**

```bash
git add apps/sanmei-cli/
git commit -m "feat(sanmei-cli): add taiun command and formatter"
```

---

### Task 8: Nenun Formatter & Command

**Files:**
- Modify: `apps/sanmei-cli/src/sanmei_cli/formatters/text.py` (add format_nenun)
- Create: `apps/sanmei-cli/src/sanmei_cli/commands/nenun.py`
- Create: `apps/sanmei-cli/tests/test_nenun_cmd.py`
- Modify: `apps/sanmei-cli/tests/test_text_formatter.py` (add nenun tests)
- Modify: `apps/sanmei-cli/src/sanmei_cli/main.py` (register command)

**Step 1: Write nenun formatter test**

Add to `apps/sanmei-cli/tests/test_text_formatter.py`:

```python
from sanmei_cli.formatters.text import format_nenun


class TestFormatNenun:
    def test_contains_header(self, nenun_list):
        result = format_nenun(nenun_list)
        assert "=== 年運 ===" in result

    def test_contains_years(self, nenun_list):
        result = format_nenun(nenun_list)
        for nenun in nenun_list:
            assert str(nenun.year) in result

    def test_contains_kanshi(self, nenun_list):
        result = format_nenun(nenun_list)
        for nenun in nenun_list:
            assert nenun.kanshi.kanji in result

    def test_contains_age(self, nenun_list):
        result = format_nenun(nenun_list)
        for nenun in nenun_list:
            assert f"{nenun.age}歳" in result
```

**Step 2: Write nenun command integration test**

```python
# apps/sanmei-cli/tests/test_nenun_cmd.py
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
```

**Step 3: Run tests to verify they fail**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_nenun_cmd.py apps/sanmei-cli/tests/test_text_formatter.py::TestFormatNenun -v`
Expected: FAIL

**Step 4: Implement nenun text formatter**

Add to `apps/sanmei-cli/src/sanmei_cli/formatters/text.py`:

```python
def format_nenun(nenuns: list[Nenun]) -> str:
    """年運をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 年運 ===")
    lines.append(f" {'年':<8s}{'干支':<8s}{'年齢'}")
    for nenun in nenuns:
        lines.append(f" {nenun.year:<8d}{nenun.kanshi.kanji:<8s}{nenun.age}歳")
    return "\n".join(lines)
```

**Step 5: Implement nenun command**

```python
# apps/sanmei-cli/src/sanmei_cli/commands/nenun.py
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
```

**Step 6: Register command in main.py**

Add to bottom of `main.py`:

```python
import sanmei_cli.commands.nenun as _nenun_cmd  # noqa: F401
```

**Step 7: Run tests to verify they pass**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_nenun_cmd.py apps/sanmei-cli/tests/test_text_formatter.py::TestFormatNenun -v`
Expected: All PASS

**Step 8: Commit**

```bash
git add apps/sanmei-cli/
git commit -m "feat(sanmei-cli): add nenun command and formatter"
```

---

### Task 9: Isouhou Formatter & Command

**Files:**
- Modify: `apps/sanmei-cli/src/sanmei_cli/formatters/text.py` (add format_isouhou)
- Create: `apps/sanmei-cli/src/sanmei_cli/commands/isouhou.py`
- Create: `apps/sanmei-cli/tests/test_isouhou_cmd.py`
- Modify: `apps/sanmei-cli/tests/test_text_formatter.py` (add isouhou tests)
- Modify: `apps/sanmei-cli/src/sanmei_cli/main.py` (register command)

**Step 1: Write isouhou formatter test**

Add to `apps/sanmei-cli/tests/test_text_formatter.py`:

```python
from sanmei_core import IsouhouResult

from sanmei_cli.formatters.text import format_isouhou


class TestFormatIsouhou:
    def test_contains_header(self, isouhou_result):
        result = format_isouhou(isouhou_result)
        assert "=== 位相法" in result

    def test_stem_interactions_shown(self, isouhou_result):
        result = format_isouhou(isouhou_result)
        if isouhou_result.stem_interactions:
            assert "【天干の合】" in result
            for si in isouhou_result.stem_interactions:
                assert si.type.value in result

    def test_branch_interactions_shown(self, isouhou_result):
        result = format_isouhou(isouhou_result)
        if isouhou_result.branch_interactions:
            assert "【地支の関係】" in result
            for bi in isouhou_result.branch_interactions:
                assert bi.type.value in result

    def test_no_interactions(self):
        empty = IsouhouResult(stem_interactions=(), branch_interactions=())
        result = format_isouhou(empty)
        assert "相互作用なし" in result
```

**Step 2: Write isouhou command integration test**

```python
# apps/sanmei-cli/tests/test_isouhou_cmd.py
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
```

**Step 3: Run tests to verify they fail**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_isouhou_cmd.py apps/sanmei-cli/tests/test_text_formatter.py::TestFormatIsouhou -v`
Expected: FAIL

**Step 4: Implement isouhou text formatter**

Add to `apps/sanmei-cli/src/sanmei_cli/formatters/text.py`:

```python
def format_isouhou(result: IsouhouResult) -> str:
    """位相法分析結果をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 位相法（命式内） ===")

    if not result.stem_interactions and not result.branch_interactions:
        lines.append("")
        lines.append("相互作用なし")
        return "\n".join(lines)

    if result.stem_interactions:
        lines.append("")
        lines.append("【天干の合】")
        for si in result.stem_interactions:
            s1 = _stem(si.stems[0].value)
            s2 = _stem(si.stems[1].value)
            lines.append(f"{s1}-{s2} {si.type.value} → {si.result_gogyo.kanji}")

    if result.branch_interactions:
        lines.append("")
        lines.append("【地支の関係】")
        for bi in result.branch_interactions:
            branches_str = "-".join(_branch(b.value) for b in bi.branches)
            if bi.result_gogyo is not None:
                lines.append(f"{branches_str} {bi.type.value} → {bi.result_gogyo.kanji}")
            else:
                lines.append(f"{branches_str} {bi.type.value}")

    return "\n".join(lines)
```

**Step 5: Implement isouhou command**

```python
# apps/sanmei-cli/src/sanmei_cli/commands/isouhou.py
"""isouhou サブコマンド."""

from __future__ import annotations

from datetime import datetime

import click
from sanmei_core import MeishikiCalculator, SanmeiError, analyze_isouhou

from sanmei_cli.formatters.json_fmt import to_json
from sanmei_cli.formatters.text import format_isouhou
from sanmei_cli.main import build_datetime, cli


@cli.command()
@click.argument("birthdate", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--time", "birth_time", default="00:00", help="出生時刻 (HH:MM)")
@click.pass_context
def isouhou(ctx: click.Context, birthdate: datetime, birth_time: str) -> None:
    """位相法（命式内の相互作用）を分析して表示する."""
    try:
        dt = build_datetime(birthdate, birth_time)
        school = ctx.obj["school"]
        calc = MeishikiCalculator(school)
        meishiki = calc.calculate(dt)
        result = analyze_isouhou(meishiki.pillars)

        if ctx.obj["json"]:
            click.echo(to_json(result))
        else:
            click.echo(format_isouhou(result))
    except SanmeiError as e:
        click.echo(f"エラー: {e}", err=True)
        ctx.exit(1)
```

**Step 6: Register command in main.py**

Add to bottom of `main.py`:

```python
import sanmei_cli.commands.isouhou as _isouhou_cmd  # noqa: F401
```

**Step 7: Run tests to verify they pass**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests/test_isouhou_cmd.py apps/sanmei-cli/tests/test_text_formatter.py::TestFormatIsouhou -v`
Expected: All PASS

**Step 8: Commit**

```bash
git add apps/sanmei-cli/
git commit -m "feat(sanmei-cli): add isouhou command and formatter"
```

---

### Task 10: Quality Gate

**Files:**
- Possibly modify any file with lint/type errors

**Step 1: Run all tests**

Run: `uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests -v --cov=sanmei_cli --cov-report=term-missing`
Expected: All PASS, coverage >= 80%

**Step 2: Run linter**

Run: `uv run ruff check apps/ && uv run ruff format --check apps/`
If errors: `uv run ruff check --fix apps/ && uv run ruff format apps/`

**Step 3: Run type checker**

Run: `uv run mypy apps/sanmei-cli/src`
Fix any type errors found.

**Step 4: Run full project check**

Run: `just check`
Expected: All passing (existing packages unaffected).

**Step 5: Manual smoke test**

Run:
```bash
uv run --project apps/sanmei-cli sanmei meishiki 2000-01-15 --time 14:30
uv run --project apps/sanmei-cli sanmei taiun 2000-01-15 --gender m --time 14:30
uv run --project apps/sanmei-cli sanmei nenun 2000-01-15 --from 2020 --to 2025
uv run --project apps/sanmei-cli sanmei isouhou 2000-01-15
uv run --project apps/sanmei-cli sanmei --json meishiki 2000-01-15
```

**Step 6: Commit**

```bash
git add -A
git commit -m "chore(sanmei-cli): pass quality gate (lint + typecheck + coverage)"
```
