# 大運四季表 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `sanmei taiun-shiki` CLI subcommand that outputs a 大運四季表 (Major Fortune Seasonal Table) showing season, age, kanshi, hidden stems, stars, and life cycle for each taiun period.

**Architecture:** New domain models (`Season`, `LifeCycle`, `TaiunShikiEntry`, `TaiunShikiChart`) and mapping tables in sanmei-core, with a calculator that composes existing `TaiunChart` with star/season calculations. CLI gets a new subcommand + text formatter function. Existing code is untouched.

**Tech Stack:** Python 3.14+, Pydantic (frozen models), click (CLI), pytest (TDD)

**Reference files:**
- Design doc: `docs/plans/2026-03-04-taiun-shiki-design.md`
- Existing patterns: `packages/sanmei-core/src/sanmei_core/domain/fortune.py`, `calculators/fortune.py`
- CLI patterns: `apps/sanmei-cli/src/sanmei_cli/commands/taiun.py`, `formatters/text.py`

---

### Task 1: Domain models — Season, LifeCycle enums

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/taiun_shiki.py`
- Test: `packages/sanmei-core/tests/unit/domain/test_taiun_shiki.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/domain/test_taiun_shiki.py
"""大運四季表ドメインモデルのテスト."""

from sanmei_core.domain.taiun_shiki import LifeCycle, Season


class TestSeason:
    def test_values(self) -> None:
        assert Season.SPRING.value == "春"
        assert Season.SUMMER.value == "夏"
        assert Season.AUTUMN.value == "秋"
        assert Season.WINTER.value == "冬"

    def test_count(self) -> None:
        assert len(Season) == 4


class TestLifeCycle:
    def test_all_twelve(self) -> None:
        assert len(LifeCycle) == 12

    def test_first_and_last(self) -> None:
        assert LifeCycle.TAIJI.value == "胎児"
        assert LifeCycle.ANOYO.value == "あの世"

    def test_middle_values(self) -> None:
        assert LifeCycle.SEINEN.value == "青年"
        assert LifeCycle.ROUJIN.value == "老人"
        assert LifeCycle.SHININ.value == "死人"
        assert LifeCycle.NYUUBO.value == "入墓"
```

**Step 2: Run test to verify it fails**

Run: `cd packages/sanmei-core && uv run pytest tests/unit/domain/test_taiun_shiki.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sanmei_core.domain.taiun_shiki'`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/taiun_shiki.py
"""大運四季表のドメインモデル."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.star import MajorStar, SubsidiaryStar


class Season(Enum):
    """四季."""

    SPRING = "春"  # 寅・卯・辰
    SUMMER = "夏"  # 巳・午・未
    AUTUMN = "秋"  # 申・酉・戌
    WINTER = "冬"  # 亥・子・丑


class LifeCycle(Enum):
    """一生の運気サイクル（十二大従星に対応）."""

    TAIJI = "胎児"  # 天報星
    AKAGO = "赤子"  # 天印星
    JIDOU = "児童"  # 天貴星
    SEISHONEN = "青少年"  # 天恍星
    SEINEN = "青年"  # 天南星
    SOUNEN = "壮年"  # 天禄星
    KACHOU = "家長"  # 天将星
    ROUJIN = "老人"  # 天堂星
    BYOUNIN = "病人"  # 天胡星
    SHININ = "死人"  # 天極星
    NYUUBO = "入墓"  # 天庫星
    ANOYO = "あの世"  # 天馳星


class TaiunShikiEntry(BaseModel, frozen=True):
    """大運四季表の1行."""

    label: str
    kanshi: Kanshi
    start_age: int
    end_age: int
    season: Season
    hidden_stems: HiddenStems
    major_star: MajorStar
    subsidiary_star: SubsidiaryStar
    life_cycle: LifeCycle


class TaiunShikiChart(BaseModel, frozen=True):
    """大運四季表."""

    direction: Literal["順行", "逆行"]
    start_age: int
    entries: tuple[TaiunShikiEntry, ...]
```

**Step 4: Run test to verify it passes**

Run: `cd packages/sanmei-core && uv run pytest tests/unit/domain/test_taiun_shiki.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/domain/taiun_shiki.py packages/sanmei-core/tests/unit/domain/test_taiun_shiki.py
git commit -m "feat(sanmei-core): add Season, LifeCycle, TaiunShikiEntry domain models"
```

---

### Task 2: Domain model — TaiunShikiEntry and TaiunShikiChart construction

**Files:**
- Modify: `packages/sanmei-core/tests/unit/domain/test_taiun_shiki.py`

**Step 1: Write the failing test**

Append to the test file:

```python
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.taiun_shiki import TaiunShikiChart, TaiunShikiEntry


class TestTaiunShikiEntry:
    def test_construction(self) -> None:
        entry = TaiunShikiEntry(
            label="第1句",
            kanshi=Kanshi.from_index(2),  # 丙寅
            start_age=5,
            end_age=14,
            season=Season.SPRING,
            hidden_stems=HiddenStems(
                hongen=TenStem.KINOE,
                chuugen=TenStem.HINOE,
                shogen=TenStem.TSUCHINOE,
            ),
            major_star=MajorStar.HOUKAKU,
            subsidiary_star=SubsidiaryStar.TENNAN,
            life_cycle=LifeCycle.SEINEN,
        )
        assert entry.label == "第1句"
        assert entry.kanshi.kanji == "丙寅"
        assert entry.season == Season.SPRING
        assert entry.life_cycle == LifeCycle.SEINEN

    def test_frozen(self) -> None:
        entry = TaiunShikiEntry(
            label="月干支",
            kanshi=Kanshi.from_index(0),
            start_age=0,
            end_age=4,
            season=Season.WINTER,
            hidden_stems=HiddenStems(hongen=TenStem.MIZUNOTO),
            major_star=MajorStar.KANSAKU,
            subsidiary_star=SubsidiaryStar.TENPOU,
            life_cycle=LifeCycle.TAIJI,
        )
        import pytest
        with pytest.raises(Exception):
            entry.label = "changed"  # type: ignore[misc]


class TestTaiunShikiChart:
    def test_construction(self) -> None:
        entry = TaiunShikiEntry(
            label="月干支",
            kanshi=Kanshi.from_index(0),
            start_age=0,
            end_age=4,
            season=Season.WINTER,
            hidden_stems=HiddenStems(hongen=TenStem.MIZUNOTO),
            major_star=MajorStar.KANSAKU,
            subsidiary_star=SubsidiaryStar.TENPOU,
            life_cycle=LifeCycle.TAIJI,
        )
        chart = TaiunShikiChart(
            direction="順行",
            start_age=5,
            entries=(entry,),
        )
        assert chart.direction == "順行"
        assert len(chart.entries) == 1
```

**Step 2: Run test to verify it passes**

Run: `cd packages/sanmei-core && uv run pytest tests/unit/domain/test_taiun_shiki.py -v`
Expected: PASS (all 8 tests — the models are already implemented)

**Step 3: Commit**

```bash
git add packages/sanmei-core/tests/unit/domain/test_taiun_shiki.py
git commit -m "test(sanmei-core): add TaiunShikiEntry and TaiunShikiChart construction tests"
```

---

### Task 3: Mapping tables — BRANCH_TO_SEASON and SUBSIDIARY_STAR_TO_LIFE_CYCLE

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/tables/taiun_shiki.py`
- Create: `packages/sanmei-core/tests/unit/tables/test_taiun_shiki.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/tables/test_taiun_shiki.py
"""大運四季表マッピングテーブルのテスト."""

from sanmei_core.domain.kanshi import TwelveBranch
from sanmei_core.domain.star import SubsidiaryStar
from sanmei_core.domain.taiun_shiki import LifeCycle, Season
from sanmei_core.tables.taiun_shiki import (
    BRANCH_TO_SEASON,
    SUBSIDIARY_STAR_TO_LIFE_CYCLE,
)


class TestBranchToSeason:
    def test_all_twelve_branches_mapped(self) -> None:
        assert len(BRANCH_TO_SEASON) == 12
        for branch in TwelveBranch:
            assert branch in BRANCH_TO_SEASON

    def test_spring(self) -> None:
        assert BRANCH_TO_SEASON[TwelveBranch.TORA] == Season.SPRING
        assert BRANCH_TO_SEASON[TwelveBranch.U] == Season.SPRING
        assert BRANCH_TO_SEASON[TwelveBranch.TATSU] == Season.SPRING

    def test_summer(self) -> None:
        assert BRANCH_TO_SEASON[TwelveBranch.MI] == Season.SUMMER
        assert BRANCH_TO_SEASON[TwelveBranch.UMA] == Season.SUMMER
        assert BRANCH_TO_SEASON[TwelveBranch.HITSUJI] == Season.SUMMER

    def test_autumn(self) -> None:
        assert BRANCH_TO_SEASON[TwelveBranch.SARU] == Season.AUTUMN
        assert BRANCH_TO_SEASON[TwelveBranch.TORI] == Season.AUTUMN
        assert BRANCH_TO_SEASON[TwelveBranch.INU] == Season.AUTUMN

    def test_winter(self) -> None:
        assert BRANCH_TO_SEASON[TwelveBranch.I] == Season.WINTER
        assert BRANCH_TO_SEASON[TwelveBranch.NE] == Season.WINTER
        assert BRANCH_TO_SEASON[TwelveBranch.USHI] == Season.WINTER


class TestSubsidiaryStarToLifeCycle:
    def test_all_twelve_stars_mapped(self) -> None:
        assert len(SUBSIDIARY_STAR_TO_LIFE_CYCLE) == 12
        for star in SubsidiaryStar:
            assert star in SUBSIDIARY_STAR_TO_LIFE_CYCLE

    def test_first_last(self) -> None:
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENPOU] == LifeCycle.TAIJI
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENCHI] == LifeCycle.ANOYO

    def test_middle_mappings(self) -> None:
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENNAN] == LifeCycle.SEINEN
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENSHOU] == LifeCycle.KACHOU
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENDOU] == LifeCycle.ROUJIN
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENKO] == LifeCycle.BYOUNIN
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENKYOKU] == LifeCycle.SHININ
        assert SUBSIDIARY_STAR_TO_LIFE_CYCLE[SubsidiaryStar.TENKU] == LifeCycle.NYUUBO
```

**Step 2: Run test to verify it fails**

Run: `cd packages/sanmei-core && uv run pytest tests/unit/tables/test_taiun_shiki.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sanmei_core.tables.taiun_shiki'`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/tables/taiun_shiki.py
"""大運四季表のマッピングテーブル."""

from sanmei_core.domain.kanshi import TwelveBranch
from sanmei_core.domain.star import SubsidiaryStar
from sanmei_core.domain.taiun_shiki import LifeCycle, Season

BRANCH_TO_SEASON: dict[TwelveBranch, Season] = {
    TwelveBranch.TORA: Season.SPRING,
    TwelveBranch.U: Season.SPRING,
    TwelveBranch.TATSU: Season.SPRING,
    TwelveBranch.MI: Season.SUMMER,
    TwelveBranch.UMA: Season.SUMMER,
    TwelveBranch.HITSUJI: Season.SUMMER,
    TwelveBranch.SARU: Season.AUTUMN,
    TwelveBranch.TORI: Season.AUTUMN,
    TwelveBranch.INU: Season.AUTUMN,
    TwelveBranch.I: Season.WINTER,
    TwelveBranch.NE: Season.WINTER,
    TwelveBranch.USHI: Season.WINTER,
}

SUBSIDIARY_STAR_TO_LIFE_CYCLE: dict[SubsidiaryStar, LifeCycle] = {
    SubsidiaryStar.TENPOU: LifeCycle.TAIJI,
    SubsidiaryStar.TENIN: LifeCycle.AKAGO,
    SubsidiaryStar.TENKI: LifeCycle.JIDOU,
    SubsidiaryStar.TENKOU: LifeCycle.SEISHONEN,
    SubsidiaryStar.TENNAN: LifeCycle.SEINEN,
    SubsidiaryStar.TENROKU: LifeCycle.SOUNEN,
    SubsidiaryStar.TENSHOU: LifeCycle.KACHOU,
    SubsidiaryStar.TENDOU: LifeCycle.ROUJIN,
    SubsidiaryStar.TENKO: LifeCycle.BYOUNIN,
    SubsidiaryStar.TENKYOKU: LifeCycle.SHININ,
    SubsidiaryStar.TENKU: LifeCycle.NYUUBO,
    SubsidiaryStar.TENCHI: LifeCycle.ANOYO,
}
```

**Step 4: Run test to verify it passes**

Run: `cd packages/sanmei-core && uv run pytest tests/unit/tables/test_taiun_shiki.py -v`
Expected: PASS (all 8 tests)

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/tables/taiun_shiki.py packages/sanmei-core/tests/unit/tables/test_taiun_shiki.py
git commit -m "feat(sanmei-core): add BRANCH_TO_SEASON and SUBSIDIARY_STAR_TO_LIFE_CYCLE tables"
```

---

### Task 4: Calculator — calculate_taiun_shiki()

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/taiun_shiki.py`
- Create: `packages/sanmei-core/tests/unit/calculators/test_taiun_shiki.py`

This task tests the core calculation. We use a known meishiki (born 2024-04-20 12:00 JST, male) where we can hand-calculate the expected stars for each taiun period.

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_taiun_shiki.py
"""大運四季表計算のテスト."""

from __future__ import annotations

from sanmei_core.calculators.taiun_shiki import calculate_taiun_shiki
from sanmei_core.domain.fortune import Taiun, TaiunChart
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.meishiki import (
    MajorStarChart,
    Meishiki,
    SubsidiaryStarChart,
)
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.taiun_shiki import LifeCycle, Season
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType
from sanmei_core.domain.zoukan_tokutei import (
    ActiveHiddenStem,
    HiddenStemType,
    ZoukanTokutei,
)
from sanmei_core.schools.standard import StandardSchool


def _make_dummy_gogyo_balance() -> GoGyoBalance:
    count = GoGyoCount(wood=1, fire=1, earth=1, metal=1, water=1)
    return GoGyoBalance(
        stem_count=count,
        branch_count=count,
        total_count=count,
        dominant=GoGyo.WOOD,
        lacking=(),
        day_stem_gogyo=GoGyo.WOOD,
    )


def _make_test_meishiki() -> Meishiki:
    """テスト命式: 日干=甲(木陽), 月柱=戊辰(index=4)."""
    return Meishiki(
        pillars=ThreePillars(
            year=Kanshi.from_index(0),  # 甲子
            month=Kanshi.from_index(4),  # 戊辰
            day=Kanshi(stem=TenStem.KINOE, branch=TwelveBranch.NE, index=0),  # 甲子
        ),
        hidden_stems={
            "year": HiddenStems(hongen=TenStem.MIZUNOTO),
            "month": HiddenStems(
                hongen=TenStem.TSUCHINOE,
                chuugen=TenStem.MIZUNOTO,
                shogen=TenStem.KINOTO,
            ),
            "day": HiddenStems(hongen=TenStem.MIZUNOTO),
        },
        zoukan_tokutei=ZoukanTokutei(
            days_from_setsuiri=15,
            year=ActiveHiddenStem(stem=TenStem.MIZUNOTO, element=HiddenStemType.HONGEN),
            month=ActiveHiddenStem(stem=TenStem.TSUCHINOE, element=HiddenStemType.HONGEN),
            day=ActiveHiddenStem(stem=TenStem.MIZUNOTO, element=HiddenStemType.HONGEN),
        ),
        major_stars=MajorStarChart(
            north=MajorStar.KANSAKU,
            east=MajorStar.KANSAKU,
            center=MajorStar.KANSAKU,
            west=MajorStar.KANSAKU,
            south=MajorStar.KANSAKU,
        ),
        subsidiary_stars=SubsidiaryStarChart(
            year=SubsidiaryStar.TENPOU,
            month=SubsidiaryStar.TENPOU,
            day=SubsidiaryStar.TENPOU,
        ),
        shimeisei=MajorStar.KANSAKU,
        tenchuusatsu=Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        ),
        shukumei_chuusatsu=(),
        gogyo_balance=_make_dummy_gogyo_balance(),
    )


def _make_test_taiun_chart() -> TaiunChart:
    """テスト大運: 順行、立運5歳、月柱=戊辰(4)から順行で3期間."""
    return TaiunChart(
        direction="順行",
        start_age=5,
        periods=(
            Taiun(kanshi=Kanshi.from_index(5), start_age=5, end_age=14),   # 己巳
            Taiun(kanshi=Kanshi.from_index(6), start_age=15, end_age=24),  # 庚午
            Taiun(kanshi=Kanshi.from_index(7), start_age=25, end_age=34),  # 辛未
        ),
    )


class TestCalculateTaiunShiki:
    def setup_method(self) -> None:
        self.school = StandardSchool()
        self.meishiki = _make_test_meishiki()
        self.taiun_chart = _make_test_taiun_chart()

    def test_returns_chart(self) -> None:
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.direction == "順行"
        assert result.start_age == 5

    def test_entry_count(self) -> None:
        """月干支行 + 3期間 = 4行."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert len(result.entries) == 4

    def test_month_kanshi_entry(self) -> None:
        """先頭行は月干支."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        first = result.entries[0]
        assert first.label == "月干支"
        assert first.kanshi.kanji == "戊辰"
        assert first.start_age == 0
        assert first.end_age == 4

    def test_month_kanshi_season(self) -> None:
        """辰 = 春."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[0].season == Season.SPRING

    def test_month_kanshi_hidden_stems(self) -> None:
        """辰の蔵干: 戊(本元), 癸(中元), 乙(初元)."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        hs = result.entries[0].hidden_stems
        assert hs.hongen == TenStem.TSUCHINOE
        assert hs.chuugen == TenStem.MIZUNOTO
        assert hs.shogen == TenStem.KINOTO

    def test_month_kanshi_major_star(self) -> None:
        """日干=甲(木陽) × 月干=戊(土陽) → 木剋土 = 財星・同陰陽 → 禄存星."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[0].major_star == MajorStar.ROKUZON

    def test_month_kanshi_subsidiary_star(self) -> None:
        """日干=甲 × 辰 → calculate_subsidiary_star で算出."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        # 甲の帝旺支=卯(3), 辰(4), distance=(4-3)%12=1 → JUUNIUN_ORDER[1]=天堂星(衰)
        assert result.entries[0].subsidiary_star == SubsidiaryStar.TENDOU

    def test_month_kanshi_life_cycle(self) -> None:
        """天堂星 → 老人."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[0].life_cycle == LifeCycle.ROUJIN

    def test_period_labels(self) -> None:
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[1].label == "第1句"
        assert result.entries[2].label == "第2句"
        assert result.entries[3].label == "第3句"

    def test_period_1_season(self) -> None:
        """己巳: 巳 = 夏."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[1].season == Season.SUMMER

    def test_period_1_major_star(self) -> None:
        """日干=甲(木陽) × 己(土陰) → 木剋土 = 財星・異陰陽 → 司禄星."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[1].major_star == MajorStar.SHIROKU

    def test_period_2_kanshi(self) -> None:
        """第2句 = 庚午."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[2].kanshi.kanji == "庚午"
        assert result.entries[2].start_age == 15
        assert result.entries[2].end_age == 24

    def test_period_2_season(self) -> None:
        """午 = 夏."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[2].season == Season.SUMMER

    def test_period_3_season(self) -> None:
        """未 = 夏."""
        result = calculate_taiun_shiki(self.meishiki, self.taiun_chart, self.school)
        assert result.entries[3].season == Season.SUMMER
```

**Step 2: Run test to verify it fails**

Run: `cd packages/sanmei-core && uv run pytest tests/unit/calculators/test_taiun_shiki.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sanmei_core.calculators.taiun_shiki'`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/taiun_shiki.py
"""大運四季表の算出."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.calculators.subsidiary_star import calculate_subsidiary_star
from sanmei_core.domain.taiun_shiki import TaiunShikiChart, TaiunShikiEntry
from sanmei_core.tables.hidden_stems import STANDARD_HIDDEN_STEMS
from sanmei_core.tables.taiun_shiki import BRANCH_TO_SEASON, SUBSIDIARY_STAR_TO_LIFE_CYCLE

if TYPE_CHECKING:
    from sanmei_core.domain.fortune import TaiunChart
    from sanmei_core.domain.meishiki import Meishiki
    from sanmei_core.protocols.school import SchoolProtocol


def calculate_taiun_shiki(
    meishiki: Meishiki,
    taiun_chart: TaiunChart,
    school: SchoolProtocol,
) -> TaiunShikiChart:
    """命式と大運表から大運四季表を算出."""
    day_stem = meishiki.pillars.day.stem
    entries: list[TaiunShikiEntry] = []

    # 月干支行
    month_kanshi = meishiki.pillars.month.kanshi
    month_sub = calculate_subsidiary_star(day_stem, month_kanshi.branch, school)
    entries.append(
        TaiunShikiEntry(
            label="月干支",
            kanshi=month_kanshi,
            start_age=0,
            end_age=max(0, taiun_chart.start_age - 1),
            season=BRANCH_TO_SEASON[month_kanshi.branch],
            hidden_stems=STANDARD_HIDDEN_STEMS[month_kanshi.branch],
            major_star=school.determine_major_star(day_stem, month_kanshi.stem),
            subsidiary_star=month_sub,
            life_cycle=SUBSIDIARY_STAR_TO_LIFE_CYCLE[month_sub],
        )
    )

    # 各大運期間
    for i, period in enumerate(taiun_chart.periods, 1):
        sub = calculate_subsidiary_star(day_stem, period.kanshi.branch, school)
        entries.append(
            TaiunShikiEntry(
                label=f"第{i}句",
                kanshi=period.kanshi,
                start_age=period.start_age,
                end_age=period.end_age,
                season=BRANCH_TO_SEASON[period.kanshi.branch],
                hidden_stems=STANDARD_HIDDEN_STEMS[period.kanshi.branch],
                major_star=school.determine_major_star(day_stem, period.kanshi.stem),
                subsidiary_star=sub,
                life_cycle=SUBSIDIARY_STAR_TO_LIFE_CYCLE[sub],
            )
        )

    return TaiunShikiChart(
        direction=taiun_chart.direction,
        start_age=taiun_chart.start_age,
        entries=tuple(entries),
    )
```

**Step 4: Run test to verify it passes**

Run: `cd packages/sanmei-core && uv run pytest tests/unit/calculators/test_taiun_shiki.py -v`
Expected: PASS (all 15 tests)

**Step 5: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/calculators/taiun_shiki.py packages/sanmei-core/tests/unit/calculators/test_taiun_shiki.py
git commit -m "feat(sanmei-core): add calculate_taiun_shiki() calculator"
```

---

### Task 5: Update sanmei-core __init__.py exports

**Files:**
- Modify: `packages/sanmei-core/src/sanmei_core/__init__.py`

**Step 1: Write the failing test**

```python
# Append a test to packages/sanmei-core/tests/unit/test_smoke.py or run interactively:
# python -c "from sanmei_core import calculate_taiun_shiki, Season, LifeCycle, TaiunShikiChart, TaiunShikiEntry"
```

Actually, just verify the import works after the change.

**Step 2: Modify `__init__.py`**

Add these imports (alphabetically placed):

```python
# In the imports section, add:
from sanmei_core.calculators.taiun_shiki import calculate_taiun_shiki
from sanmei_core.domain.taiun_shiki import (
    LifeCycle,
    Season,
    TaiunShikiChart,
    TaiunShikiEntry,
)

# In __all__, add (alphabetically):
#   "LifeCycle",
#   "Season",
#   "TaiunShikiChart",
#   "TaiunShikiEntry",
#   "calculate_taiun_shiki",
```

**Step 3: Run full sanmei-core tests**

Run: `cd packages/sanmei-core && uv run pytest tests/ -v --tb=short`
Expected: ALL PASS (existing + new tests)

**Step 4: Commit**

```bash
git add packages/sanmei-core/src/sanmei_core/__init__.py
git commit -m "feat(sanmei-core): export taiun_shiki models and calculator from __init__"
```

---

### Task 6: CLI text formatter — format_taiun_shiki()

**Files:**
- Modify: `apps/sanmei-cli/src/sanmei_cli/formatters/text.py`
- Modify: `apps/sanmei-cli/tests/test_text_formatter.py`

**Step 1: Write the failing test**

Append to `apps/sanmei-cli/tests/test_text_formatter.py`:

```python
from sanmei_core import calculate_taiun_shiki

from sanmei_cli.formatters.text import format_taiun_shiki


class TestFormatTaiunShiki:
    @pytest.fixture
    def shiki_chart(self, meishiki, taiun_chart, school):
        return calculate_taiun_shiki(meishiki, taiun_chart, school)

    def test_contains_header(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert "=== 大運四季表 ===" in result

    def test_contains_direction(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert shiki_chart.direction in result

    def test_contains_start_age(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert f"立運: {shiki_chart.start_age}歳" in result

    def test_column_headers(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert "季節" in result
        assert "年齢" in result
        assert "大運" in result
        assert "干支" in result
        assert "蔵干" in result
        assert "十大主星" in result
        assert "十二大従星" in result
        assert "サイクル" in result

    def test_column_order(self, shiki_chart):
        """列順: 季節→年齢→大運→干支→蔵干→十大主星→十二大従星→サイクル."""
        result = format_taiun_shiki(shiki_chart)
        header_line = [l for l in result.split("\n") if "季節" in l and "サイクル" in l][0]
        assert header_line.index("季節") < header_line.index("年齢")
        assert header_line.index("年齢") < header_line.index("大運")
        assert header_line.index("大運") < header_line.index("干支")
        assert header_line.index("干支") < header_line.index("蔵干")
        assert header_line.index("蔵干") < header_line.index("十大主星")
        assert header_line.index("十大主星") < header_line.index("十二大従星")
        assert header_line.index("十二大従星") < header_line.index("サイクル")

    def test_contains_month_kanshi_label(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert "月干支" in result

    def test_contains_period_labels(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        assert "第1句" in result

    def test_contains_season_values(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.season.value in result

    def test_contains_kanshi_kanji(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.kanshi.kanji in result

    def test_contains_major_star(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.major_star.value in result

    def test_contains_subsidiary_star(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.subsidiary_star.value in result

    def test_contains_life_cycle(self, shiki_chart):
        result = format_taiun_shiki(shiki_chart)
        for entry in shiki_chart.entries:
            assert entry.life_cycle.value in result

    def test_hidden_stems_dot_separated(self, shiki_chart):
        """蔵干が「・」区切りで表示される."""
        result = format_taiun_shiki(shiki_chart)
        # 蔵干が複数ある行には「・」が含まれる
        has_multi = any(
            e.hidden_stems.chuugen is not None or e.hidden_stems.shogen is not None
            for e in shiki_chart.entries
        )
        if has_multi:
            assert "・" in result
```

Note: add `import pytest` at the top of the test file if not already present.

Also add fixture to `apps/sanmei-cli/tests/conftest.py`:

```python
# Add import
from sanmei_core import calculate_taiun_shiki

# Add fixture
@pytest.fixture
def shiki_chart(meishiki, taiun_chart, school):
    return calculate_taiun_shiki(meishiki, taiun_chart, school)
```

**Step 2: Run test to verify it fails**

Run: `cd apps/sanmei-cli && uv run pytest tests/test_text_formatter.py::TestFormatTaiunShiki -v`
Expected: FAIL with `ImportError: cannot import name 'format_taiun_shiki'`

**Step 3: Write minimal implementation**

Add to the end of `apps/sanmei-cli/src/sanmei_cli/formatters/text.py`:

```python
def format_taiun_shiki(chart: TaiunShikiChart) -> str:
    """大運四季表をテキスト形式でフォーマット."""
    lines: list[str] = []
    lines.append("=== 大運四季表 ===")
    lines.append(f"方向: {chart.direction}  立運: {chart.start_age}歳")
    lines.append("")

    # 列幅定義
    w_season = 6    # 季節
    w_age = 12      # 年齢
    w_label = 10    # 大運
    w_kanshi = 6    # 干支
    w_zoukan = 12   # 蔵干
    w_major = 10    # 十大主星
    w_sub = 10      # 十二大従星

    # ヘッダー
    lines.append(
        f"{_cjk_ljust('季節', w_season)}"
        f"{_cjk_ljust('年齢', w_age)}"
        f"{_cjk_ljust('大運', w_label)}"
        f"{_cjk_ljust('干支', w_kanshi)}"
        f"{_cjk_ljust('蔵干', w_zoukan)}"
        f"{_cjk_ljust('十大主星', w_major)}"
        f"{_cjk_ljust('十二大従星', w_sub)}"
        f"サイクル"
    )

    for entry in chart.entries:
        # 蔵干を「・」区切りで列挙（hongen, chuugen, shogenの順、Noneは省略）
        stems = [_STEM_KANJI[entry.hidden_stems.hongen.value]]
        if entry.hidden_stems.chuugen is not None:
            stems.append(_STEM_KANJI[entry.hidden_stems.chuugen.value])
        if entry.hidden_stems.shogen is not None:
            stems.append(_STEM_KANJI[entry.hidden_stems.shogen.value])
        zoukan_str = "・".join(stems)

        # 年齢
        age_str = f"{entry.start_age}-{entry.end_age}歳"

        lines.append(
            f"{_cjk_ljust(entry.season.value, w_season)}"
            f"{_cjk_ljust(age_str, w_age)}"
            f"{_cjk_ljust(entry.label, w_label)}"
            f"{_cjk_ljust(entry.kanshi.kanji, w_kanshi)}"
            f"{_cjk_ljust(zoukan_str, w_zoukan)}"
            f"{_cjk_ljust(entry.major_star.value, w_major)}"
            f"{_cjk_ljust(entry.subsidiary_star.value, w_sub)}"
            f"{entry.life_cycle.value}"
        )

    return "\n".join(lines)
```

Also add to the `TYPE_CHECKING` block at the top of the file:

```python
from sanmei_core.domain.taiun_shiki import TaiunShikiChart
```

**Step 4: Run test to verify it passes**

Run: `cd apps/sanmei-cli && uv run pytest tests/test_text_formatter.py::TestFormatTaiunShiki -v`
Expected: PASS (all 13 tests)

**Step 5: Commit**

```bash
git add apps/sanmei-cli/src/sanmei_cli/formatters/text.py apps/sanmei-cli/tests/test_text_formatter.py apps/sanmei-cli/tests/conftest.py
git commit -m "feat(sanmei-cli): add format_taiun_shiki() text formatter"
```

---

### Task 7: CLI command — sanmei taiun-shiki

**Files:**
- Create: `apps/sanmei-cli/src/sanmei_cli/commands/taiun_shiki.py`
- Modify: `apps/sanmei-cli/src/sanmei_cli/main.py` (add import)
- Create: `apps/sanmei-cli/tests/test_taiun_shiki_cmd.py`

**Step 1: Write the failing test**

```python
# apps/sanmei-cli/tests/test_taiun_shiki_cmd.py
"""taiun-shiki サブコマンドのテスト."""

import json

from click.testing import CliRunner

from sanmei_cli.main import cli


class TestTaiunShikiCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_basic(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15", "--gender", "m"])
        assert result.exit_code == 0
        assert "=== 大運四季表 ===" in result.output

    def test_contains_column_headers(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15", "--gender", "m"])
        assert "季節" in result.output
        assert "サイクル" in result.output

    def test_contains_month_kanshi(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15", "--gender", "m"])
        assert "月干支" in result.output

    def test_contains_period_labels(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15", "--gender", "m"])
        assert "第1句" in result.output

    def test_female(self):
        result = self.runner.invoke(
            cli, ["taiun-shiki", "2000-01-15", "--gender", "female"]
        )
        assert result.exit_code == 0

    def test_json_output(self):
        result = self.runner.invoke(
            cli, ["--json", "taiun-shiki", "2000-01-15", "--gender", "男"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "direction" in data
        assert "entries" in data

    def test_missing_gender(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "2000-01-15"])
        assert result.exit_code != 0

    def test_custom_periods(self):
        result = self.runner.invoke(
            cli, ["taiun-shiki", "2000-01-15", "--gender", "m", "--periods", "5"]
        )
        assert result.exit_code == 0

    def test_help(self):
        result = self.runner.invoke(cli, ["taiun-shiki", "--help"])
        assert result.exit_code == 0
        assert "--gender" in result.output
```

**Step 2: Run test to verify it fails**

Run: `cd apps/sanmei-cli && uv run pytest tests/test_taiun_shiki_cmd.py -v`
Expected: FAIL (command not found)

**Step 3: Write minimal implementation**

```python
# apps/sanmei-cli/src/sanmei_cli/commands/taiun_shiki.py
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
```

Add import to `apps/sanmei-cli/src/sanmei_cli/main.py`:

```python
import sanmei_cli.commands.taiun_shiki as _taiun_shiki_cmd  # noqa: E402, F401
```

**Step 4: Run test to verify it passes**

Run: `cd apps/sanmei-cli && uv run pytest tests/test_taiun_shiki_cmd.py -v`
Expected: PASS (all 9 tests)

**Step 5: Commit**

```bash
git add apps/sanmei-cli/src/sanmei_cli/commands/taiun_shiki.py apps/sanmei-cli/src/sanmei_cli/main.py apps/sanmei-cli/tests/test_taiun_shiki_cmd.py
git commit -m "feat(sanmei-cli): add taiun-shiki subcommand for 大運四季表"
```

---

### Task 8: Full quality check and verification

**Files:** None (verification only)

**Step 1: Run full test suite**

Run: `just test`
Expected: ALL PASS

**Step 2: Run lint**

Run: `just lint`
Expected: No errors

**Step 3: Run typecheck**

Run: `just typecheck`
Expected: No errors

**Step 4: Run full quality check**

Run: `just check`
Expected: ALL PASS

**Step 5: Manual smoke test**

Run: `cd apps/sanmei-cli && uv run sanmei taiun-shiki 1990-05-15 --gender 男 --time 14:30`

Verify the output looks like:
```
=== 大運四季表 ===
方向: ...  立運: N歳

季節  年齢      大運      干支    蔵干        十大主星  十二大従星  サイクル
...   0-N歳    月干支    XX      ...         ...       ...         ...
...   N-N歳    第1句     XX      ...         ...       ...         ...
...
```

**Step 6: Fix any issues found, re-run `just check`**

**Step 7: Commit any fixes**

```bash
git commit -m "fix(sanmei-core): address quality check issues for taiun-shiki"
```
