# 算命歴変換モジュール実装計画

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 西暦日付から算命学の三柱干支（年柱・月柱・日柱）を算出するコアモジュールを実装する。

**Architecture:** Protocol 中心設計。`SetsuiriProvider` Protocol で節入り日データを抽象化し、流派ごとの差し替えを可能にする。天文計算（Meeus アルゴリズム）をデフォルト実装として提供。日柱計算は Provider 不要の純粋算術。

**Tech Stack:** Python 3.14+, pydantic 2.10+, pytest, ruff strict, mypy strict

**Design doc:** `docs/plans/2026-03-01-sanmei-calendar-design.md`

**Domain knowledge:** `docs/domain/` 配下（特に Chapter 2: 干支、Chapter 3: 命式構造）

**Test command:** `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v`

**Lint/type command:** `just lint && just typecheck`

---

### Task 1: エラー型の定義

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/errors.py`
- Test: `packages/sanmei-core/tests/unit/test_errors.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/test_errors.py
from sanmei_core.domain.errors import (
    DateOutOfRangeError,
    SanmeiError,
    SetsuiriNotFoundError,
)


def test_sanmei_error_is_exception() -> None:
    assert issubclass(SanmeiError, Exception)


def test_date_out_of_range_is_sanmei_error() -> None:
    err = DateOutOfRangeError(1800)
    assert isinstance(err, SanmeiError)
    assert "1800" in str(err)


def test_setsuiri_not_found_is_sanmei_error() -> None:
    err = SetsuiriNotFoundError(2025)
    assert isinstance(err, SanmeiError)
    assert "2025" in str(err)
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/test_errors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sanmei_core.domain.errors'`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/errors.py
"""算命学コアの例外定義."""


class SanmeiError(Exception):
    """sanmei-core の基底例外."""


class DateOutOfRangeError(SanmeiError):
    """対象範囲外の日付 (1864-2100) が指定された."""

    def __init__(self, year: int) -> None:
        super().__init__(f"Year {year} is out of supported range (1864-2100)")
        self.year = year


class SetsuiriNotFoundError(SanmeiError):
    """指定年の節入りデータが見つからない."""

    def __init__(self, year: int) -> None:
        super().__init__(f"Setsuiri data not found for year {year}")
        self.year = year
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/test_errors.py -v`
Expected: 3 passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`
Expected: PASS（sanmei-core 部分）

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/errors.py packages/sanmei-core/tests/unit/test_errors.py
git commit -m "feat(sanmei-core): add error types for calendar module"
```

---

### Task 2: 十干・十二支・干支のドメインモデル

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/kanshi.py`
- Test: `packages/sanmei-core/tests/unit/domain/test_kanshi.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/domain/__init__.py
# (empty)

# packages/sanmei-core/tests/unit/domain/test_kanshi.py
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch


class TestTenStem:
    def test_count(self) -> None:
        assert len(TenStem) == 10

    def test_values_are_sequential(self) -> None:
        for i, stem in enumerate(TenStem):
            assert stem.value == i

    def test_kinoe_is_zero(self) -> None:
        assert TenStem.KINOE.value == 0

    def test_mizunoto_is_nine(self) -> None:
        assert TenStem.MIZUNOTO.value == 9


class TestTwelveBranch:
    def test_count(self) -> None:
        assert len(TwelveBranch) == 12

    def test_values_are_sequential(self) -> None:
        for i, branch in enumerate(TwelveBranch):
            assert branch.value == i

    def test_ne_is_zero(self) -> None:
        assert TwelveBranch.NE.value == 0

    def test_i_is_eleven(self) -> None:
        assert TwelveBranch.I.value == 11


class TestKanshi:
    def test_from_index_kinoe_ne(self) -> None:
        """甲子 = index 0"""
        k = Kanshi.from_index(0)
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.NE
        assert k.index == 0

    def test_from_index_kinoe_inu(self) -> None:
        """甲戌 = index 10"""
        k = Kanshi.from_index(10)
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.INU
        assert k.index == 10

    def test_from_index_mizunoto_i(self) -> None:
        """癸亥 = index 59 (最後)"""
        k = Kanshi.from_index(59)
        assert k.stem == TenStem.MIZUNOTO
        assert k.branch == TwelveBranch.I
        assert k.index == 59

    def test_from_index_wraps_at_60(self) -> None:
        assert Kanshi.from_index(60) == Kanshi.from_index(0)

    def test_sixty_cycle_has_no_duplicates(self) -> None:
        all_kanshi = [Kanshi.from_index(i) for i in range(60)]
        pairs = [(k.stem, k.branch) for k in all_kanshi]
        assert len(set(pairs)) == 60

    def test_kanji_name(self) -> None:
        k = Kanshi.from_index(0)
        assert k.kanji == "甲子"
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_kanshi.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/kanshi.py
"""干支（十干・十二支）のドメインモデル."""

from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel


class TenStem(IntEnum):
    """十干（天干）."""

    KINOE = 0       # 甲 木陽
    KINOTO = 1      # 乙 木陰
    HINOE = 2       # 丙 火陽
    HINOTO = 3      # 丁 火陰
    TSUCHINOE = 4   # 戊 土陽
    TSUCHINOTO = 5  # 己 土陰
    KANOE = 6       # 庚 金陽
    KANOTO = 7      # 辛 金陰
    MIZUNOE = 8     # 壬 水陽
    MIZUNOTO = 9    # 癸 水陰


_STEM_KANJI = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")


class TwelveBranch(IntEnum):
    """十二支（地支）."""

    NE = 0       # 子
    USHI = 1     # 丑
    TORA = 2     # 寅
    U = 3        # 卯
    TATSU = 4    # 辰
    MI = 5       # 巳
    UMA = 6      # 午
    HITSUJI = 7  # 未
    SARU = 8     # 申
    TORI = 9     # 酉
    INU = 10     # 戌
    I = 11       # 亥


_BRANCH_KANJI = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")


class Kanshi(BaseModel, frozen=True):
    """干支（天干+地支のペア）.

    六十干支サイクルの1要素を表す。
    index は 0-59 の通し番号で、stem = index % 10, branch = index % 12。
    """

    stem: TenStem
    branch: TwelveBranch
    index: int

    @classmethod
    def from_index(cls, index: int) -> Kanshi:
        """六十干支の通し番号から Kanshi を生成."""
        idx = index % 60
        return cls(
            stem=TenStem(idx % 10),
            branch=TwelveBranch(idx % 12),
            index=idx,
        )

    @property
    def kanji(self) -> str:
        """漢字表記（例: '甲子'）."""
        return _STEM_KANJI[self.stem.value] + _BRANCH_KANJI[self.branch.value]
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_kanshi.py -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/kanshi.py packages/sanmei-core/tests/unit/domain/
git commit -m "feat(sanmei-core): add TenStem, TwelveBranch, and Kanshi domain models"
```

---

### Task 3: 二十四節気 Enum と SetsuiriDate モデル

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/calendar.py`
- Test: `packages/sanmei-core/tests/unit/domain/test_calendar.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/domain/test_calendar.py
from datetime import UTC, datetime

from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm


class TestSolarTerm:
    def test_setsu_terms_count(self) -> None:
        """節気は12個."""
        setsu = [t for t in SolarTerm if t.is_setsu]
        assert len(setsu) == 12

    def test_chuu_terms_count(self) -> None:
        """中気は12個."""
        chuu = [t for t in SolarTerm if not t.is_setsu]
        assert len(chuu) == 12

    def test_risshun_longitude(self) -> None:
        assert SolarTerm.RISSHUN.longitude == 315.0

    def test_keichitsu_longitude(self) -> None:
        assert SolarTerm.KEICHITSU.longitude == 345.0

    def test_shunbun_is_chuu(self) -> None:
        """春分は中気."""
        assert not SolarTerm.SHUNBUN.is_setsu

    def test_risshun_is_setsu(self) -> None:
        """立春は節気."""
        assert SolarTerm.RISSHUN.is_setsu

    def test_risshun_sanmei_month(self) -> None:
        """立春は算命学1月（寅月）."""
        assert SolarTerm.RISSHUN.sanmei_month == 1


class TestSetsuiriDate:
    def test_create(self) -> None:
        sd = SetsuiriDate(
            year=2024,
            month=1,
            datetime_utc=datetime(2024, 2, 4, 8, 27, tzinfo=UTC),
            solar_term=SolarTerm.RISSHUN,
        )
        assert sd.year == 2024
        assert sd.month == 1
        assert sd.solar_term == SolarTerm.RISSHUN
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_calendar.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/calendar.py
"""算命暦の節入り日・二十四節気モデル."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class SolarTerm(Enum):
    """二十四節気.

    value は (太陽黄経, 節気かどうか, 算命学月 or None) のタプル。
    算命学月は節気のみに割り当て（1=寅月〜12=丑月）。中気は None。
    """

    # --- 春 ---
    RISSHUN = (315.0, True, 1)       # 立春
    USUI = (330.0, False, None)      # 雨水
    KEICHITSU = (345.0, True, 2)     # 啓蟄
    SHUNBUN = (0.0, False, None)     # 春分
    SEIMEI = (15.0, True, 3)         # 清明
    KOKUU = (30.0, False, None)      # 穀雨
    # --- 夏 ---
    RIKKA = (45.0, True, 4)          # 立夏
    SHOUMAN = (60.0, False, None)    # 小満
    BOUSHU = (75.0, True, 5)         # 芒種
    GESHI = (90.0, False, None)      # 夏至
    SHOUSHO = (105.0, True, 6)       # 小暑
    TAISHO = (120.0, False, None)    # 大暑
    # --- 秋 ---
    RISSHUU = (135.0, True, 7)       # 立秋
    SHOSHO = (150.0, False, None)    # 処暑
    HAKURO = (165.0, True, 8)        # 白露
    SHUUBUN = (180.0, False, None)   # 秋分
    KANRO = (195.0, True, 9)         # 寒露
    SOUKOU = (210.0, False, None)    # 霜降
    # --- 冬 ---
    RITTOU = (225.0, True, 10)       # 立冬
    SHOUSETSU = (240.0, False, None) # 小雪
    TAISETSU = (255.0, True, 11)     # 大雪
    TOUJI = (270.0, False, None)     # 冬至
    SHOUKAN = (285.0, True, 12)      # 小寒
    DAIKAN = (300.0, False, None)    # 大寒

    @property
    def longitude(self) -> float:
        """太陽黄経（度）."""
        return self.value[0]

    @property
    def is_setsu(self) -> bool:
        """節気かどうか（True なら月境界）."""
        return self.value[1]

    @property
    def sanmei_month(self) -> int | None:
        """算命学上の月番号（1=寅月〜12=丑月）。中気は None."""
        return self.value[2]


class SetsuiriDate(BaseModel, frozen=True):
    """節入り日.

    特定の年・月における節気の正確な時刻を表す。
    datetime_utc は UTC で保持し、タイムゾーン変換は利用時に行う。
    """

    year: int
    month: int  # 算命学上の月 (1-12, 寅月=1)
    datetime_utc: datetime
    solar_term: SolarTerm
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_calendar.py -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/calendar.py packages/sanmei-core/tests/unit/domain/test_calendar.py
git commit -m "feat(sanmei-core): add SolarTerm enum and SetsuiriDate model"
```

---

### Task 4: 三柱モデルと SetsuiriProvider Protocol

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/pillar.py`
- Create: `packages/sanmei-core/src/sanmei_core/protocols/setsuiri.py`
- Create: `packages/sanmei-core/src/sanmei_core/protocols/__init__.py`
- Test: `packages/sanmei-core/tests/unit/domain/test_pillar.py`
- Test: `packages/sanmei-core/tests/unit/test_protocols.py`

**Step 1: Write the failing tests**

```python
# packages/sanmei-core/tests/unit/domain/test_pillar.py
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.pillar import ThreePillars


def test_three_pillars_creation() -> None:
    year = Kanshi.from_index(0)   # 甲子
    month = Kanshi.from_index(2)  # 丙寅
    day = Kanshi.from_index(10)   # 甲戌
    pillars = ThreePillars(year=year, month=month, day=day)
    assert pillars.year.kanji == "甲子"
    assert pillars.month.kanji == "丙寅"
    assert pillars.day.kanji == "甲戌"
```

```python
# packages/sanmei-core/tests/unit/test_protocols.py
from datetime import UTC, datetime

from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.protocols.setsuiri import SetsuiriProvider


class StubProvider:
    """SetsuiriProvider Protocol を満たすスタブ."""

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        return [
            SetsuiriDate(
                year=year,
                month=1,
                datetime_utc=datetime(year, 2, 4, 8, 0, tzinfo=UTC),
                solar_term=SolarTerm.RISSHUN,
            ),
        ]

    def get_risshun(self, year: int) -> SetsuiriDate:
        return self.get_setsuiri_dates(year)[0]


def test_stub_satisfies_protocol() -> None:
    provider: SetsuiriProvider = StubProvider()
    result = provider.get_risshun(2024)
    assert result.solar_term == SolarTerm.RISSHUN
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_pillar.py packages/sanmei-core/tests/unit/test_protocols.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/pillar.py
"""三柱（年柱・月柱・日柱）のドメインモデル."""

from pydantic import BaseModel

from sanmei_core.domain.kanshi import Kanshi


class ThreePillars(BaseModel, frozen=True):
    """三柱."""

    year: Kanshi
    month: Kanshi
    day: Kanshi
```

```python
# packages/sanmei-core/src/sanmei_core/protocols/__init__.py
# (empty)
```

```python
# packages/sanmei-core/src/sanmei_core/protocols/setsuiri.py
"""SetsuiriProvider Protocol — 節入り日データの供給インターフェース."""

from __future__ import annotations

from typing import Protocol

from sanmei_core.domain.calendar import SetsuiriDate


class SetsuiriProvider(Protocol):
    """節入り日を供給するプロトコル.

    流派ごとに実装を差し替え可能。
    """

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        """指定年の12節入り日（節気のみ、中気は除く）を返す.

        立春〜小寒の12件。算命学の月境界となる節気のみ。
        """
        ...

    def get_risshun(self, year: int) -> SetsuiriDate:
        """指定年の立春（年の境界）を返す."""
        ...
```

**Step 4: Run tests to verify they pass**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_pillar.py packages/sanmei-core/tests/unit/test_protocols.py -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/pillar.py packages/sanmei-core/src/sanmei_core/protocols/ packages/sanmei-core/tests/unit/domain/test_pillar.py packages/sanmei-core/tests/unit/test_protocols.py
git commit -m "feat(sanmei-core): add ThreePillars model and SetsuiriProvider protocol"
```

---

### Task 5: テーブルデータ（六十干支サイクル・五虎遁年法）

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/tables/kanshi_cycle.py`
- Create: `packages/sanmei-core/src/sanmei_core/tables/month_stem.py`
- Test: `packages/sanmei-core/tests/unit/tables/test_kanshi_cycle.py`
- Test: `packages/sanmei-core/tests/unit/tables/test_month_stem.py`

**Step 1: Write the failing tests**

```python
# packages/sanmei-core/tests/unit/tables/__init__.py
# (empty)

# packages/sanmei-core/tests/unit/tables/test_kanshi_cycle.py
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.tables.kanshi_cycle import SIXTY_KANSHI


def test_sixty_kanshi_length() -> None:
    assert len(SIXTY_KANSHI) == 60


def test_first_is_kinoe_ne() -> None:
    """甲子."""
    assert SIXTY_KANSHI[0].stem == TenStem.KINOE
    assert SIXTY_KANSHI[0].branch == TwelveBranch.NE


def test_last_is_mizunoto_i() -> None:
    """癸亥."""
    assert SIXTY_KANSHI[59].stem == TenStem.MIZUNOTO
    assert SIXTY_KANSHI[59].branch == TwelveBranch.I


def test_all_unique() -> None:
    pairs = [(k.stem, k.branch) for k in SIXTY_KANSHI]
    assert len(set(pairs)) == 60


def test_index_matches_position() -> None:
    for i, k in enumerate(SIXTY_KANSHI):
        assert k.index == i
```

```python
# packages/sanmei-core/tests/unit/tables/test_month_stem.py
from sanmei_core.domain.kanshi import TenStem
from sanmei_core.tables.month_stem import get_month_stem


class TestGoKoTonNenHou:
    """五虎遁年法テスト — 年干から各月の天干を決定."""

    def test_kinoe_year_tora_month(self) -> None:
        """甲年の寅月（1月）は丙."""
        assert get_month_stem(TenStem.KINOE, 1) == TenStem.HINOE

    def test_ki_year_tora_month(self) -> None:
        """己年の寅月（1月）も丙."""
        assert get_month_stem(TenStem.TSUCHINOTO, 1) == TenStem.HINOE

    def test_kinoe_year_u_month(self) -> None:
        """甲年の卯月（2月）は丁."""
        assert get_month_stem(TenStem.KINOE, 2) == TenStem.HINOTO

    def test_kinoto_year_tora_month(self) -> None:
        """乙年の寅月（1月）は戊."""
        assert get_month_stem(TenStem.KINOTO, 1) == TenStem.TSUCHINOE

    def test_all_five_patterns_tora(self) -> None:
        """五虎遁年法の全5パターン（寅月）."""
        expected = {
            TenStem.KINOE: TenStem.HINOE,       # 甲 → 丙
            TenStem.KINOTO: TenStem.TSUCHINOE,   # 乙 → 戊
            TenStem.HINOE: TenStem.KANOE,        # 丙 → 庚
            TenStem.HINOTO: TenStem.MIZUNOE,     # 丁 → 壬
            TenStem.TSUCHINOE: TenStem.KINOE,    # 戊 → 甲
            TenStem.TSUCHINOTO: TenStem.HINOE,   # 己 → 丙
            TenStem.KANOE: TenStem.TSUCHINOE,    # 庚 → 戊
            TenStem.KANOTO: TenStem.KANOE,       # 辛 → 庚
            TenStem.MIZUNOE: TenStem.MIZUNOE,    # 壬 → 壬
            TenStem.MIZUNOTO: TenStem.KINOE,     # 癸 → 甲
        }
        for year_stem, expected_month_stem in expected.items():
            assert get_month_stem(year_stem, 1) == expected_month_stem, (
                f"year_stem={year_stem.name}"
            )

    def test_month_12_wraps(self) -> None:
        """甲年の丑月（12月）は丁."""
        # 丙(寅) + 11 = 丁(丑) ... (2 + 11) % 10 = 3 = 丁
        assert get_month_stem(TenStem.KINOE, 12) == TenStem.HINOTO
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/tables/ -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/tables/kanshi_cycle.py
"""六十干支サイクルテーブル."""

from sanmei_core.domain.kanshi import Kanshi

SIXTY_KANSHI: tuple[Kanshi, ...] = tuple(Kanshi.from_index(i) for i in range(60))
```

```python
# packages/sanmei-core/src/sanmei_core/tables/month_stem.py
"""五虎遁年法 — 年干から月干を決定するテーブル."""

from sanmei_core.domain.kanshi import TenStem

# 年干 → 寅月（算命学1月）の天干
# 甲・己 → 丙, 乙・庚 → 戊, 丙・辛 → 庚, 丁・壬 → 壬, 戊・癸 → 甲
_TORA_STEM: dict[TenStem, TenStem] = {
    TenStem.KINOE: TenStem.HINOE,
    TenStem.TSUCHINOTO: TenStem.HINOE,
    TenStem.KINOTO: TenStem.TSUCHINOE,
    TenStem.KANOE: TenStem.TSUCHINOE,
    TenStem.HINOE: TenStem.KANOE,
    TenStem.KANOTO: TenStem.KANOE,
    TenStem.HINOTO: TenStem.MIZUNOE,
    TenStem.MIZUNOE: TenStem.MIZUNOE,
    TenStem.TSUCHINOE: TenStem.KINOE,
    TenStem.MIZUNOTO: TenStem.KINOE,
}


def get_month_stem(year_stem: TenStem, sanmei_month: int) -> TenStem:
    """五虎遁年法で月干を算出.

    Args:
        year_stem: 年柱の天干
        sanmei_month: 算命学上の月 (1=寅月〜12=丑月)

    Returns:
        該当月の天干
    """
    tora_stem = _TORA_STEM[year_stem]
    return TenStem((tora_stem.value + sanmei_month - 1) % 10)
```

**Step 4: Run tests to verify they pass**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/tables/ -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/tables/kanshi_cycle.py packages/sanmei-core/src/sanmei_core/tables/month_stem.py packages/sanmei-core/tests/unit/tables/
git commit -m "feat(sanmei-core): add sixty kanshi cycle and go-ko-ton-nen-hou table"
```

---

### Task 6: 日柱計算

SetsuiriProvider 不要の純粋算術。最もシンプルなので最初に実装。

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/day_pillar.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_day_pillar.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/__init__.py
# (empty)

# packages/sanmei-core/tests/unit/calculators/test_day_pillar.py
from datetime import datetime, timezone

from sanmei_core.calculators.day_pillar import day_pillar
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

JST = timezone.utc.__class__(offset=__import__("datetime").timedelta(hours=9))


class TestDayPillar:
    def test_reference_date_1900_01_01(self) -> None:
        """基準日: 1900-01-01 = 甲戌 (index 10)."""
        k = day_pillar(datetime(1900, 1, 1, tzinfo=JST))
        assert k.index == 10
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.INU

    def test_sixty_day_cycle(self) -> None:
        """60日後は同じ干支に戻る."""
        k1 = day_pillar(datetime(1900, 1, 1, tzinfo=JST))
        k2 = day_pillar(datetime(1900, 3, 2, tzinfo=JST))
        assert k1.index == k2.index

    def test_next_day(self) -> None:
        """1900-01-02 = 乙亥 (index 11)."""
        k = day_pillar(datetime(1900, 1, 2, tzinfo=JST))
        assert k.index == 11

    def test_year_2000_jan_1(self) -> None:
        """2000-01-01 の日柱.

        1900-01-01 から 36524 日後。
        (10 + 36524) % 60 = 36534 % 60 = 54
        """
        k = day_pillar(datetime(2000, 1, 1, tzinfo=JST))
        assert k.index == 54

    def test_date_before_reference(self) -> None:
        """1899-12-31 = 癸酉 (index 9)."""
        k = day_pillar(datetime(1899, 12, 31, tzinfo=JST))
        assert k.index == 9

    def test_timezone_affects_date(self) -> None:
        """UTC 23:30 は JST で翌日。異なる日柱になりうる."""
        utc = timezone.utc
        # UTC 2000-01-01 23:30 = JST 2000-01-02 08:30
        k_utc = day_pillar(datetime(2000, 1, 1, 23, 30, tzinfo=utc), tz=utc)
        k_jst = day_pillar(datetime(2000, 1, 1, 23, 30, tzinfo=utc), tz=JST)
        # JST では翌日扱いなので index が 1 違う
        assert (k_jst.index - k_utc.index) % 60 == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_day_pillar.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/day_pillar.py
"""日柱計算 — 西暦日付から日干支を算出."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone, tzinfo

from sanmei_core.domain.kanshi import Kanshi

JST = timezone(timedelta(hours=9))

# 基準日: 1900-01-01 = 甲戌 (六十干支 index 10)
_REFERENCE_DATE = date(1900, 1, 1)
_REFERENCE_INDEX = 10


def day_pillar(dt: datetime, *, tz: tzinfo | None = None) -> Kanshi:
    """日柱の干支を算出.

    Args:
        dt: 対象日時（timezone-aware を推奨）
        tz: 日付判定に使うタイムゾーン。None の場合は JST。

    Returns:
        日柱の干支
    """
    if tz is None:
        tz = JST
    local_dt = dt.astimezone(tz)
    local_date = local_dt.date()
    diff = (local_date - _REFERENCE_DATE).days
    index = (_REFERENCE_INDEX + diff) % 60
    return Kanshi.from_index(index)
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_day_pillar.py -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/day_pillar.py packages/sanmei-core/tests/unit/calculators/
git commit -m "feat(sanmei-core): implement day pillar calculation"
```

---

### Task 7: 年柱計算

立春の境界判定を含む。SetsuiriProvider から立春データを取得。

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/year_pillar.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_year_pillar.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_year_pillar.py
from datetime import UTC, datetime, timedelta, timezone

from sanmei_core.calculators.year_pillar import year_pillar
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

JST = timezone(timedelta(hours=9))


def _risshun(year: int, month: int, day: int, hour: int) -> SetsuiriDate:
    """テスト用ヘルパー: 立春の SetsuiriDate を JST 時刻から作成."""
    jst_dt = datetime(year, month, day, hour, 0, tzinfo=JST)
    return SetsuiriDate(
        year=year,
        month=1,
        datetime_utc=jst_dt.astimezone(UTC),
        solar_term=SolarTerm.RISSHUN,
    )


class TestYearPillar:
    def test_2024_after_risshun(self) -> None:
        """2024年立春(2/4 17:27 JST)後 → 甲辰.

        (2024 - 4) % 10 = 0 = 甲, (2024 - 4) % 12 = 4 = 辰
        """
        risshun = _risshun(2024, 2, 4, 18)  # 立春の1時間後
        dt = datetime(2024, 3, 1, 12, 0, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.TATSU

    def test_2024_before_risshun(self) -> None:
        """2024年立春前 → 2023年 = 癸卯.

        (2023 - 4) % 10 = 9 = 癸, (2023 - 4) % 12 = 3 = 卯
        """
        risshun = _risshun(2024, 2, 4, 18)
        dt = datetime(2024, 1, 15, 12, 0, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.MIZUNOTO
        assert k.branch == TwelveBranch.U

    def test_risshun_boundary_exact(self) -> None:
        """立春の瞬間 → 当年の干支."""
        risshun = _risshun(2024, 2, 4, 17)
        dt = datetime(2024, 2, 4, 17, 0, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.KINOE  # 2024年

    def test_risshun_boundary_one_minute_before(self) -> None:
        """立春の1分前 → 前年の干支."""
        risshun = _risshun(2024, 2, 4, 17)
        dt = datetime(2024, 2, 4, 16, 59, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.MIZUNOTO  # 2023年

    def test_1864_kinoe_ne(self) -> None:
        """1864年 = 甲子 (六十干支の起点)."""
        risshun = _risshun(1864, 2, 4, 12)
        dt = datetime(1864, 6, 1, 12, 0, tzinfo=JST)
        k = year_pillar(dt, risshun, tz=JST)
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.NE
        assert k.index == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_year_pillar.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/year_pillar.py
"""年柱計算 — 立春を境界として年干支を算出."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo

from sanmei_core.domain.calendar import SetsuiriDate
from sanmei_core.domain.kanshi import Kanshi

JST = timezone(timedelta(hours=9))


def year_pillar(
    dt: datetime,
    risshun: SetsuiriDate,
    *,
    tz: tzinfo | None = None,
) -> Kanshi:
    """年柱の干支を算出.

    立春より前なら前年の干支、立春以降なら当年の干支を使用。
    基準: 西暦4年 = 甲子 (index 0)。

    Args:
        dt: 対象日時
        risshun: 当年の立春データ
        tz: タイムゾーン。None の場合は JST。

    Returns:
        年柱の干支
    """
    if tz is None:
        tz = JST
    local_dt = dt.astimezone(tz)
    risshun_local = risshun.datetime_utc.astimezone(tz)

    year = local_dt.year
    if local_dt < risshun_local:
        year -= 1

    index = (year - 4) % 60
    return Kanshi.from_index(index)
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_year_pillar.py -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/year_pillar.py packages/sanmei-core/tests/unit/calculators/test_year_pillar.py
git commit -m "feat(sanmei-core): implement year pillar calculation with risshun boundary"
```

---

### Task 8: 月柱計算

節入り日リストから該当月を特定し、五虎遁年法で月干を算出。

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/month_pillar.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_month_pillar.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_month_pillar.py
from datetime import UTC, datetime, timedelta, timezone

from sanmei_core.calculators.month_pillar import month_pillar
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

JST = timezone(timedelta(hours=9))

# 節気の太陽黄経順（算命学月1〜12）に対応する SolarTerm
_SETSU_TERMS = [
    SolarTerm.RISSHUN,   # 1月 寅
    SolarTerm.KEICHITSU, # 2月 卯
    SolarTerm.SEIMEI,    # 3月 辰
    SolarTerm.RIKKA,     # 4月 巳
    SolarTerm.BOUSHU,    # 5月 午
    SolarTerm.SHOUSHO,   # 6月 未
    SolarTerm.RISSHUU,   # 7月 申
    SolarTerm.HAKURO,    # 8月 酉
    SolarTerm.KANRO,     # 9月 戌
    SolarTerm.RITTOU,    # 10月 亥
    SolarTerm.TAISETSU,  # 11月 子
    SolarTerm.SHOUKAN,   # 12月 丑
]

# 2024年のおおよその節入り日（JST、テスト用固定データ）
_SETSUIRI_2024_JST = [
    (2024, 2, 4, 17),    # 立春
    (2024, 3, 5, 11),    # 啓蟄
    (2024, 4, 4, 16),    # 清明
    (2024, 5, 5, 9),     # 立夏
    (2024, 6, 5, 13),    # 芒種
    (2024, 7, 6, 23),    # 小暑
    (2024, 8, 7, 9),     # 立秋
    (2024, 9, 7, 12),    # 白露
    (2024, 10, 8, 4),    # 寒露
    (2024, 11, 7, 7),    # 立冬
    (2024, 12, 7, 0),    # 大雪
    (2025, 1, 5, 11),    # 小寒（翌年1月）
]


def _make_setsuiri_dates() -> list[SetsuiriDate]:
    result = []
    for i, (y, m, d, h) in enumerate(_SETSUIRI_2024_JST):
        jst_dt = datetime(y, m, d, h, 0, tzinfo=JST)
        result.append(
            SetsuiriDate(
                year=2024,
                month=i + 1,
                datetime_utc=jst_dt.astimezone(UTC),
                solar_term=_SETSU_TERMS[i],
            )
        )
    return result


class TestMonthPillar:
    def test_march_2024_is_u_month(self) -> None:
        """2024年3月15日 → 啓蟄(3/5)後、清明(4/4)前 → 卯月（算命学2月）.

        月支 = 卯(3)。年干=甲 → 寅月天干=丙 → 卯月天干=丁。
        """
        dates = _make_setsuiri_dates()
        year_stem = TenStem.KINOE  # 甲年
        dt = datetime(2024, 3, 15, 12, 0, tzinfo=JST)
        k = month_pillar(dt, dates, year_stem, tz=JST)
        assert k.branch == TwelveBranch.U  # 卯
        assert k.stem == TenStem.HINOTO  # 丁

    def test_feb_2024_before_risshun_is_previous_chou(self) -> None:
        """2024年2月1日 → 立春(2/4)前 → 丑月（算命学12月）.

        前年の最後の月。year_stem は前年(癸)のもの。
        癸年 → 寅月天干=甲 → 丑月(12月)天干 = (甲+11) % 10 = 乙
        """
        dates = _make_setsuiri_dates()
        year_stem = TenStem.MIZUNOTO  # 癸年（前年）
        dt = datetime(2024, 2, 1, 12, 0, tzinfo=JST)
        k = month_pillar(dt, dates, year_stem, tz=JST)
        assert k.branch == TwelveBranch.USHI  # 丑

    def test_risshun_boundary_exact(self) -> None:
        """立春の瞬間 → 寅月."""
        dates = _make_setsuiri_dates()
        year_stem = TenStem.KINOE
        dt = datetime(2024, 2, 4, 17, 0, tzinfo=JST)
        k = month_pillar(dt, dates, year_stem, tz=JST)
        assert k.branch == TwelveBranch.TORA  # 寅

    def test_all_five_year_stem_patterns(self) -> None:
        """五虎遁年法の全5パターンで寅月の月干を検証."""
        dates = _make_setsuiri_dates()
        dt = datetime(2024, 2, 10, 12, 0, tzinfo=JST)  # 寅月中
        expected_pairs = [
            (TenStem.KINOE, TenStem.HINOE),       # 甲 → 丙寅
            (TenStem.KINOTO, TenStem.TSUCHINOE),   # 乙 → 戊寅
            (TenStem.HINOE, TenStem.KANOE),        # 丙 → 庚寅
            (TenStem.HINOTO, TenStem.MIZUNOE),     # 丁 → 壬寅
            (TenStem.TSUCHINOE, TenStem.KINOE),    # 戊 → 甲寅
        ]
        for year_stem, expected_month_stem in expected_pairs:
            k = month_pillar(dt, dates, year_stem, tz=JST)
            assert k.stem == expected_month_stem, f"year_stem={year_stem.name}"
            assert k.branch == TwelveBranch.TORA
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_month_pillar.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/month_pillar.py
"""月柱計算 — 節入り日から月干支を算出."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo

from sanmei_core.domain.calendar import SetsuiriDate
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.tables.month_stem import get_month_stem

JST = timezone(timedelta(hours=9))


def month_pillar(
    dt: datetime,
    setsuiri_dates: list[SetsuiriDate],
    year_stem: TenStem,
    *,
    tz: tzinfo | None = None,
) -> Kanshi:
    """月柱の干支を算出.

    節入り日リストから該当月を特定し、五虎遁年法で月干を決定。

    Args:
        dt: 対象日時
        setsuiri_dates: 当年の12節入り日（立春〜小寒）
        year_stem: 年柱の天干（五虎遁年法の入力）
        tz: タイムゾーン。None の場合は JST。

    Returns:
        月柱の干支
    """
    if tz is None:
        tz = JST
    local_dt = dt.astimezone(tz)

    # 節入り日を時系列ソート
    sorted_dates = sorted(setsuiri_dates, key=lambda s: s.datetime_utc)

    # date がどの節入り日の間に入るかを判定
    sanmei_month = _find_sanmei_month(local_dt, sorted_dates, tz)

    # 月支: 寅(2) から算命学月番号分オフセット
    branch = TwelveBranch((TwelveBranch.TORA.value + sanmei_month - 1) % 12)

    # 月干: 五虎遁年法
    stem = get_month_stem(year_stem, sanmei_month)

    # 六十干支 index を算出
    index = _stem_branch_to_index(stem, branch)
    return Kanshi(stem=stem, branch=branch, index=index)


def _find_sanmei_month(
    local_dt: datetime,
    sorted_dates: list[SetsuiriDate],
    tz: tzinfo,
) -> int:
    """対象日時が属する算命学月を特定.

    Returns:
        算命学月 (1=寅月〜12=丑月)
    """
    # 逆順に走査し、最初に「節入り日 <= local_dt」となる月を見つける
    for sd in reversed(sorted_dates):
        setsuiri_local = sd.datetime_utc.astimezone(tz)
        if local_dt >= setsuiri_local:
            return sd.month

    # 全節入り日より前 → 前年の丑月(12月)
    return 12


def _stem_branch_to_index(stem: TenStem, branch: TwelveBranch) -> int:
    """天干と地支から六十干支の index を算出."""
    # stem = index % 10, branch = index % 12
    # 中国剰余定理: index = (6 * stem - 5 * branch) % 60
    return (6 * stem.value - 5 * branch.value) % 60
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_month_pillar.py -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/month_pillar.py packages/sanmei-core/tests/unit/calculators/test_month_pillar.py
git commit -m "feat(sanmei-core): implement month pillar calculation with go-ko-ton-nen-hou"
```

---

### Task 9: 太陽黄経計算（Meeus アルゴリズム）+ MeeusSetsuiriProvider

最も複雑なタスク。Jean Meeus のアルゴリズムで太陽黄経を計算し、二分探索で節入り時刻を特定する。

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/solar_longitude.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_solar_longitude.py`

**参考:** Jean Meeus, *Astronomical Algorithms*, 2nd Edition, Chapter 25 (Solar Coordinates)

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_solar_longitude.py
from datetime import UTC, datetime, timedelta, timezone

import pytest

from sanmei_core.calculators.solar_longitude import (
    MeeusSetsuiriProvider,
    solar_longitude,
)
from sanmei_core.domain.calendar import SolarTerm

JST = timezone(timedelta(hours=9))


class TestSolarLongitude:
    def test_vernal_equinox_2024(self) -> None:
        """2024年春分 (3/20 12:06 UTC 付近) → 黄経 ≈ 0°."""
        dt = datetime(2024, 3, 20, 12, 0, tzinfo=UTC)
        jde = _datetime_to_jde(dt)
        lon = solar_longitude(jde)
        assert abs(lon) < 0.5 or abs(lon - 360) < 0.5

    def test_summer_solstice_2024(self) -> None:
        """2024年夏至 (6/20 20:51 UTC 付近) → 黄経 ≈ 90°."""
        dt = datetime(2024, 6, 20, 21, 0, tzinfo=UTC)
        jde = _datetime_to_jde(dt)
        lon = solar_longitude(jde)
        assert abs(lon - 90) < 0.5

    def test_risshun_2024(self) -> None:
        """2024年立春 (2/4 08:27 UTC 付近) → 黄経 ≈ 315°."""
        dt = datetime(2024, 2, 4, 8, 30, tzinfo=UTC)
        jde = _datetime_to_jde(dt)
        lon = solar_longitude(jde)
        assert abs(lon - 315) < 0.5


class TestMeeusSetsuiriProvider:
    def test_risshun_2024(self) -> None:
        """2024年の立春は2月4日(JST)."""
        provider = MeeusSetsuiriProvider()
        risshun = provider.get_risshun(2024)
        risshun_jst = risshun.datetime_utc.astimezone(JST)
        assert risshun_jst.month == 2
        assert risshun_jst.day == 4
        assert risshun.solar_term == SolarTerm.RISSHUN

    def test_setsuiri_dates_count(self) -> None:
        """1年分の節入り日は12件."""
        provider = MeeusSetsuiriProvider()
        dates = provider.get_setsuiri_dates(2024)
        assert len(dates) == 12

    def test_setsuiri_dates_are_chronological(self) -> None:
        """節入り日は時系列順."""
        provider = MeeusSetsuiriProvider()
        dates = provider.get_setsuiri_dates(2024)
        for i in range(len(dates) - 1):
            assert dates[i].datetime_utc < dates[i + 1].datetime_utc

    def test_risshun_2024_hour_precision(self) -> None:
        """2024年立春の精度: ±1時間以内.

        実際の立春: 2024-02-04 17:27 JST = 08:27 UTC
        """
        provider = MeeusSetsuiriProvider()
        risshun = provider.get_risshun(2024)
        expected = datetime(2024, 2, 4, 8, 27, tzinfo=UTC)
        diff = abs((risshun.datetime_utc - expected).total_seconds())
        assert diff < 3600, f"Diff: {diff}s (expected < 3600s)"

    def test_supported_range(self) -> None:
        """1864-2100 の範囲で立春を計算可能."""
        provider = MeeusSetsuiriProvider()
        for year in [1864, 1900, 1950, 2000, 2024, 2050, 2100]:
            risshun = provider.get_risshun(year)
            risshun_jst = risshun.datetime_utc.astimezone(JST)
            # 立春は常に2月（±数日）
            assert risshun_jst.month == 2, f"Year {year}: month={risshun_jst.month}"
            assert 2 <= risshun_jst.day <= 5, f"Year {year}: day={risshun_jst.day}"


def _datetime_to_jde(dt: datetime) -> float:
    """datetime → Julian Ephemeris Day 変換（テスト用ヘルパー）."""
    from sanmei_core.calculators.solar_longitude import datetime_to_jde
    return datetime_to_jde(dt)
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_solar_longitude.py -v`
Expected: FAIL

**Step 3: Write implementation**

これは大きい実装なので、以下の構成で `solar_longitude.py` を作成する:

1. `datetime_to_jde(dt)` — datetime → Julian Ephemeris Day
2. `jde_to_datetime(jde)` — JDE → datetime (UTC)
3. `solar_longitude(jde)` — JDE から太陽黄経を計算（Meeus Chapter 25）
4. `_find_solar_term_time(year, target_longitude)` — 二分探索で節入り時刻を特定
5. `MeeusSetsuiriProvider` — SetsuiriProvider Protocol 実装

```python
# packages/sanmei-core/src/sanmei_core/calculators/solar_longitude.py
"""太陽黄経計算（Jean Meeus アルゴリズム）と MeeusSetsuiriProvider.

Jean Meeus, *Astronomical Algorithms*, 2nd Edition, Chapter 25 に基づく。
VSOP87 簡略版を使用。精度: ±0.01° (≒ ±15分)。
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm

# --- Julian Day Number 変換 ---

_J2000 = 2451545.0  # 2000-01-01 12:00 TT の JDE
_UNIX_EPOCH_JDE = 2440587.5  # 1970-01-01 00:00 UTC の JDE


def datetime_to_jde(dt: datetime) -> float:
    """datetime (UTC) → Julian Ephemeris Day.

    簡略化のため ΔT（TT-UTC 差）は無視。
    対象範囲(1864-2100)では最大 ΔT ≈ 70秒で、時単位精度には影響なし。
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    delta = dt - datetime(2000, 1, 1, 12, 0, 0)
    return _J2000 + delta.total_seconds() / 86400.0


def jde_to_datetime(jde: float) -> datetime:
    """Julian Ephemeris Day → datetime (UTC)."""
    delta_days = jde - _J2000
    return datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC) + timedelta(days=delta_days)


# --- 太陽黄経計算 (Meeus Chapter 25) ---

def solar_longitude(jde: float) -> float:
    """JDE から太陽の幾何学的黄経（度）を計算.

    Meeus, Astronomical Algorithms, 2nd ed., Chapter 25.
    低精度バージョン（Table 25.C の主要項）。
    """
    # Julian centuries from J2000.0
    t = (jde - _J2000) / 36525.0

    # 太陽の平均黄経 (L0) — degree
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    l0 = l0 % 360

    # 太陽の平均近点角 (M) — degree
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    m_rad = math.radians(m % 360)

    # 中心差 (C)
    c = (
        (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m_rad)
        + (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
        + 0.000289 * math.sin(3 * m_rad)
    )

    # 太陽の真黄経
    sun_lon = l0 + c

    # 章動と光行差の補正 (簡略)
    omega = 125.04 - 1934.136 * t
    omega_rad = math.radians(omega)
    apparent_lon = sun_lon - 0.00569 - 0.00478 * math.sin(omega_rad)

    return apparent_lon % 360


# --- 節入り日計算 ---

# 節気（月境界）の SolarTerm を算命学月順に列挙
_SETSU_TERMS: tuple[SolarTerm, ...] = (
    SolarTerm.RISSHUN,   # 1月 寅 315°
    SolarTerm.KEICHITSU, # 2月 卯 345°
    SolarTerm.SEIMEI,    # 3月 辰 15°
    SolarTerm.RIKKA,     # 4月 巳 45°
    SolarTerm.BOUSHU,    # 5月 午 75°
    SolarTerm.SHOUSHO,   # 6月 未 105°
    SolarTerm.RISSHUU,   # 7月 申 135°
    SolarTerm.HAKURO,    # 8月 酉 165°
    SolarTerm.KANRO,     # 9月 戌 195°
    SolarTerm.RITTOU,    # 10月 亥 225°
    SolarTerm.TAISETSU,  # 11月 子 255°
    SolarTerm.SHOUKAN,   # 12月 丑 285°
)

# 各節気のおおよその月日（探索範囲の初期推定用）
_APPROX_MONTH_DAY: tuple[tuple[int, int], ...] = (
    (2, 4),   # 立春
    (3, 6),   # 啓蟄
    (4, 5),   # 清明
    (5, 6),   # 立夏
    (6, 6),   # 芒種
    (7, 7),   # 小暑
    (8, 7),   # 立秋
    (9, 8),   # 白露
    (10, 8),  # 寒露
    (11, 7),  # 立冬
    (12, 7),  # 大雪
    (1, 6),   # 小寒（翌年1月）
)


def _find_solar_term_time(
    year: int,
    target_longitude: float,
    approx_month: int,
    approx_day: int,
) -> datetime:
    """二分探索で太陽黄経が target_longitude に達する UTC 時刻を求める.

    探索精度: 約1分。
    """
    # 小寒は翌年1月
    search_year = year + 1 if approx_month == 1 else year
    center = datetime(search_year, approx_month, approx_day, 12, 0, tzinfo=UTC)
    # ±15日の範囲で探索
    lo_jde = datetime_to_jde(center - timedelta(days=15))
    hi_jde = datetime_to_jde(center + timedelta(days=15))

    target = target_longitude

    # 黄経は 0°/360° をまたぐことがあるので正規化
    def _normalized_longitude(jde: float) -> float:
        lon = solar_longitude(jde)
        if target > 180:
            # target が 315° 等の場合、0° 付近を +360 にして連続化
            if lon < 180:
                lon += 360
        return lon

    if target > 180:
        target_normalized = target
    else:
        target_normalized = target

    for _ in range(64):  # 十分な反復回数
        mid_jde = (lo_jde + hi_jde) / 2
        mid_lon = _normalized_longitude(mid_jde)
        if mid_lon < target_normalized:
            lo_jde = mid_jde
        else:
            hi_jde = mid_jde
        if (hi_jde - lo_jde) < 0.0005:  # ≈ 43秒
            break

    result_jde = (lo_jde + hi_jde) / 2
    return jde_to_datetime(result_jde)


# --- MeeusSetsuiriProvider ---

class MeeusSetsuiriProvider:
    """Jean Meeus のアルゴリズムに基づく SetsuiriProvider 実装.

    太陽黄経を計算し、各節気の正確な時刻を二分探索で特定する。
    精度: ±15分（時単位要件に十分）。
    対象範囲: 1864-2100年。
    """

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        """指定年の12節入り日を算出."""
        results: list[SetsuiriDate] = []
        for i, term in enumerate(_SETSU_TERMS):
            approx_m, approx_d = _APPROX_MONTH_DAY[i]
            dt_utc = _find_solar_term_time(
                year, term.longitude, approx_m, approx_d,
            )
            results.append(
                SetsuiriDate(
                    year=year,
                    month=i + 1,
                    datetime_utc=dt_utc,
                    solar_term=term,
                )
            )
        return results

    def get_risshun(self, year: int) -> SetsuiriDate:
        """指定年の立春を算出."""
        approx_m, approx_d = _APPROX_MONTH_DAY[0]
        dt_utc = _find_solar_term_time(
            year, SolarTerm.RISSHUN.longitude, approx_m, approx_d,
        )
        return SetsuiriDate(
            year=year,
            month=1,
            datetime_utc=dt_utc,
            solar_term=SolarTerm.RISSHUN,
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_solar_longitude.py -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/solar_longitude.py packages/sanmei-core/tests/unit/calculators/test_solar_longitude.py
git commit -m "feat(sanmei-core): implement Meeus solar longitude and MeeusSetsuiriProvider"
```

---

### Task 10: SanmeiCalendar ファサード

全てを統合するエントリポイント。

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/pillar_calculator.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_pillar_calculator.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_pillar_calculator.py
from datetime import UTC, datetime, timedelta, timezone

import pytest

from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.solar_longitude import MeeusSetsuiriProvider
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.errors import DateOutOfRangeError
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.protocols.setsuiri import SetsuiriProvider

JST = timezone(timedelta(hours=9))


class MockSetsuiriProvider:
    """テスト用の固定データ Provider."""

    def __init__(self, data: dict[int, list[SetsuiriDate]]) -> None:
        self._data = data

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        return self._data[year]

    def get_risshun(self, year: int) -> SetsuiriDate:
        dates = self._data[year]
        return next(d for d in dates if d.solar_term == SolarTerm.RISSHUN)


class TestSanmeiCalendar:
    def test_three_pillars_returns_all(self) -> None:
        """三柱が全て返される."""
        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        pillars = cal.three_pillars(datetime(2024, 6, 15, 12, 0, tzinfo=JST))
        assert pillars.year is not None
        assert pillars.month is not None
        assert pillars.day is not None

    def test_day_pillar_consistency(self) -> None:
        """ファサード経由の日柱が個別関数と一致."""
        from sanmei_core.calculators.day_pillar import day_pillar

        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        assert cal.day_pillar(dt) == day_pillar(dt, tz=JST)

    def test_date_out_of_range_raises(self) -> None:
        """範囲外の日付でエラー."""
        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        with pytest.raises(DateOutOfRangeError):
            cal.three_pillars(datetime(1800, 1, 1, tzinfo=JST))

    def test_date_out_of_range_future(self) -> None:
        """未来すぎる日付でエラー."""
        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        with pytest.raises(DateOutOfRangeError):
            cal.three_pillars(datetime(2200, 1, 1, tzinfo=JST))


class TestSanmeiCalendarWithMeeus:
    """MeeusSetsuiriProvider を使った統合テスト."""

    def test_2024_06_15(self) -> None:
        """2024年6月15日(JST) の三柱.

        年柱: 2024年 → (2024-4)%60=0 → 甲辰 (立春後)
        月柱: 芒種(6/5)後、小暑(7/6)前 → 午月(5月)
              甲年の午月天干: 丙+4 = 庚
        日柱: (10 + days_since_1900)%60 を計算
        """
        cal = SanmeiCalendar(MeeusSetsuiriProvider(), tz=JST)
        pillars = cal.three_pillars(datetime(2024, 6, 15, 12, 0, tzinfo=JST))

        # 年柱: 甲辰
        assert pillars.year.stem == TenStem.KINOE
        assert pillars.year.branch == TwelveBranch.TATSU

        # 月柱: 庚午
        assert pillars.month.stem == TenStem.KANOE
        assert pillars.month.branch == TwelveBranch.UMA
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_pillar_calculator.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/pillar_calculator.py
"""SanmeiCalendar — 三柱算出の統合エントリポイント."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo

from sanmei_core.calculators.day_pillar import day_pillar
from sanmei_core.calculators.month_pillar import month_pillar
from sanmei_core.calculators.year_pillar import year_pillar
from sanmei_core.domain.errors import DateOutOfRangeError
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.protocols.setsuiri import SetsuiriProvider

JST = timezone(timedelta(hours=9))

_MIN_YEAR = 1864
_MAX_YEAR = 2100


class SanmeiCalendar:
    """西暦日付から三柱干支を算出する統合エントリポイント.

    SetsuiriProvider を注入することで、流派ごとの節入り日データに対応。
    """

    def __init__(
        self,
        setsuiri_provider: SetsuiriProvider,
        *,
        tz: tzinfo | None = None,
    ) -> None:
        self._provider = setsuiri_provider
        self._tz = tz or JST

    def three_pillars(self, dt: datetime) -> ThreePillars:
        """三柱を一括算出."""
        self._validate_range(dt)
        return ThreePillars(
            year=self._year_pillar(dt),
            month=self._month_pillar(dt),
            day=self._day_pillar(dt),
        )

    def year_pillar(self, dt: datetime) -> Kanshi:
        """年柱を算出."""
        self._validate_range(dt)
        return self._year_pillar(dt)

    def month_pillar(self, dt: datetime) -> Kanshi:
        """月柱を算出."""
        self._validate_range(dt)
        return self._month_pillar(dt)

    def day_pillar(self, dt: datetime) -> Kanshi:
        """日柱を算出."""
        self._validate_range(dt)
        return self._day_pillar(dt)

    def _year_pillar(self, dt: datetime) -> Kanshi:
        local_dt = dt.astimezone(self._tz)
        risshun = self._provider.get_risshun(local_dt.year)
        return year_pillar(dt, risshun, tz=self._tz)

    def _month_pillar(self, dt: datetime) -> Kanshi:
        local_dt = dt.astimezone(self._tz)
        year_k = self._year_pillar(dt)

        # 年柱の年で節入り日を取得
        risshun = self._provider.get_risshun(local_dt.year)
        risshun_local = risshun.datetime_utc.astimezone(self._tz)

        if local_dt < risshun_local:
            # 立春前 → 前年の節入り日データを使用
            setsuiri_dates = self._provider.get_setsuiri_dates(local_dt.year - 1)
        else:
            setsuiri_dates = self._provider.get_setsuiri_dates(local_dt.year)

        return month_pillar(dt, setsuiri_dates, year_k.stem, tz=self._tz)

    def _day_pillar(self, dt: datetime) -> Kanshi:
        return day_pillar(dt, tz=self._tz)

    def _validate_range(self, dt: datetime) -> None:
        local_dt = dt.astimezone(self._tz)
        if local_dt.year < _MIN_YEAR or local_dt.year > _MAX_YEAR:
            raise DateOutOfRangeError(local_dt.year)
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_pillar_calculator.py -v`
Expected: All passed

**Step 5: Run lint and typecheck**

Run: `just lint && just typecheck`

**Step 6: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/pillar_calculator.py packages/sanmei-core/tests/unit/calculators/test_pillar_calculator.py
git commit -m "feat(sanmei-core): implement SanmeiCalendar facade for three pillar calculation"
```

---

### Task 11: パブリック API エクスポートと最終品質チェック

`__init__.py` のエクスポート整理と全品質ゲート通過。

**Files:**
- Modify: `packages/sanmei-core/src/sanmei_core/__init__.py`
- Modify: `packages/sanmei-core/src/sanmei_core/domain/__init__.py`
- Modify: `packages/sanmei-core/src/sanmei_core/calculators/__init__.py`
- Test: existing tests + coverage check

**Step 1: Update __init__.py files**

```python
# packages/sanmei-core/src/sanmei_core/__init__.py
"""算命学コアロジック - 純粋計算ライブラリ."""

from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.solar_longitude import MeeusSetsuiriProvider
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars

__all__ = [
    "Kanshi",
    "MeeusSetsuiriProvider",
    "SanmeiCalendar",
    "TenStem",
    "ThreePillars",
    "TwelveBranch",
]
```

```python
# packages/sanmei-core/src/sanmei_core/domain/__init__.py
"""ドメインモデル."""
```

```python
# packages/sanmei-core/src/sanmei_core/calculators/__init__.py
"""計算エンジン."""
```

**Step 2: Run full quality check**

Run: `just check`
Expected: lint PASS, typecheck PASS, test PASS

**Step 3: Check test coverage**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v --cov=sanmei_core --cov-report=term-missing`
Expected: 80%+ coverage

**Step 4: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/__init__.py packages/sanmei-core/src/sanmei_core/domain/__init__.py packages/sanmei-core/src/sanmei_core/calculators/__init__.py
git commit -m "feat(sanmei-core): export public API for calendar conversion module"
```
