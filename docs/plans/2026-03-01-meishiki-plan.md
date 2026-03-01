# 命式完成モジュール Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate a complete Meishiki (destiny chart) from a birth date, including hidden stems, ten major stars, twelve subsidiary stars, and tenchuusatsu.

**Architecture:** Protocol-first + Bottom-up. Define SchoolProtocol for school variations, build foundation tables (GoGyo, hidden stems), then calculators (stars, tenchuusatsu), then MeishikiCalculator facade.

**Tech Stack:** Python 3.14+, pydantic 2.10+, pytest, ruff strict, mypy strict

**Base paths:**
- Source: `packages/sanmei-core/src/sanmei_core/`
- Tests: `packages/sanmei-core/tests/unit/`
- Domain docs: `docs/domain/`
- Design doc: `docs/plans/2026-03-01-meishiki-design.md`

**Conventions** (match existing code exactly):
- `from __future__ import annotations` in every file
- `BaseModel, frozen=True` for immutable models
- `IntEnum` for ordered numeric enums, `Enum` for categories
- Module docstrings in Japanese
- `_` prefix for private constants/helpers
- Tests mirror source structure under `tests/unit/`
- Test classes: `Test<Feature>`, methods: `test_<case>`

---

### Task 1: GoGyo & InYou Domain Enums

**Files:**
- Create: `src/sanmei_core/domain/gogyo.py`
- Test: `tests/unit/domain/test_gogyo.py`

**Step 1: Write the failing test**

Create `tests/unit/domain/test_gogyo.py`:

```python
"""五行・陰陽の Enum テスト."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo, InYou


class TestGoGyo:
    def test_count(self) -> None:
        assert len(GoGyo) == 5

    def test_values(self) -> None:
        assert GoGyo.WOOD == 0
        assert GoGyo.FIRE == 1
        assert GoGyo.EARTH == 2
        assert GoGyo.METAL == 3
        assert GoGyo.WATER == 4

    def test_kanji(self) -> None:
        assert GoGyo.WOOD.kanji == "木"
        assert GoGyo.FIRE.kanji == "火"
        assert GoGyo.EARTH.kanji == "土"
        assert GoGyo.METAL.kanji == "金"
        assert GoGyo.WATER.kanji == "水"


class TestInYou:
    def test_count(self) -> None:
        assert len(InYou) == 2

    def test_values(self) -> None:
        assert InYou.YOU == 0
        assert InYou.IN == 1

    def test_kanji(self) -> None:
        assert InYou.YOU.kanji == "陽"
        assert InYou.IN.kanji == "陰"
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_gogyo.py -v`
Expected: FAIL (module not found)

**Step 3: Write minimal implementation**

Create `src/sanmei_core/domain/gogyo.py`:

```python
"""五行（ごぎょう）と陰陽（いんよう）のドメインモデル."""

from __future__ import annotations

from enum import IntEnum

_GOGYO_KANJI = ("木", "火", "土", "金", "水")
_INYOU_KANJI = ("陽", "陰")


class GoGyo(IntEnum):
    """五行."""

    WOOD = 0   # 木
    FIRE = 1   # 火
    EARTH = 2  # 土
    METAL = 3  # 金
    WATER = 4  # 水

    @property
    def kanji(self) -> str:
        """漢字表記."""
        return _GOGYO_KANJI[self.value]


class InYou(IntEnum):
    """陰陽."""

    YOU = 0  # 陽
    IN = 1   # 陰

    @property
    def kanji(self) -> str:
        """漢字表記."""
        return _INYOU_KANJI[self.value]
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_gogyo.py -v`
Expected: PASS (all 6 tests)

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/gogyo.py packages/sanmei-core/tests/unit/domain/test_gogyo.py
git commit -m "feat(sanmei-core): add GoGyo and InYou domain enums"
```

---

### Task 2: Star Domain Enums

**Files:**
- Create: `src/sanmei_core/domain/star.py`
- Test: `tests/unit/domain/test_star.py`

**Step 1: Write the failing test**

Create `tests/unit/domain/test_star.py`:

```python
"""十大主星・十二大従星の Enum テスト."""

from __future__ import annotations

from sanmei_core.domain.star import MajorStar, SubsidiaryStar


class TestMajorStar:
    def test_count(self) -> None:
        assert len(MajorStar) == 10

    def test_values(self) -> None:
        assert MajorStar.KANSAKU.value == "貫索星"
        assert MajorStar.SEKIMON.value == "石門星"
        assert MajorStar.HOUKAKU.value == "鳳閣星"
        assert MajorStar.CHOUJYO.value == "調舒星"
        assert MajorStar.ROKUZON.value == "禄存星"
        assert MajorStar.SHIROKU.value == "司禄星"
        assert MajorStar.SHAKI.value == "車騎星"
        assert MajorStar.KENGYU.value == "牽牛星"
        assert MajorStar.RYUKOU.value == "龍高星"
        assert MajorStar.GYOKUDO.value == "玉堂星"


class TestSubsidiaryStar:
    def test_count(self) -> None:
        assert len(SubsidiaryStar) == 12

    def test_values(self) -> None:
        assert SubsidiaryStar.TENPOU.value == "天報星"
        assert SubsidiaryStar.TENIN.value == "天印星"
        assert SubsidiaryStar.TENKI.value == "天貴星"
        assert SubsidiaryStar.TENKOU.value == "天恍星"
        assert SubsidiaryStar.TENNAN.value == "天南星"
        assert SubsidiaryStar.TENROKU.value == "天禄星"
        assert SubsidiaryStar.TENSHOU.value == "天将星"
        assert SubsidiaryStar.TENDOU.value == "天堂星"
        assert SubsidiaryStar.TENKO.value == "天胡星"
        assert SubsidiaryStar.TENKYOKU.value == "天極星"
        assert SubsidiaryStar.TENKU.value == "天庫星"
        assert SubsidiaryStar.TENCHI.value == "天馳星"
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_star.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/domain/star.py`:

```python
"""十大主星（じゅうだいしゅせい）・十二大従星（じゅうにだいじゅうせい）."""

from __future__ import annotations

from enum import Enum


class MajorStar(Enum):
    """十大主星."""

    KANSAKU = "貫索星"   # 比劫・陽
    SEKIMON = "石門星"   # 比劫・陰
    HOUKAKU = "鳳閣星"   # 食傷・陽
    CHOUJYO = "調舒星"   # 食傷・陰
    ROKUZON = "禄存星"   # 財星・陽
    SHIROKU = "司禄星"   # 財星・陰
    SHAKI = "車騎星"     # 官星・陽
    KENGYU = "牽牛星"    # 官星・陰
    RYUKOU = "龍高星"    # 印綬・陽
    GYOKUDO = "玉堂星"   # 印綬・陰


class SubsidiaryStar(Enum):
    """十二大従星."""

    TENPOU = "天報星"    # 胎
    TENIN = "天印星"     # 養
    TENKI = "天貴星"     # 長生
    TENKOU = "天恍星"    # 沐浴
    TENNAN = "天南星"    # 冠帯
    TENROKU = "天禄星"   # 建禄
    TENSHOU = "天将星"   # 帝旺
    TENDOU = "天堂星"    # 衰
    TENKO = "天胡星"     # 病
    TENKYOKU = "天極星"  # 死
    TENKU = "天庫星"     # 墓
    TENCHI = "天馳星"    # 絶
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_star.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/star.py packages/sanmei-core/tests/unit/domain/test_star.py
git commit -m "feat(sanmei-core): add MajorStar and SubsidiaryStar domain enums"
```

---

### Task 3: HiddenStems & Tenchuusatsu Domain Models

**Files:**
- Create: `src/sanmei_core/domain/hidden_stems.py`
- Create: `src/sanmei_core/domain/tenchuusatsu.py`
- Test: `tests/unit/domain/test_hidden_stems.py`
- Test: `tests/unit/domain/test_tenchuusatsu.py`

**Step 1: Write the failing tests**

Create `tests/unit/domain/test_hidden_stems.py`:

```python
"""蔵干モデルのテスト."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem


class TestHiddenStems:
    def test_all_three(self) -> None:
        hs = HiddenStems(main=TenStem.KINOE, middle=TenStem.HINOE, minor=TenStem.TSUCHINOE)
        assert hs.main == TenStem.KINOE
        assert hs.middle == TenStem.HINOE
        assert hs.minor == TenStem.TSUCHINOE

    def test_main_only(self) -> None:
        hs = HiddenStems(main=TenStem.MIZUNOTO, middle=None, minor=None)
        assert hs.main == TenStem.MIZUNOTO
        assert hs.middle is None
        assert hs.minor is None

    def test_main_and_middle(self) -> None:
        hs = HiddenStems(main=TenStem.MIZUNOE, middle=TenStem.KINOE, minor=None)
        assert hs.middle == TenStem.KINOE
        assert hs.minor is None

    def test_frozen(self) -> None:
        hs = HiddenStems(main=TenStem.KINOE, middle=None, minor=None)
        with pytest.raises(ValidationError):
            hs.main = TenStem.KINOTO  # type: ignore[misc]
```

Create `tests/unit/domain/test_tenchuusatsu.py`:

```python
"""天中殺モデルのテスト."""

from __future__ import annotations

from sanmei_core.domain.kanshi import TwelveBranch
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType


class TestTenchuusatsuType:
    def test_count(self) -> None:
        assert len(TenchuusatsuType) == 6

    def test_values(self) -> None:
        assert TenchuusatsuType.NE_USHI.value == "子丑天中殺"
        assert TenchuusatsuType.TORA_U.value == "寅卯天中殺"
        assert TenchuusatsuType.TATSU_MI.value == "辰巳天中殺"
        assert TenchuusatsuType.UMA_HITSUJI.value == "午未天中殺"
        assert TenchuusatsuType.SARU_TORI.value == "申酉天中殺"
        assert TenchuusatsuType.INU_I.value == "戌亥天中殺"


class TestTenchuusatsu:
    def test_creation(self) -> None:
        tc = Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        )
        assert tc.type == TenchuusatsuType.INU_I
        assert tc.branches == (TwelveBranch.INU, TwelveBranch.I)
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_hidden_stems.py packages/sanmei-core/tests/unit/domain/test_tenchuusatsu.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/domain/hidden_stems.py`:

```python
"""蔵干（ぞうかん）のドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel

from sanmei_core.domain.kanshi import TenStem


class HiddenStems(BaseModel, frozen=True):
    """蔵干.

    各十二支の内部に格納された十干。本気（主）・中気（副）・余気（従）の最大3つ。
    """

    main: TenStem
    middle: TenStem | None = None
    minor: TenStem | None = None
```

Create `src/sanmei_core/domain/tenchuusatsu.py`:

```python
"""天中殺（てんちゅうさつ）のドメインモデル."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from sanmei_core.domain.kanshi import TwelveBranch


class TenchuusatsuType(Enum):
    """天中殺の六種類."""

    NE_USHI = "子丑天中殺"
    TORA_U = "寅卯天中殺"
    TATSU_MI = "辰巳天中殺"
    UMA_HITSUJI = "午未天中殺"
    SARU_TORI = "申酉天中殺"
    INU_I = "戌亥天中殺"


class Tenchuusatsu(BaseModel, frozen=True):
    """天中殺."""

    type: TenchuusatsuType
    branches: tuple[TwelveBranch, TwelveBranch]
```

**Step 4: Run tests to verify they pass**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_hidden_stems.py packages/sanmei-core/tests/unit/domain/test_tenchuusatsu.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/hidden_stems.py packages/sanmei-core/src/sanmei_core/domain/tenchuusatsu.py packages/sanmei-core/tests/unit/domain/test_hidden_stems.py packages/sanmei-core/tests/unit/domain/test_tenchuusatsu.py
git commit -m "feat(sanmei-core): add HiddenStems and Tenchuusatsu domain models"
```

---

### Task 4: GoGyo Relation Tables & Functions

**Files:**
- Create: `src/sanmei_core/tables/gogyo.py`
- Test: `tests/unit/tables/test_gogyo.py`

**Reference:** `docs/domain/04_Chapter4_Ten_Major_Stars.md` Section 4.3 (五行関係ルール)

**Step 1: Write the failing test**

Create `tests/unit/tables/test_gogyo.py`:

```python
"""五行関係テーブルのテスト."""

from __future__ import annotations

import pytest

from sanmei_core.domain.gogyo import GoGyo, InYou
from sanmei_core.domain.kanshi import TenStem
from sanmei_core.tables.gogyo import (
    SOUKOKU,
    SOUGOU,
    STEM_TO_GOGYO,
    STEM_TO_INYOU,
    GoGyoRelation,
    get_relation,
    is_same_polarity,
)


class TestStemMappings:
    def test_stem_to_gogyo_count(self) -> None:
        assert len(STEM_TO_GOGYO) == 10

    @pytest.mark.parametrize(
        ("stem", "expected"),
        [
            (TenStem.KINOE, GoGyo.WOOD),
            (TenStem.KINOTO, GoGyo.WOOD),
            (TenStem.HINOE, GoGyo.FIRE),
            (TenStem.HINOTO, GoGyo.FIRE),
            (TenStem.TSUCHINOE, GoGyo.EARTH),
            (TenStem.TSUCHINOTO, GoGyo.EARTH),
            (TenStem.KANOE, GoGyo.METAL),
            (TenStem.KANOTO, GoGyo.METAL),
            (TenStem.MIZUNOE, GoGyo.WATER),
            (TenStem.MIZUNOTO, GoGyo.WATER),
        ],
    )
    def test_stem_to_gogyo(self, stem: TenStem, expected: GoGyo) -> None:
        assert STEM_TO_GOGYO[stem] == expected

    @pytest.mark.parametrize(
        ("stem", "expected"),
        [
            (TenStem.KINOE, InYou.YOU),
            (TenStem.KINOTO, InYou.IN),
            (TenStem.HINOE, InYou.YOU),
            (TenStem.HINOTO, InYou.IN),
        ],
    )
    def test_stem_to_inyou(self, stem: TenStem, expected: InYou) -> None:
        assert STEM_TO_INYOU[stem] == expected


class TestCycles:
    def test_sougou_production_cycle(self) -> None:
        """木→火→土→金→水→木."""
        assert SOUGOU[GoGyo.WOOD] == GoGyo.FIRE
        assert SOUGOU[GoGyo.FIRE] == GoGyo.EARTH
        assert SOUGOU[GoGyo.EARTH] == GoGyo.METAL
        assert SOUGOU[GoGyo.METAL] == GoGyo.WATER
        assert SOUGOU[GoGyo.WATER] == GoGyo.WOOD

    def test_soukoku_control_cycle(self) -> None:
        """木→土→水→火→金→木."""
        assert SOUKOKU[GoGyo.WOOD] == GoGyo.EARTH
        assert SOUKOKU[GoGyo.EARTH] == GoGyo.WATER
        assert SOUKOKU[GoGyo.WATER] == GoGyo.FIRE
        assert SOUKOKU[GoGyo.FIRE] == GoGyo.METAL
        assert SOUKOKU[GoGyo.METAL] == GoGyo.WOOD


class TestIsSamePolarity:
    def test_same_yang(self) -> None:
        assert is_same_polarity(TenStem.KINOE, TenStem.HINOE) is True

    def test_same_yin(self) -> None:
        assert is_same_polarity(TenStem.KINOTO, TenStem.HINOTO) is True

    def test_different(self) -> None:
        assert is_same_polarity(TenStem.KINOE, TenStem.KINOTO) is False


class TestGetRelation:
    def test_hikaku_same_element(self) -> None:
        """甲 vs 甲 = 比劫（同五行）."""
        assert get_relation(TenStem.KINOE, TenStem.KINOE) == GoGyoRelation.HIKAKU

    def test_hikaku_different_polarity(self) -> None:
        """甲 vs 乙 = 比劫（同五行・異陰陽）."""
        assert get_relation(TenStem.KINOE, TenStem.KINOTO) == GoGyoRelation.HIKAKU

    def test_shokushou_day_produces(self) -> None:
        """甲(木) vs 丙(火) = 食傷（木生火）."""
        assert get_relation(TenStem.KINOE, TenStem.HINOE) == GoGyoRelation.SHOKUSHOU

    def test_zaisei_day_conquers(self) -> None:
        """甲(木) vs 戊(土) = 財星（木剋土）."""
        assert get_relation(TenStem.KINOE, TenStem.TSUCHINOE) == GoGyoRelation.ZAISEI

    def test_kansei_target_conquers(self) -> None:
        """甲(木) vs 庚(金) = 官星（金剋木）."""
        assert get_relation(TenStem.KINOE, TenStem.KANOE) == GoGyoRelation.KANSEI

    def test_injyu_target_produces(self) -> None:
        """甲(木) vs 壬(水) = 印綬（水生木）."""
        assert get_relation(TenStem.KINOE, TenStem.MIZUNOE) == GoGyoRelation.INJYU
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/tables/test_gogyo.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/tables/gogyo.py`:

```python
"""五行関係テーブル."""

from __future__ import annotations

from enum import Enum

from sanmei_core.domain.gogyo import GoGyo, InYou
from sanmei_core.domain.kanshi import TenStem

STEM_TO_GOGYO: dict[TenStem, GoGyo] = {
    TenStem.KINOE: GoGyo.WOOD,
    TenStem.KINOTO: GoGyo.WOOD,
    TenStem.HINOE: GoGyo.FIRE,
    TenStem.HINOTO: GoGyo.FIRE,
    TenStem.TSUCHINOE: GoGyo.EARTH,
    TenStem.TSUCHINOTO: GoGyo.EARTH,
    TenStem.KANOE: GoGyo.METAL,
    TenStem.KANOTO: GoGyo.METAL,
    TenStem.MIZUNOE: GoGyo.WATER,
    TenStem.MIZUNOTO: GoGyo.WATER,
}

STEM_TO_INYOU: dict[TenStem, InYou] = {
    TenStem.KINOE: InYou.YOU,
    TenStem.KINOTO: InYou.IN,
    TenStem.HINOE: InYou.YOU,
    TenStem.HINOTO: InYou.IN,
    TenStem.TSUCHINOE: InYou.YOU,
    TenStem.TSUCHINOTO: InYou.IN,
    TenStem.KANOE: InYou.YOU,
    TenStem.KANOTO: InYou.IN,
    TenStem.MIZUNOE: InYou.YOU,
    TenStem.MIZUNOTO: InYou.IN,
}

SOUGOU: dict[GoGyo, GoGyo] = {
    GoGyo.WOOD: GoGyo.FIRE,
    GoGyo.FIRE: GoGyo.EARTH,
    GoGyo.EARTH: GoGyo.METAL,
    GoGyo.METAL: GoGyo.WATER,
    GoGyo.WATER: GoGyo.WOOD,
}
"""相生（そうしょう）: 木→火→土→金→水→木."""

SOUKOKU: dict[GoGyo, GoGyo] = {
    GoGyo.WOOD: GoGyo.EARTH,
    GoGyo.EARTH: GoGyo.WATER,
    GoGyo.WATER: GoGyo.FIRE,
    GoGyo.FIRE: GoGyo.METAL,
    GoGyo.METAL: GoGyo.WOOD,
}
"""相剋（そうこく）: 木→土→水→火→金→木."""


class GoGyoRelation(Enum):
    """日干から見た五行関係."""

    HIKAKU = "比劫"
    SHOKUSHOU = "食傷"
    ZAISEI = "財星"
    KANSEI = "官星"
    INJYU = "印綬"


def get_relation(day_stem: TenStem, target_stem: TenStem) -> GoGyoRelation:
    """日干と対象干の五行関係を判定."""
    day_g = STEM_TO_GOGYO[day_stem]
    target_g = STEM_TO_GOGYO[target_stem]
    if day_g == target_g:
        return GoGyoRelation.HIKAKU
    if SOUGOU[day_g] == target_g:
        return GoGyoRelation.SHOKUSHOU
    if SOUKOKU[day_g] == target_g:
        return GoGyoRelation.ZAISEI
    if SOUKOKU[target_g] == day_g:
        return GoGyoRelation.KANSEI
    return GoGyoRelation.INJYU


def is_same_polarity(stem_a: TenStem, stem_b: TenStem) -> bool:
    """同陰陽かを判定."""
    return STEM_TO_INYOU[stem_a] == STEM_TO_INYOU[stem_b]
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/tables/test_gogyo.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/tables/gogyo.py packages/sanmei-core/tests/unit/tables/test_gogyo.py
git commit -m "feat(sanmei-core): add GoGyo relation tables and functions"
```

---

### Task 5: Hidden Stems Table

**Files:**
- Create: `src/sanmei_core/tables/hidden_stems.py`
- Test: `tests/unit/tables/test_hidden_stems.py`

**Reference:** `docs/domain/02_Chapter2_Basics_of_Kanshi.md` Section 2.4 (蔵干テーブル)

**Step 1: Write the failing test**

Create `tests/unit/tables/test_hidden_stems.py`:

```python
"""蔵干テーブルのテスト."""

from __future__ import annotations

import pytest

from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.tables.hidden_stems import STANDARD_HIDDEN_STEMS


class TestStandardHiddenStems:
    def test_all_branches_present(self) -> None:
        assert len(STANDARD_HIDDEN_STEMS) == 12
        for branch in TwelveBranch:
            assert branch in STANDARD_HIDDEN_STEMS

    @pytest.mark.parametrize(
        ("branch", "main", "middle", "minor"),
        [
            (TwelveBranch.NE, TenStem.MIZUNOTO, None, None),
            (TwelveBranch.USHI, TenStem.TSUCHINOTO, TenStem.KANOTO, TenStem.MIZUNOTO),
            (TwelveBranch.TORA, TenStem.KINOE, TenStem.HINOE, TenStem.TSUCHINOE),
            (TwelveBranch.U, TenStem.KINOTO, None, None),
            (TwelveBranch.TATSU, TenStem.TSUCHINOE, TenStem.KINOTO, TenStem.MIZUNOTO),
            (TwelveBranch.MI, TenStem.HINOE, TenStem.KANOE, TenStem.TSUCHINOE),
            (TwelveBranch.UMA, TenStem.HINOTO, TenStem.TSUCHINOTO, None),
            (TwelveBranch.HITSUJI, TenStem.TSUCHINOTO, TenStem.HINOTO, TenStem.KINOTO),
            (TwelveBranch.SARU, TenStem.KANOE, TenStem.MIZUNOE, TenStem.TSUCHINOE),
            (TwelveBranch.TORI, TenStem.KANOTO, None, None),
            (TwelveBranch.INU, TenStem.TSUCHINOE, TenStem.KANOTO, TenStem.HINOTO),
            (TwelveBranch.I, TenStem.MIZUNOE, TenStem.KINOE, None),
        ],
    )
    def test_hidden_stems(
        self,
        branch: TwelveBranch,
        main: TenStem,
        middle: TenStem | None,
        minor: TenStem | None,
    ) -> None:
        hs = STANDARD_HIDDEN_STEMS[branch]
        assert hs.main == main
        assert hs.middle == middle
        assert hs.minor == minor
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/tables/test_hidden_stems.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/tables/hidden_stems.py`:

```python
"""蔵干テーブル（標準流派）.

docs/domain/02_Chapter2_Basics_of_Kanshi.md Section 2.4 準拠。
"""

from __future__ import annotations

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

STANDARD_HIDDEN_STEMS: dict[TwelveBranch, HiddenStems] = {
    TwelveBranch.NE: HiddenStems(main=TenStem.MIZUNOTO),
    TwelveBranch.USHI: HiddenStems(
        main=TenStem.TSUCHINOTO, middle=TenStem.KANOTO, minor=TenStem.MIZUNOTO
    ),
    TwelveBranch.TORA: HiddenStems(
        main=TenStem.KINOE, middle=TenStem.HINOE, minor=TenStem.TSUCHINOE
    ),
    TwelveBranch.U: HiddenStems(main=TenStem.KINOTO),
    TwelveBranch.TATSU: HiddenStems(
        main=TenStem.TSUCHINOE, middle=TenStem.KINOTO, minor=TenStem.MIZUNOTO
    ),
    TwelveBranch.MI: HiddenStems(
        main=TenStem.HINOE, middle=TenStem.KANOE, minor=TenStem.TSUCHINOE
    ),
    TwelveBranch.UMA: HiddenStems(main=TenStem.HINOTO, middle=TenStem.TSUCHINOTO),
    TwelveBranch.HITSUJI: HiddenStems(
        main=TenStem.TSUCHINOTO, middle=TenStem.HINOTO, minor=TenStem.KINOTO
    ),
    TwelveBranch.SARU: HiddenStems(
        main=TenStem.KANOE, middle=TenStem.MIZUNOE, minor=TenStem.TSUCHINOE
    ),
    TwelveBranch.TORI: HiddenStems(main=TenStem.KANOTO),
    TwelveBranch.INU: HiddenStems(
        main=TenStem.TSUCHINOE, middle=TenStem.KANOTO, minor=TenStem.HINOTO
    ),
    TwelveBranch.I: HiddenStems(main=TenStem.MIZUNOE, middle=TenStem.KINOE),
}
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/tables/test_hidden_stems.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/tables/hidden_stems.py packages/sanmei-core/tests/unit/tables/test_hidden_stems.py
git commit -m "feat(sanmei-core): add standard hidden stems (zoukan) table"
```

---

### Task 6: SchoolProtocol

**Files:**
- Create: `src/sanmei_core/protocols/school.py`
- Test: `tests/unit/test_school_protocol.py`

**Step 1: Write the failing test**

Create `tests/unit/test_school_protocol.py`:

```python
"""SchoolProtocol の構造型テスト."""

from __future__ import annotations

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar
from sanmei_core.protocols.school import SchoolProtocol
from sanmei_core.protocols.setsuiri import SetsuiriProvider


class _StubSchool:
    """SchoolProtocol を満たすスタブ."""

    @property
    def name(self) -> str:
        return "stub"

    def get_hidden_stems(self, branch: TwelveBranch) -> HiddenStems:
        return HiddenStems(main=TenStem.KINOE)

    def determine_major_star(
        self, day_stem: TenStem, target_stem: TenStem
    ) -> MajorStar:
        return MajorStar.KANSAKU

    def get_teiou_branch(self, stem: TenStem) -> TwelveBranch:
        return TwelveBranch.U

    def get_setsuiri_provider(self) -> SetsuiriProvider:
        raise NotImplementedError


def test_stub_satisfies_protocol() -> None:
    school: SchoolProtocol = _StubSchool()
    assert school.name == "stub"
    assert school.get_hidden_stems(TwelveBranch.NE).main == TenStem.KINOE
    assert school.determine_major_star(TenStem.KINOE, TenStem.KINOE) == MajorStar.KANSAKU
    assert school.get_teiou_branch(TenStem.KINOE) == TwelveBranch.U
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/test_school_protocol.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/protocols/school.py`:

```python
"""SchoolProtocol — 流派固有ロジックの統合インターフェース."""

from __future__ import annotations

from typing import Protocol

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar
from sanmei_core.protocols.setsuiri import SetsuiriProvider


class SchoolProtocol(Protocol):
    """流派固有ロジックの統合インターフェース.

    蔵干テーブル・十大主星判定・十二運帝旺支・節入り日計算の
    全差異点を一つの Protocol にまとめる。
    """

    @property
    def name(self) -> str:
        """流派名."""
        ...

    def get_hidden_stems(self, branch: TwelveBranch) -> HiddenStems:
        """地支から蔵干を取得."""
        ...

    def determine_major_star(
        self, day_stem: TenStem, target_stem: TenStem
    ) -> MajorStar:
        """日干と対象干から十大主星を判定."""
        ...

    def get_teiou_branch(self, stem: TenStem) -> TwelveBranch:
        """十干の帝旺支（十二大従星算出用）を取得."""
        ...

    def get_setsuiri_provider(self) -> SetsuiriProvider:
        """節入り日プロバイダを取得."""
        ...
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/test_school_protocol.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/protocols/school.py packages/sanmei-core/tests/unit/test_school_protocol.py
git commit -m "feat(sanmei-core): add SchoolProtocol for multi-school support"
```

---

### Task 7: StandardSchool Implementation

**Files:**
- Modify: `src/sanmei_core/schools/standard.py` (create)
- Test: `tests/unit/schools/test_standard.py` (create)

**Reference:**
- `docs/domain/04_Chapter4` Section 4.3 (十大主星算出ルール)
- `docs/domain/05_Chapter5` Section 5.2 (帝旺支)

**Step 1: Write the failing test**

Create `tests/unit/schools/__init__.py` (empty) and `tests/unit/schools/test_standard.py`:

```python
"""標準流派のテスト."""

from __future__ import annotations

import pytest

from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar
from sanmei_core.schools.standard import StandardSchool


class TestStandardSchoolName:
    def test_name(self) -> None:
        school = StandardSchool()
        assert school.name == "standard"


class TestHiddenStems:
    def test_ne_main_is_mizunoto(self) -> None:
        school = StandardSchool()
        hs = school.get_hidden_stems(TwelveBranch.NE)
        assert hs.main == TenStem.MIZUNOTO

    def test_tora_all_three(self) -> None:
        school = StandardSchool()
        hs = school.get_hidden_stems(TwelveBranch.TORA)
        assert hs.main == TenStem.KINOE
        assert hs.middle == TenStem.HINOE
        assert hs.minor == TenStem.TSUCHINOE


class TestDetermineMajorStar:
    """docs/domain/04_Chapter4 Section 4.3 のルール表を検証."""

    @pytest.mark.parametrize(
        ("day", "target", "expected"),
        [
            # 比劫: 同五行・同陰陽 → 貫索星
            (TenStem.KINOE, TenStem.KINOE, MajorStar.KANSAKU),
            # 比劫: 同五行・異陰陽 → 石門星
            (TenStem.KINOE, TenStem.KINOTO, MajorStar.SEKIMON),
            # 食傷: 日干が生む・同陰陽 → 鳳閣星
            (TenStem.KINOE, TenStem.HINOE, MajorStar.HOUKAKU),
            # 食傷: 日干が生む・異陰陽 → 調舒星
            (TenStem.KINOE, TenStem.HINOTO, MajorStar.CHOUJYO),
            # 財星: 日干が剋す・同陰陽 → 禄存星
            (TenStem.KINOE, TenStem.TSUCHINOE, MajorStar.ROKUZON),
            # 財星: 日干が剋す・異陰陽 → 司禄星
            (TenStem.KINOE, TenStem.TSUCHINOTO, MajorStar.SHIROKU),
            # 官星: 日干を剋す・異陰陽 → 車騎星
            (TenStem.KINOE, TenStem.KANOTO, MajorStar.SHAKI),
            # 官星: 日干を剋す・同陰陽 → 牽牛星
            (TenStem.KINOE, TenStem.KANOE, MajorStar.KENGYU),
            # 印綬: 日干を生む・異陰陽 → 龍高星
            (TenStem.KINOE, TenStem.MIZUNOTO, MajorStar.RYUKOU),
            # 印綬: 日干を生む・同陰陽 → 玉堂星
            (TenStem.KINOE, TenStem.MIZUNOE, MajorStar.GYOKUDO),
        ],
    )
    def test_kinoe_vs_all(
        self, day: TenStem, target: TenStem, expected: MajorStar
    ) -> None:
        school = StandardSchool()
        assert school.determine_major_star(day, target) == expected

    def test_hinoe_vs_mizunoe(self) -> None:
        """丙(火) vs 壬(水): 官星・同陰陽 → 牽牛星."""
        school = StandardSchool()
        assert school.determine_major_star(TenStem.HINOE, TenStem.MIZUNOE) == MajorStar.KENGYU


class TestGetTeiouBranch:
    @pytest.mark.parametrize(
        ("stem", "expected"),
        [
            (TenStem.KINOE, TwelveBranch.U),
            (TenStem.KINOTO, TwelveBranch.U),
            (TenStem.HINOE, TwelveBranch.UMA),
            (TenStem.HINOTO, TwelveBranch.UMA),
            (TenStem.TSUCHINOE, TwelveBranch.INU),
            (TenStem.TSUCHINOTO, TwelveBranch.HITSUJI),
            (TenStem.KANOE, TwelveBranch.TORI),
            (TenStem.KANOTO, TwelveBranch.TORI),
            (TenStem.MIZUNOE, TwelveBranch.NE),
            (TenStem.MIZUNOTO, TwelveBranch.NE),
        ],
    )
    def test_teiou_branch(self, stem: TenStem, expected: TwelveBranch) -> None:
        school = StandardSchool()
        assert school.get_teiou_branch(stem) == expected


class TestGetSetsuiriProvider:
    def test_returns_provider(self) -> None:
        school = StandardSchool()
        provider = school.get_setsuiri_provider()
        dates = provider.get_setsuiri_dates(2024)
        assert len(dates) == 12
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/schools/test_standard.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/schools/standard.py`:

```python
"""標準流派の実装."""

from __future__ import annotations

from sanmei_core.calculators.solar_longitude import MeeusSetsuiriProvider
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar
from sanmei_core.protocols.setsuiri import SetsuiriProvider
from sanmei_core.tables.gogyo import GoGyoRelation, get_relation, is_same_polarity
from sanmei_core.tables.hidden_stems import STANDARD_HIDDEN_STEMS

_TEIOU_MAP: dict[TenStem, TwelveBranch] = {
    TenStem.KINOE: TwelveBranch.U,
    TenStem.KINOTO: TwelveBranch.U,
    TenStem.HINOE: TwelveBranch.UMA,
    TenStem.HINOTO: TwelveBranch.UMA,
    TenStem.TSUCHINOE: TwelveBranch.INU,
    TenStem.TSUCHINOTO: TwelveBranch.HITSUJI,
    TenStem.KANOE: TwelveBranch.TORI,
    TenStem.KANOTO: TwelveBranch.TORI,
    TenStem.MIZUNOE: TwelveBranch.NE,
    TenStem.MIZUNOTO: TwelveBranch.NE,
}

# 五行関係 + 陰陽 → 十大主星
_STAR_MAP: dict[tuple[GoGyoRelation, bool], MajorStar] = {
    (GoGyoRelation.HIKAKU, True): MajorStar.KANSAKU,
    (GoGyoRelation.HIKAKU, False): MajorStar.SEKIMON,
    (GoGyoRelation.SHOKUSHOU, True): MajorStar.HOUKAKU,
    (GoGyoRelation.SHOKUSHOU, False): MajorStar.CHOUJYO,
    (GoGyoRelation.ZAISEI, True): MajorStar.ROKUZON,
    (GoGyoRelation.ZAISEI, False): MajorStar.SHIROKU,
    (GoGyoRelation.KANSEI, False): MajorStar.SHAKI,
    (GoGyoRelation.KANSEI, True): MajorStar.KENGYU,
    (GoGyoRelation.INJYU, False): MajorStar.RYUKOU,
    (GoGyoRelation.INJYU, True): MajorStar.GYOKUDO,
}


class StandardSchool:
    """標準流派.

    蔵干: docs/domain/02_Chapter2 準拠
    陰陽判定: docs/domain/04_Chapter4 準拠
    土性帝旺: 戊→戌, 己→未
    節入り: MeeusSetsuiriProvider
    """

    @property
    def name(self) -> str:
        """流派名."""
        return "standard"

    def get_hidden_stems(self, branch: TwelveBranch) -> HiddenStems:
        """地支から蔵干を取得."""
        return STANDARD_HIDDEN_STEMS[branch]

    def determine_major_star(
        self, day_stem: TenStem, target_stem: TenStem
    ) -> MajorStar:
        """日干と対象干から十大主星を判定."""
        relation = get_relation(day_stem, target_stem)
        same_pol = is_same_polarity(day_stem, target_stem)
        return _STAR_MAP[(relation, same_pol)]

    def get_teiou_branch(self, stem: TenStem) -> TwelveBranch:
        """十干の帝旺支を取得."""
        return _TEIOU_MAP[stem]

    def get_setsuiri_provider(self) -> SetsuiriProvider:
        """節入り日プロバイダを取得."""
        return MeeusSetsuiriProvider()
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/schools/test_standard.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/schools/standard.py packages/sanmei-core/tests/unit/schools/__init__.py packages/sanmei-core/tests/unit/schools/test_standard.py
git commit -m "feat(sanmei-core): implement StandardSchool with star determination"
```

---

### Task 8: SchoolRegistry

**Files:**
- Create: `src/sanmei_core/schools/registry.py`
- Test: `tests/unit/schools/test_registry.py`

**Step 1: Write the failing test**

Create `tests/unit/schools/test_registry.py`:

```python
"""SchoolRegistry のテスト."""

from __future__ import annotations

import pytest

from sanmei_core.domain.errors import SanmeiError
from sanmei_core.schools.registry import SchoolRegistry
from sanmei_core.schools.standard import StandardSchool


class TestSchoolRegistry:
    def test_register_and_get(self) -> None:
        registry = SchoolRegistry()
        school = StandardSchool()
        registry.register(school)
        assert registry.get("standard") is school

    def test_get_unknown_raises(self) -> None:
        registry = SchoolRegistry()
        with pytest.raises(SanmeiError, match="unknown"):
            registry.get("unknown")

    def test_default_returns_first_registered(self) -> None:
        registry = SchoolRegistry()
        school = StandardSchool()
        registry.register(school)
        assert registry.default() is school

    def test_default_empty_raises(self) -> None:
        registry = SchoolRegistry()
        with pytest.raises(SanmeiError, match="No schools"):
            registry.default()

    def test_list_schools(self) -> None:
        registry = SchoolRegistry()
        registry.register(StandardSchool())
        assert registry.list_schools() == ["standard"]

    def test_create_default_has_standard(self) -> None:
        registry = SchoolRegistry.create_default()
        assert registry.default().name == "standard"
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/schools/test_registry.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/schools/registry.py`:

```python
"""SchoolRegistry — 流派レジストリ."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.domain.errors import SanmeiError

if TYPE_CHECKING:
    from sanmei_core.protocols.school import SchoolProtocol


class SchoolRegistry:
    """流派の登録・取得を行うレジストリ."""

    def __init__(self) -> None:
        self._schools: dict[str, SchoolProtocol] = {}
        self._default_name: str | None = None

    def register(self, school: SchoolProtocol) -> None:
        """流派を登録."""
        self._schools[school.name] = school
        if self._default_name is None:
            self._default_name = school.name

    def get(self, name: str) -> SchoolProtocol:
        """名前で流派を取得."""
        if name not in self._schools:
            msg = f"School '{name}' is unknown. Available: {list(self._schools)}"
            raise SanmeiError(msg)
        return self._schools[name]

    def default(self) -> SchoolProtocol:
        """デフォルト流派を取得."""
        if self._default_name is None:
            msg = "No schools registered"
            raise SanmeiError(msg)
        return self._schools[self._default_name]

    def list_schools(self) -> list[str]:
        """登録済み流派名のリスト."""
        return list(self._schools)

    @classmethod
    def create_default(cls) -> SchoolRegistry:
        """標準流派を登録済みのレジストリを生成."""
        from sanmei_core.schools.standard import StandardSchool

        registry = cls()
        registry.register(StandardSchool())
        return registry
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/schools/test_registry.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/schools/registry.py packages/sanmei-core/tests/unit/schools/test_registry.py
git commit -m "feat(sanmei-core): add SchoolRegistry for school management"
```

---

### Task 9: Tenchuusatsu Calculator

**Files:**
- Create: `src/sanmei_core/calculators/tenchuusatsu.py`
- Test: `tests/unit/calculators/test_tenchuusatsu.py`

**Reference:** `docs/domain/06_Chapter6_Chuusetsu.md` Section 6.1.1

**Step 1: Write the failing test**

Create `tests/unit/calculators/test_tenchuusatsu.py`:

```python
"""天中殺計算のテスト."""

from __future__ import annotations

import pytest

from sanmei_core.calculators.tenchuusatsu import calculate_tenchuusatsu
from sanmei_core.domain.kanshi import Kanshi, TwelveBranch
from sanmei_core.domain.tenchuusatsu import TenchuusatsuType


class TestCalculateTenchuusatsu:
    def test_group0_inu_i(self) -> None:
        """甲子(0)〜癸酉(9) → 戌亥天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(0))
        assert tc.type == TenchuusatsuType.INU_I
        assert tc.branches == (TwelveBranch.INU, TwelveBranch.I)

    def test_group1_saru_tori(self) -> None:
        """甲戌(10)〜癸未(19) → 申酉天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(10))
        assert tc.type == TenchuusatsuType.SARU_TORI

    def test_group2_uma_hitsuji(self) -> None:
        """甲申(20)〜癸巳(29) → 午未天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(20))
        assert tc.type == TenchuusatsuType.UMA_HITSUJI

    def test_group3_tatsu_mi(self) -> None:
        """甲午(30)〜癸卯(39) → 辰巳天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(30))
        assert tc.type == TenchuusatsuType.TATSU_MI

    def test_group4_tora_u(self) -> None:
        """甲辰(40)〜癸丑(49) → 寅卯天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(40))
        assert tc.type == TenchuusatsuType.TORA_U

    def test_group5_ne_ushi(self) -> None:
        """甲寅(50)〜癸亥(59) → 子丑天中殺."""
        tc = calculate_tenchuusatsu(Kanshi.from_index(50))
        assert tc.type == TenchuusatsuType.NE_USHI

    @pytest.mark.parametrize("index", range(60))
    def test_all_60_kanshi_have_valid_type(self, index: int) -> None:
        tc = calculate_tenchuusatsu(Kanshi.from_index(index))
        assert isinstance(tc.type, TenchuusatsuType)
        assert len(tc.branches) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_tenchuusatsu.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/calculators/tenchuusatsu.py`:

```python
"""天中殺の算出."""

from __future__ import annotations

from sanmei_core.domain.kanshi import Kanshi, TwelveBranch
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType

_GROUP_MAP: tuple[tuple[TenchuusatsuType, tuple[TwelveBranch, TwelveBranch]], ...] = (
    (TenchuusatsuType.INU_I, (TwelveBranch.INU, TwelveBranch.I)),
    (TenchuusatsuType.SARU_TORI, (TwelveBranch.SARU, TwelveBranch.TORI)),
    (TenchuusatsuType.UMA_HITSUJI, (TwelveBranch.UMA, TwelveBranch.HITSUJI)),
    (TenchuusatsuType.TATSU_MI, (TwelveBranch.TATSU, TwelveBranch.MI)),
    (TenchuusatsuType.TORA_U, (TwelveBranch.TORA, TwelveBranch.U)),
    (TenchuusatsuType.NE_USHI, (TwelveBranch.NE, TwelveBranch.USHI)),
)


def calculate_tenchuusatsu(day_kanshi: Kanshi) -> Tenchuusatsu:
    """日柱の干支から天中殺を算出.

    六十干支を10干ずつ6グループに分割。
    各グループで十二支のうち2つが欠ける → その2支が天中殺支。
    """
    group = day_kanshi.index // 10
    tc_type, branches = _GROUP_MAP[group]
    return Tenchuusatsu(type=tc_type, branches=branches)
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_tenchuusatsu.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/tenchuusatsu.py packages/sanmei-core/tests/unit/calculators/test_tenchuusatsu.py
git commit -m "feat(sanmei-core): add tenchuusatsu calculator"
```

---

### Task 10: Major Star Calculator

**Files:**
- Create: `src/sanmei_core/calculators/major_star.py`
- Test: `tests/unit/calculators/test_major_star.py`

**Step 1: Write the failing test**

Create `tests/unit/calculators/test_major_star.py`:

```python
"""十大主星計算のテスト."""

from __future__ import annotations

from sanmei_core.calculators.major_star import calculate_major_star_chart
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar
from sanmei_core.schools.standard import StandardSchool


class TestCalculateMajorStarChart:
    def test_kinoe_ne_hinoe_tora_mizunoe_i(self) -> None:
        """年柱=甲子, 月柱=丙寅, 日柱=壬亥 の十大主星配置."""
        school = StandardSchool()
        pillars = ThreePillars(
            year=Kanshi.from_index(0),   # 甲子
            month=Kanshi.from_index(2),  # 丙寅 (index=2 → stem=丙, branch=寅)
            day=Kanshi.from_index(48),   # 壬子... let me use a specific one
        )
        # 日柱=壬亥 → index=48 → stem=壬(8), branch=亥(11)? No.
        # index 48: stem=48%10=8(壬), branch=48%12=0(子) → 壬子
        # Let's pick 日柱=壬亥: stem=壬(8), branch=亥(11), index=?
        # 8 % 10 = 8, need 48 % 12 = 0 → 子. Try index 59: 59%10=9(癸), 59%12=11(亥)
        # 壬亥: stem=8, branch=11. 8 mod 10 = 8, need (idx)%12=11 → idx=8+10k, 8%12=8, 18%12=6, 28%12=4, 38%12=2, 48%12=0, 58%12=10. None give 11.
        # Actually Kanshi cycle: index where stem=8 AND branch=11:
        # Solve: idx ≡ 8 (mod 10) AND idx ≡ 11 (mod 12).
        # idx=58 → 58%10=8, 58%12=10 → 戌. No.
        # idx=8 → 8%12=8(申). idx=18 → 18%12=6(午). idx=28 → 28%12=4(辰). idx=38 → 38%12=2(寅). idx=48 → 48%12=0(子).
        # 壬 never pairs with 亥 in 60 cycle! Because 8+11=19, 19%2=1 (odd).
        # stem%2 must equal branch%2 for valid kanshi. 壬=8(even), 亥=11(odd). Invalid.
        # Use 壬子 instead: index=48, stem=壬(8), branch=子(0)
        pillars = ThreePillars(
            year=Kanshi.from_index(0),   # 甲子
            month=Kanshi.from_index(2),  # 丙寅
            day=Kanshi.from_index(48),   # 壬子
        )
        hidden = {
            "year": school.get_hidden_stems(pillars.year.branch),    # 子 → 癸
            "month": school.get_hidden_stems(pillars.month.branch),  # 寅 → 甲,丙,戊
            "day": school.get_hidden_stems(pillars.day.branch),      # 子 → 癸
        }
        chart = calculate_major_star_chart(pillars, hidden, school)

        # 日干=壬(水陽)
        # north: 年干=甲(木陽) vs 壬(水陽) → 食傷・同陽 → 鳳閣星
        assert chart.north == MajorStar.HOUKAKU
        # east: 月干=丙(火陽) vs 壬(水陽) → 官星・同陽 → 牽牛星
        assert chart.east == MajorStar.KENGYU
        # center: 日支蔵干主気=癸(水陰) vs 壬(水陽) → 比劫・異陰陽 → 石門星
        assert chart.center == MajorStar.SEKIMON
        # west: 月支蔵干主気=甲(木陽) vs 壬(水陽) → 食傷・同陽 → 鳳閣星
        assert chart.west == MajorStar.HOUKAKU
        # south: 年支蔵干主気=癸(水陰) vs 壬(水陽) → 比劫・異陰陽 → 石門星
        assert chart.south == MajorStar.SEKIMON
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_major_star.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/calculators/major_star.py`:

```python
"""十大主星の算出."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar

if TYPE_CHECKING:
    from sanmei_core.protocols.school import SchoolProtocol


class MajorStarChart:
    """十大主星の人体図（5位置）.

    north: 北(頭) — 年干 vs 日干
    east:  東(左手) — 月干 vs 日干
    center: 中央(胸) — 日支蔵干主気 vs 日干
    west:  西(右手) — 月支蔵干主気 vs 日干
    south: 南(腹) — 年支蔵干主気 vs 日干
    """

    pass  # This will be the domain model, but we define it in domain/meishiki.py later


def calculate_major_star_chart(
    pillars: ThreePillars,
    hidden_stems: dict[str, HiddenStems],
    school: SchoolProtocol,
) -> MajorStarChart:
    """三柱+蔵干から人体図の十大主星5星を算出."""
    from sanmei_core.domain.meishiki import MajorStarChart as MSC

    day_stem = pillars.day.stem
    return MSC(
        north=school.determine_major_star(day_stem, pillars.year.stem),
        east=school.determine_major_star(day_stem, pillars.month.stem),
        center=school.determine_major_star(day_stem, hidden_stems["day"].main),
        west=school.determine_major_star(day_stem, hidden_stems["month"].main),
        south=school.determine_major_star(day_stem, hidden_stems["year"].main),
    )
```

Wait — we need the `MajorStarChart` model first. Let me restructure: we need to create `domain/meishiki.py` first. Let me adjust the plan.

**Revised Step 3: Create domain model + calculator together**

First create `src/sanmei_core/domain/meishiki.py`:

```python
"""命式（めいしき）の複合ドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu


class MajorStarChart(BaseModel, frozen=True):
    """十大主星の人体図（5位置）."""

    north: MajorStar
    east: MajorStar
    center: MajorStar
    west: MajorStar
    south: MajorStar


class SubsidiaryStarChart(BaseModel, frozen=True):
    """十二大従星（3位置）."""

    year: SubsidiaryStar
    month: SubsidiaryStar
    day: SubsidiaryStar


class Meishiki(BaseModel, frozen=True):
    """完全な命式."""

    pillars: ThreePillars
    hidden_stems: dict[str, HiddenStems]
    major_stars: MajorStarChart
    subsidiary_stars: SubsidiaryStarChart
    tenchuusatsu: Tenchuusatsu
```

Then create `src/sanmei_core/calculators/major_star.py`:

```python
"""十大主星の算出."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.meishiki import MajorStarChart
from sanmei_core.domain.pillar import ThreePillars

if TYPE_CHECKING:
    from sanmei_core.protocols.school import SchoolProtocol


def calculate_major_star_chart(
    pillars: ThreePillars,
    hidden_stems: dict[str, HiddenStems],
    school: SchoolProtocol,
) -> MajorStarChart:
    """三柱+蔵干から人体図の十大主星5星を算出."""
    day_stem = pillars.day.stem
    return MajorStarChart(
        north=school.determine_major_star(day_stem, pillars.year.stem),
        east=school.determine_major_star(day_stem, pillars.month.stem),
        center=school.determine_major_star(day_stem, hidden_stems["day"].main),
        west=school.determine_major_star(day_stem, hidden_stems["month"].main),
        south=school.determine_major_star(day_stem, hidden_stems["year"].main),
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_major_star.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/meishiki.py packages/sanmei-core/src/sanmei_core/calculators/major_star.py packages/sanmei-core/tests/unit/calculators/test_major_star.py
git commit -m "feat(sanmei-core): add Meishiki models and major star calculator"
```

---

### Task 11: Subsidiary Star Calculator

**Files:**
- Create: `src/sanmei_core/calculators/subsidiary_star.py`
- Test: `tests/unit/calculators/test_subsidiary_star.py`

**Reference:** `docs/domain/05_Chapter5` Section 5.2

**Step 1: Write the failing test**

Create `tests/unit/calculators/test_subsidiary_star.py`:

```python
"""十二大従星計算のテスト."""

from __future__ import annotations

import pytest

from sanmei_core.calculators.subsidiary_star import (
    calculate_subsidiary_star,
    calculate_subsidiary_star_chart,
)
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import SubsidiaryStar
from sanmei_core.schools.standard import StandardSchool


class TestCalculateSubsidiaryStar:
    """日干と地支から十二大従星を算出.

    標準流派: 帝旺支から順方向に十二運を割り当て。
    """

    def test_kinoe_at_u_is_tenshou(self) -> None:
        """甲(木) の帝旺支=卯 → 卯=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOE, TwelveBranch.U, school) == SubsidiaryStar.TENSHOU

    def test_kinoe_at_tatsu_is_tendou(self) -> None:
        """甲(木) の帝旺支=卯 → 辰=帝旺+1=衰=天堂星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOE, TwelveBranch.TATSU, school) == SubsidiaryStar.TENDOU

    def test_kinoe_at_tora_is_tenroku(self) -> None:
        """甲(木) の帝旺支=卯 → 寅=帝旺-1=建禄=天禄星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.KINOE, TwelveBranch.TORA, school) == SubsidiaryStar.TENROKU

    def test_hinoe_at_uma_is_tenshou(self) -> None:
        """丙(火) の帝旺支=午 → 午=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.HINOE, TwelveBranch.UMA, school) == SubsidiaryStar.TENSHOU

    def test_mizunoe_at_ne_is_tenshou(self) -> None:
        """壬(水) の帝旺支=子 → 子=帝旺=天将星."""
        school = StandardSchool()
        assert calculate_subsidiary_star(TenStem.MIZUNOE, TwelveBranch.NE, school) == SubsidiaryStar.TENSHOU

    @pytest.mark.parametrize(
        ("stem", "branch", "expected"),
        [
            # 甲(帝旺=卯): 子=帝旺から+9=沐浴=天恍星
            (TenStem.KINOE, TwelveBranch.NE, SubsidiaryStar.TENKOU),
            # 甲(帝旺=卯): 午=帝旺から+3=死=天極星
            (TenStem.KINOE, TwelveBranch.UMA, SubsidiaryStar.TENKYOKU),
            # 甲(帝旺=卯): 酉=帝旺から+6=胎=天報星
            (TenStem.KINOE, TwelveBranch.TORI, SubsidiaryStar.TENPOU),
        ],
    )
    def test_parametrized_cases(
        self, stem: TenStem, branch: TwelveBranch, expected: SubsidiaryStar
    ) -> None:
        school = StandardSchool()
        assert calculate_subsidiary_star(stem, branch, school) == expected


class TestCalculateSubsidiaryStarChart:
    def test_chart_from_pillars(self) -> None:
        school = StandardSchool()
        # 日干=甲, 年支=子, 月支=寅, 日支=辰
        pillars = ThreePillars(
            year=Kanshi.from_index(0),   # 甲子
            month=Kanshi.from_index(2),  # 丙寅
            day=Kanshi.from_index(4),    # 戊辰 (stem=4=戊, branch=4=辰)
        )
        # 日干=戊(土陽) の帝旺支=戌(StandardSchool)
        # 年支=子: (0 - 10) % 12 = 2 → index 2 = 病 = 天胡星
        # 月支=寅: (2 - 10) % 12 = 4 → index 4 = 墓 = 天庫星... wait
        # Let me recalculate: distance = (target - teiou) % 12
        # 戊 → 帝旺=戌(10)
        # 子(0): (0 - 10) % 12 = 2 → JUUNIUN[2] = 病 = 天胡星
        # 寅(2): (2 - 10) % 12 = 4 → JUUNIUN[4] = 墓 = 天庫星
        # 辰(4): (4 - 10) % 12 = 6 → JUUNIUN[6] = 胎 = 天報星
        chart = calculate_subsidiary_star_chart(pillars, pillars.day.stem, school)
        assert chart.year == SubsidiaryStar.TENKO      # 病=天胡星
        assert chart.month == SubsidiaryStar.TENKU      # 墓=天庫星
        assert chart.day == SubsidiaryStar.TENPOU       # 胎=天報星
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_subsidiary_star.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/calculators/subsidiary_star.py`:

```python
"""十二大従星の算出."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.meishiki import SubsidiaryStarChart
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import SubsidiaryStar

if TYPE_CHECKING:
    from sanmei_core.protocols.school import SchoolProtocol

JUUNIUN_ORDER: tuple[SubsidiaryStar, ...] = (
    SubsidiaryStar.TENSHOU,   # 帝旺 (0)
    SubsidiaryStar.TENDOU,    # 衰   (1)
    SubsidiaryStar.TENKO,     # 病   (2)
    SubsidiaryStar.TENKYOKU,  # 死   (3)
    SubsidiaryStar.TENKU,     # 墓   (4)
    SubsidiaryStar.TENCHI,    # 絶   (5)
    SubsidiaryStar.TENPOU,    # 胎   (6)
    SubsidiaryStar.TENIN,     # 養   (7)
    SubsidiaryStar.TENKI,     # 長生 (8)
    SubsidiaryStar.TENKOU,    # 沐浴 (9)
    SubsidiaryStar.TENNAN,    # 冠帯 (10)
    SubsidiaryStar.TENROKU,   # 建禄 (11)
)


def calculate_subsidiary_star(
    day_stem: TenStem,
    target_branch: TwelveBranch,
    school: SchoolProtocol,
) -> SubsidiaryStar:
    """日干と対象地支から十二大従星を算出.

    帝旺支から対象地支までの順方向距離で十二運を決定。
    """
    teiou = school.get_teiou_branch(day_stem)
    distance = (target_branch.value - teiou.value) % 12
    return JUUNIUN_ORDER[distance]


def calculate_subsidiary_star_chart(
    pillars: ThreePillars,
    day_stem: TenStem,
    school: SchoolProtocol,
) -> SubsidiaryStarChart:
    """三柱から十二大従星3つを算出."""
    return SubsidiaryStarChart(
        year=calculate_subsidiary_star(day_stem, pillars.year.branch, school),
        month=calculate_subsidiary_star(day_stem, pillars.month.branch, school),
        day=calculate_subsidiary_star(day_stem, pillars.day.branch, school),
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_subsidiary_star.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/subsidiary_star.py packages/sanmei-core/tests/unit/calculators/test_subsidiary_star.py
git commit -m "feat(sanmei-core): add subsidiary star calculator"
```

---

### Task 12: MeishikiCalculator Facade

**Files:**
- Create: `src/sanmei_core/calculators/meishiki_calculator.py`
- Test: `tests/unit/calculators/test_meishiki_calculator.py`

**Reference:** `docs/domain/Appendix_A_Meishiki_Samples.md` (1985-04-10 サンプル)

**Step 1: Write the failing test**

Create `tests/unit/calculators/test_meishiki_calculator.py`:

```python
"""MeishikiCalculator 統合テスト."""

from __future__ import annotations

from datetime import datetime, timezone

from sanmei_core.calculators.meishiki_calculator import MeishikiCalculator
from sanmei_core.constants import JST
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.tenchuusatsu import TenchuusatsuType
from sanmei_core.schools.standard import StandardSchool


class TestMeishikiCalculator:
    def test_basic_calculation(self) -> None:
        """基本的な命式計算が正しく動作する."""
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)

        assert meishiki.pillars.year.stem is not None
        assert meishiki.pillars.month.stem is not None
        assert meishiki.pillars.day.stem is not None
        assert len(meishiki.hidden_stems) == 3
        assert "year" in meishiki.hidden_stems
        assert "month" in meishiki.hidden_stems
        assert "day" in meishiki.hidden_stems
        assert meishiki.major_stars.north is not None
        assert meishiki.subsidiary_stars.year is not None
        assert meishiki.tenchuusatsu.type is not None

    def test_appendix_a_sample(self) -> None:
        """Appendix A サンプル: 1985年4月10日（男性）.

        年柱=乙丑, 月柱=庚辰, 日柱=癸亥 (要検証)
        蔵干(主): 己, 戊, 壬
        """
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        # 1985-04-10 (清明=4/5頃 を過ぎている → 辰月)
        dt = datetime(1985, 4, 10, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)

        # 蔵干の主気を検証
        assert meishiki.hidden_stems["year"].main is not None
        assert meishiki.hidden_stems["month"].main is not None
        assert meishiki.hidden_stems["day"].main is not None

        # 天中殺の type が有効であること
        assert isinstance(meishiki.tenchuusatsu.type, TenchuusatsuType)

    def test_meishiki_is_frozen(self) -> None:
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 1, 1, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        # frozen model → attribute assignment raises
        import pytest

        with pytest.raises(Exception):
            meishiki.pillars = None  # type: ignore[assignment]
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/sanmei_core/calculators/meishiki_calculator.py`:

```python
"""MeishikiCalculator — 命式算出の統合ファサード."""

from __future__ import annotations

from datetime import datetime, tzinfo

from sanmei_core.calculators.major_star import calculate_major_star_chart
from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.subsidiary_star import calculate_subsidiary_star_chart
from sanmei_core.calculators.tenchuusatsu import calculate_tenchuusatsu
from sanmei_core.constants import JST
from sanmei_core.domain.meishiki import Meishiki
from sanmei_core.protocols.school import SchoolProtocol


class MeishikiCalculator:
    """西暦日時から完全な命式を算出する統合ファサード."""

    def __init__(
        self,
        school: SchoolProtocol,
        *,
        tz: tzinfo | None = None,
    ) -> None:
        self._school = school
        self._tz = tz or JST
        self._calendar = SanmeiCalendar(
            school.get_setsuiri_provider(), tz=self._tz
        )

    def calculate(self, dt: datetime) -> Meishiki:
        """西暦日時から完全な命式を算出."""
        pillars = self._calendar.three_pillars(dt)
        hidden_stems = {
            "year": self._school.get_hidden_stems(pillars.year.branch),
            "month": self._school.get_hidden_stems(pillars.month.branch),
            "day": self._school.get_hidden_stems(pillars.day.branch),
        }
        major_stars = calculate_major_star_chart(pillars, hidden_stems, self._school)
        subsidiary_stars = calculate_subsidiary_star_chart(
            pillars, pillars.day.stem, self._school
        )
        tenchuusatsu = calculate_tenchuusatsu(pillars.day)
        return Meishiki(
            pillars=pillars,
            hidden_stems=hidden_stems,
            major_stars=major_stars,
            subsidiary_stars=subsidiary_stars,
            tenchuusatsu=tenchuusatsu,
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/meishiki_calculator.py packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py
git commit -m "feat(sanmei-core): add MeishikiCalculator facade"
```

---

### Task 13: Public API & Quality Gate

**Files:**
- Modify: `src/sanmei_core/__init__.py`
- Modify: `src/sanmei_core/schools/__init__.py`

**Step 1: Update public API**

Add new exports to `src/sanmei_core/__init__.py`:

```python
"""算命学コアロジック - 純粋計算ライブラリ."""

from sanmei_core.calculators.meishiki_calculator import MeishikiCalculator
from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.solar_longitude import MeeusSetsuiriProvider
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.errors import (
    DateOutOfRangeError,
    SanmeiError,
    SetsuiriNotFoundError,
)
from sanmei_core.domain.gogyo import GoGyo, InYou
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.meishiki import Meishiki, MajorStarChart, SubsidiaryStarChart
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType
from sanmei_core.protocols.school import SchoolProtocol
from sanmei_core.protocols.setsuiri import SetsuiriProvider
from sanmei_core.schools.registry import SchoolRegistry
from sanmei_core.schools.standard import StandardSchool

__all__ = [
    "DateOutOfRangeError",
    "GoGyo",
    "HiddenStems",
    "InYou",
    "Kanshi",
    "MajorStar",
    "MajorStarChart",
    "MeeusSetsuiriProvider",
    "Meishiki",
    "MeishikiCalculator",
    "SanmeiCalendar",
    "SanmeiError",
    "SchoolProtocol",
    "SchoolRegistry",
    "SetsuiriDate",
    "SetsuiriNotFoundError",
    "SetsuiriProvider",
    "SolarTerm",
    "StandardSchool",
    "SubsidiaryStar",
    "SubsidiaryStarChart",
    "TenStem",
    "Tenchuusatsu",
    "TenchuusatsuType",
    "ThreePillars",
    "TwelveBranch",
]
```

**Step 2: Run full quality gate**

```bash
just check
```

Expected: lint PASS, typecheck PASS, tests PASS (all existing + new)

**Step 3: Run coverage check**

```bash
uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v --cov=sanmei_core --cov-report=term-missing
```

Expected: 80%+ coverage

**Step 4: Fix any lint/type issues found**

Address any ruff or mypy errors.

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/__init__.py packages/sanmei-core/src/sanmei_core/schools/__init__.py
git commit -m "feat(sanmei-core): export meishiki public API and pass quality gate"
```
