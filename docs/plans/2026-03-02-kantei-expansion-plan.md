# 鑑定機能拡充 実装計画

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** sanmei-core に宿命中殺・五行バランス・位相法（合冲刑害）・大運・年運の4モジュールを追加し、鑑定機能を完成させる。

**Architecture:** 拡張 Meishiki + 独立 Fortune。命式の本質情報（宿命中殺、五行バランス）は Meishiki に統合。位相法は共有モジュール。大運・年運は独立した Fortune モジュール。

**Tech Stack:** Python 3.14+, pydantic 2.10+, pytest, ruff strict, mypy strict

**Design doc:** `docs/plans/2026-03-02-kantei-expansion-design.md`

**Domain knowledge:** `docs/domain/` 配下（特に Ch.6: 中殺、Ch.8: 合冲刑害、Ch.9: 鑑定技法、Ch.11: 応用概念）

**Test command:** `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v`

**Lint/type command:** `just lint && just typecheck`

---

### Task 1: 宿命中殺ドメインモデル

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/shukumei_chuusatsu.py`
- Test: `packages/sanmei-core/tests/unit/domain/test_shukumei_chuusatsu.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/domain/test_shukumei_chuusatsu.py
"""宿命中殺ドメインモデルのテスト."""

from __future__ import annotations

from sanmei_core.domain.shukumei_chuusatsu import (
    ShukumeiChuusatsu,
    ShukumeiChuusatsuPosition,
)


class TestShukumeiChuusatsuPosition:
    def test_has_five_positions(self) -> None:
        assert len(ShukumeiChuusatsuPosition) == 5

    def test_year_branch(self) -> None:
        assert ShukumeiChuusatsuPosition.YEAR_BRANCH.value == "年支中殺"

    def test_month_branch(self) -> None:
        assert ShukumeiChuusatsuPosition.MONTH_BRANCH.value == "月支中殺"

    def test_day_branch(self) -> None:
        assert ShukumeiChuusatsuPosition.DAY_BRANCH.value == "日支中殺"

    def test_year_stem(self) -> None:
        assert ShukumeiChuusatsuPosition.YEAR_STEM.value == "年干中殺"

    def test_month_stem(self) -> None:
        assert ShukumeiChuusatsuPosition.MONTH_STEM.value == "月干中殺"


class TestShukumeiChuusatsu:
    def test_creation(self) -> None:
        sc = ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.DAY_BRANCH)
        assert sc.position == ShukumeiChuusatsuPosition.DAY_BRANCH

    def test_frozen(self) -> None:
        sc = ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.YEAR_BRANCH)
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            sc.position = ShukumeiChuusatsuPosition.MONTH_BRANCH  # type: ignore[misc]
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_shukumei_chuusatsu.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/shukumei_chuusatsu.py
"""宿命中殺（しゅくめいちゅうさつ）のドメインモデル."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ShukumeiChuusatsuPosition(Enum):
    """宿命中殺が当たる位置."""

    YEAR_BRANCH = "年支中殺"
    MONTH_BRANCH = "月支中殺"
    DAY_BRANCH = "日支中殺"
    YEAR_STEM = "年干中殺"
    MONTH_STEM = "月干中殺"


class ShukumeiChuusatsu(BaseModel, frozen=True):
    """宿命中殺."""

    position: ShukumeiChuusatsuPosition
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_shukumei_chuusatsu.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add ShukumeiChuusatsu domain model
```

---

### Task 2: 宿命中殺算出ロジック

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/shukumei_chuusatsu.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_shukumei_chuusatsu.py`

**Context:** 天中殺の2支が、命式の年支/月支/日支に含まれていれば宿命中殺。天干中殺は、対応する地支が天中殺支の場合にのみ発生する（年干は年支が中殺の場合、月干は月支が中殺の場合）。日干は中殺されない（日柱は天中殺の算出元なので日干中殺は存在しない）。

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_shukumei_chuusatsu.py
"""宿命中殺算出のテスト."""

from __future__ import annotations

import pytest
from sanmei_core.calculators.shukumei_chuusatsu import calculate_shukumei_chuusatsu
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.shukumei_chuusatsu import ShukumeiChuusatsuPosition
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType


def _make_pillars(
    year_branch: TwelveBranch,
    month_branch: TwelveBranch,
    day_branch: TwelveBranch,
) -> ThreePillars:
    """テスト用三柱を作成（stemは適当）."""
    return ThreePillars(
        year=Kanshi(stem=TenStem.KINOE, branch=year_branch, index=0),
        month=Kanshi(stem=TenStem.KINOTO, branch=month_branch, index=1),
        day=Kanshi(stem=TenStem.HINOE, branch=day_branch, index=2),
    )


class TestCalculateShukumeiChuusatsu:
    def test_no_shukumei_chuusatsu(self) -> None:
        """三柱のどの地支も天中殺支に含まれない → 空リスト."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        )
        pillars = _make_pillars(TwelveBranch.NE, TwelveBranch.TORA, TwelveBranch.UMA)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        assert result == []

    def test_year_branch_chuusatsu(self) -> None:
        """年支が天中殺支 → 年支中殺 + 年干中殺."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        )
        pillars = _make_pillars(TwelveBranch.INU, TwelveBranch.TORA, TwelveBranch.UMA)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        positions = {sc.position for sc in result}
        assert ShukumeiChuusatsuPosition.YEAR_BRANCH in positions
        assert ShukumeiChuusatsuPosition.YEAR_STEM in positions

    def test_month_branch_chuusatsu(self) -> None:
        """月支が天中殺支 → 月支中殺 + 月干中殺."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.TORA_U,
            branches=(TwelveBranch.TORA, TwelveBranch.U),
        )
        pillars = _make_pillars(TwelveBranch.NE, TwelveBranch.U, TwelveBranch.UMA)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        positions = {sc.position for sc in result}
        assert ShukumeiChuusatsuPosition.MONTH_BRANCH in positions
        assert ShukumeiChuusatsuPosition.MONTH_STEM in positions

    def test_day_branch_chuusatsu(self) -> None:
        """日支が天中殺支 → 日支中殺のみ（日干中殺は存在しない）."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.NE_USHI,
            branches=(TwelveBranch.NE, TwelveBranch.USHI),
        )
        pillars = _make_pillars(TwelveBranch.TORA, TwelveBranch.UMA, TwelveBranch.NE)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        positions = {sc.position for sc in result}
        assert ShukumeiChuusatsuPosition.DAY_BRANCH in positions
        assert ShukumeiChuusatsuPosition.YEAR_STEM not in positions
        assert ShukumeiChuusatsuPosition.MONTH_STEM not in positions

    def test_multiple_positions(self) -> None:
        """複数の柱が天中殺支に当たる場合."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.NE_USHI,
            branches=(TwelveBranch.NE, TwelveBranch.USHI),
        )
        pillars = _make_pillars(TwelveBranch.NE, TwelveBranch.USHI, TwelveBranch.NE)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        positions = {sc.position for sc in result}
        assert ShukumeiChuusatsuPosition.YEAR_BRANCH in positions
        assert ShukumeiChuusatsuPosition.YEAR_STEM in positions
        assert ShukumeiChuusatsuPosition.MONTH_BRANCH in positions
        assert ShukumeiChuusatsuPosition.MONTH_STEM in positions
        assert ShukumeiChuusatsuPosition.DAY_BRANCH in positions

    @pytest.mark.parametrize(
        "tc_type",
        list(TenchuusatsuType),
    )
    def test_returns_list_for_all_tenchuusatsu_types(
        self, tc_type: TenchuusatsuType
    ) -> None:
        """全天中殺タイプで正常にリストを返す."""
        from sanmei_core.calculators.tenchuusatsu import _GROUP_MAP

        branches = next(b for t, b in _GROUP_MAP if t == tc_type)
        tc = Tenchuusatsu(type=tc_type, branches=branches)
        pillars = _make_pillars(TwelveBranch.TORA, TwelveBranch.UMA, TwelveBranch.TORI)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        assert isinstance(result, list)
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_shukumei_chuusatsu.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/shukumei_chuusatsu.py
"""宿命中殺の算出."""

from __future__ import annotations

from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.shukumei_chuusatsu import (
    ShukumeiChuusatsu,
    ShukumeiChuusatsuPosition,
)
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu


def calculate_shukumei_chuusatsu(
    pillars: ThreePillars,
    tenchuusatsu: Tenchuusatsu,
) -> list[ShukumeiChuusatsu]:
    """三柱と天中殺から宿命中殺を判定.

    判定ルール:
    - 年支/月支/日支が天中殺の2支に含まれれば → 支の中殺
    - 年柱/月柱の地支が天中殺支であれば → その天干も中殺
    - 日干中殺は存在しない（日柱が天中殺の算出元）
    """
    tc_branches = set(tenchuusatsu.branches)
    result: list[ShukumeiChuusatsu] = []

    if pillars.year.branch in tc_branches:
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.YEAR_BRANCH))
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.YEAR_STEM))

    if pillars.month.branch in tc_branches:
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.MONTH_BRANCH))
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.MONTH_STEM))

    if pillars.day.branch in tc_branches:
        result.append(ShukumeiChuusatsu(position=ShukumeiChuusatsuPosition.DAY_BRANCH))

    return result
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_shukumei_chuusatsu.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add shukumei chuusatsu calculator
```

---

### Task 3: Meishiki 拡張（宿命中殺の統合）

**Files:**
- Modify: `packages/sanmei-core/src/sanmei_core/domain/meishiki.py`
- Modify: `packages/sanmei-core/src/sanmei_core/calculators/meishiki_calculator.py`
- Modify: `packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py`

**Step 1: Write the failing test**

Add to existing test file:

```python
# Add to packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py

    def test_meishiki_has_shukumei_chuusatsu(self) -> None:
        """命式に宿命中殺フィールドが含まれる."""
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        assert isinstance(meishiki.shukumei_chuusatsu, tuple)
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py::TestMeishikiCalculator::test_meishiki_has_shukumei_chuusatsu -v`
Expected: FAIL with `AttributeError`

**Step 3: Update implementation**

Update `packages/sanmei-core/src/sanmei_core/domain/meishiki.py`:

```python
"""命式（めいしき）の複合ドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.shukumei_chuusatsu import ShukumeiChuusatsu
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
    shukumei_chuusatsu: tuple[ShukumeiChuusatsu, ...]
```

Update `packages/sanmei-core/src/sanmei_core/calculators/meishiki_calculator.py`:

```python
"""MeishikiCalculator — 命式算出の統合ファサード."""

from __future__ import annotations

from datetime import datetime, tzinfo

from sanmei_core.calculators.major_star import calculate_major_star_chart
from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.shukumei_chuusatsu import calculate_shukumei_chuusatsu
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
        self._calendar = SanmeiCalendar(school.get_setsuiri_provider(), tz=self._tz)

    def calculate(self, dt: datetime) -> Meishiki:
        """西暦日時から完全な命式を算出."""
        pillars = self._calendar.three_pillars(dt)
        hidden_stems = {
            "year": self._school.get_hidden_stems(pillars.year.branch),
            "month": self._school.get_hidden_stems(pillars.month.branch),
            "day": self._school.get_hidden_stems(pillars.day.branch),
        }
        major_stars = calculate_major_star_chart(pillars, hidden_stems, self._school)
        subsidiary_stars = calculate_subsidiary_star_chart(pillars, pillars.day.stem, self._school)
        tenchuusatsu = calculate_tenchuusatsu(pillars.day)
        shukumei_chuusatsu = tuple(
            calculate_shukumei_chuusatsu(pillars, tenchuusatsu)
        )
        return Meishiki(
            pillars=pillars,
            hidden_stems=hidden_stems,
            major_stars=major_stars,
            subsidiary_stars=subsidiary_stars,
            tenchuusatsu=tenchuusatsu,
            shukumei_chuusatsu=shukumei_chuusatsu,
        )
```

**Step 4: Run ALL tests to verify nothing broke**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v`
Expected: ALL PASS

**Step 5: Commit**

```
feat(sanmei-core): integrate shukumei chuusatsu into Meishiki
```

---

### Task 4: 五行バランスドメインモデル

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/gogyo_balance.py`
- Test: `packages/sanmei-core/tests/unit/domain/test_gogyo_balance.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/domain/test_gogyo_balance.py
"""五行バランスドメインモデルのテスト."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount


class TestGoGyoCount:
    def test_creation_defaults(self) -> None:
        count = GoGyoCount()
        assert count.wood == 0
        assert count.fire == 0
        assert count.earth == 0
        assert count.metal == 0
        assert count.water == 0

    def test_creation_with_values(self) -> None:
        count = GoGyoCount(wood=3, fire=1, earth=2, metal=0, water=1)
        assert count.wood == 3
        assert count.fire == 1

    def test_get(self) -> None:
        count = GoGyoCount(wood=3, fire=1, earth=2, metal=0, water=1)
        assert count.get(GoGyo.WOOD) == 3
        assert count.get(GoGyo.FIRE) == 1
        assert count.get(GoGyo.METAL) == 0

    def test_total(self) -> None:
        count = GoGyoCount(wood=3, fire=1, earth=2, metal=0, water=1)
        assert count.total == 7

    def test_total_zero(self) -> None:
        count = GoGyoCount()
        assert count.total == 0

    def test_frozen(self) -> None:
        count = GoGyoCount(wood=1)
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            count.wood = 5  # type: ignore[misc]


class TestGoGyoBalance:
    def test_creation(self) -> None:
        stem = GoGyoCount(wood=1, fire=1, earth=1)
        branch = GoGyoCount(wood=2, metal=1)
        total = GoGyoCount(wood=3, fire=1, earth=1, metal=1)
        balance = GoGyoBalance(
            stem_count=stem,
            branch_count=branch,
            total_count=total,
            dominant=GoGyo.WOOD,
            lacking=(GoGyo.WATER,),
            day_stem_gogyo=GoGyo.WOOD,
        )
        assert balance.dominant == GoGyo.WOOD
        assert GoGyo.WATER in balance.lacking
        assert balance.day_stem_gogyo == GoGyo.WOOD
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_gogyo_balance.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/gogyo_balance.py
"""五行バランスのドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel

from sanmei_core.domain.gogyo import GoGyo

_GOGYO_FIELDS = ("wood", "fire", "earth", "metal", "water")


class GoGyoCount(BaseModel, frozen=True):
    """命式中の各五行の出現数."""

    wood: int = 0
    fire: int = 0
    earth: int = 0
    metal: int = 0
    water: int = 0

    def get(self, gogyo: GoGyo) -> int:
        """GoGyo enum から対応するカウントを取得."""
        return getattr(self, _GOGYO_FIELDS[gogyo.value])

    @property
    def total(self) -> int:
        """全五行の合計."""
        return self.wood + self.fire + self.earth + self.metal + self.water


class GoGyoBalance(BaseModel, frozen=True):
    """五行バランス分析結果."""

    stem_count: GoGyoCount
    branch_count: GoGyoCount
    total_count: GoGyoCount
    dominant: GoGyo
    lacking: tuple[GoGyo, ...]
    day_stem_gogyo: GoGyo
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_gogyo_balance.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add GoGyoBalance domain model
```

---

### Task 5: 五行バランス算出ロジック

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/gogyo_balance.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_gogyo_balance.py`

**Context:** 天干3本の五行 + 蔵干（各地支の本気・中気・余気）の五行をカウント。STEM_TO_GOGYO テーブル（`tables/gogyo.py`）を使用。蔵干は `HiddenStems` の `main`, `middle`, `minor` から取得。

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_gogyo_balance.py
"""五行バランス算出のテスト."""

from __future__ import annotations

from sanmei_core.calculators.gogyo_balance import calculate_gogyo_balance
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars


def _make_pillars(
    year_stem: TenStem,
    month_stem: TenStem,
    day_stem: TenStem,
) -> ThreePillars:
    return ThreePillars(
        year=Kanshi(stem=year_stem, branch=TwelveBranch.NE, index=0),
        month=Kanshi(stem=month_stem, branch=TwelveBranch.NE, index=0),
        day=Kanshi(stem=day_stem, branch=TwelveBranch.NE, index=0),
    )


class TestCalculateGogyoBalance:
    def test_stem_count_all_wood(self) -> None:
        """天干が全て木（甲甲甲）の場合、stem_count.wood == 3."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.KINOE, TenStem.KINOE)
        hidden = {
            "year": HiddenStems(main=TenStem.MIZUNOTO),
            "month": HiddenStems(main=TenStem.MIZUNOTO),
            "day": HiddenStems(main=TenStem.MIZUNOTO),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.stem_count.wood == 3
        assert balance.stem_count.fire == 0

    def test_branch_count_includes_hidden_stems(self) -> None:
        """蔵干の本気・中気・余気が全てカウントされる."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.KINOE, TenStem.KINOE)
        # 寅の蔵干: 甲(木), 丙(火), 戊(土)
        hidden = {
            "year": HiddenStems(main=TenStem.KINOE, middle=TenStem.HINOE, minor=TenStem.TSUCHINOE),
            "month": HiddenStems(main=TenStem.KINOE),
            "day": HiddenStems(main=TenStem.MIZUNOTO),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.branch_count.wood == 2  # 甲 + 甲
        assert balance.branch_count.fire == 1  # 丙
        assert balance.branch_count.earth == 1  # 戊
        assert balance.branch_count.water == 1  # 癸

    def test_total_count_is_sum(self) -> None:
        """total_count は stem_count + branch_count."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.HINOE, TenStem.KANOE)
        hidden = {
            "year": HiddenStems(main=TenStem.MIZUNOTO),
            "month": HiddenStems(main=TenStem.MIZUNOTO),
            "day": HiddenStems(main=TenStem.MIZUNOTO),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.total_count.wood == balance.stem_count.wood + balance.branch_count.wood
        assert balance.total_count.fire == balance.stem_count.fire + balance.branch_count.fire
        assert balance.total_count.total == balance.stem_count.total + balance.branch_count.total

    def test_dominant_is_highest(self) -> None:
        """dominant は最も多い五行."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.KINOTO, TenStem.KINOE)
        hidden = {
            "year": HiddenStems(main=TenStem.KINOE),
            "month": HiddenStems(main=TenStem.KINOE),
            "day": HiddenStems(main=TenStem.KINOE),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.dominant == GoGyo.WOOD

    def test_lacking_identifies_missing(self) -> None:
        """lacking は不在の五行を列挙."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.KINOTO, TenStem.KINOE)
        hidden = {
            "year": HiddenStems(main=TenStem.KINOE),
            "month": HiddenStems(main=TenStem.KINOE),
            "day": HiddenStems(main=TenStem.KINOE),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        lacking = set(balance.lacking)
        assert GoGyo.FIRE in lacking
        assert GoGyo.EARTH in lacking
        assert GoGyo.METAL in lacking
        assert GoGyo.WATER in lacking

    def test_day_stem_gogyo(self) -> None:
        """day_stem_gogyo は日干の五行."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.HINOE, TenStem.MIZUNOE)
        hidden = {
            "year": HiddenStems(main=TenStem.KINOE),
            "month": HiddenStems(main=TenStem.KINOE),
            "day": HiddenStems(main=TenStem.KINOE),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.day_stem_gogyo == GoGyo.WATER
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_gogyo_balance.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/gogyo_balance.py
"""五行バランスの算出."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.tables.gogyo import STEM_TO_GOGYO


def _count_stems(stems: list[TenStem]) -> GoGyoCount:
    """十干リストから五行カウントを算出."""
    counts = {g: 0 for g in GoGyo}
    for stem in stems:
        counts[STEM_TO_GOGYO[stem]] += 1
    return GoGyoCount(
        wood=counts[GoGyo.WOOD],
        fire=counts[GoGyo.FIRE],
        earth=counts[GoGyo.EARTH],
        metal=counts[GoGyo.METAL],
        water=counts[GoGyo.WATER],
    )


def _collect_hidden_stems(hidden_stems: dict[str, HiddenStems]) -> list[TenStem]:
    """蔵干から全ての十干を収集."""
    result: list[TenStem] = []
    for hs in hidden_stems.values():
        result.append(hs.main)
        if hs.middle is not None:
            result.append(hs.middle)
        if hs.minor is not None:
            result.append(hs.minor)
    return result


def _add_counts(a: GoGyoCount, b: GoGyoCount) -> GoGyoCount:
    return GoGyoCount(
        wood=a.wood + b.wood,
        fire=a.fire + b.fire,
        earth=a.earth + b.earth,
        metal=a.metal + b.metal,
        water=a.water + b.water,
    )


def calculate_gogyo_balance(
    pillars: ThreePillars,
    hidden_stems: dict[str, HiddenStems],
) -> GoGyoBalance:
    """三柱と蔵干から五行バランスを算出."""
    stem_list = [pillars.year.stem, pillars.month.stem, pillars.day.stem]
    stem_count = _count_stems(stem_list)

    branch_stems = _collect_hidden_stems(hidden_stems)
    branch_count = _count_stems(branch_stems)

    total_count = _add_counts(stem_count, branch_count)

    # dominant: 最多の五行（同数の場合は GoGyo の定義順で最初）
    dominant = max(GoGyo, key=lambda g: total_count.get(g))

    # lacking: カウント0の五行
    lacking = tuple(g for g in GoGyo if total_count.get(g) == 0)

    day_stem_gogyo = STEM_TO_GOGYO[pillars.day.stem]

    return GoGyoBalance(
        stem_count=stem_count,
        branch_count=branch_count,
        total_count=total_count,
        dominant=dominant,
        lacking=lacking,
        day_stem_gogyo=day_stem_gogyo,
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_gogyo_balance.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add gogyo balance calculator
```

---

### Task 6: Meishiki 拡張（五行バランスの統合）

**Files:**
- Modify: `packages/sanmei-core/src/sanmei_core/domain/meishiki.py`
- Modify: `packages/sanmei-core/src/sanmei_core/calculators/meishiki_calculator.py`
- Modify: `packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py`

**Step 1: Write the failing test**

Add to existing test file:

```python
# Add to packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py

    def test_meishiki_has_gogyo_balance(self) -> None:
        """命式に五行バランスフィールドが含まれる."""
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        assert meishiki.gogyo_balance is not None
        assert meishiki.gogyo_balance.total_count.total > 0
        assert meishiki.gogyo_balance.day_stem_gogyo is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_meishiki_calculator.py::TestMeishikiCalculator::test_meishiki_has_gogyo_balance -v`
Expected: FAIL with `AttributeError`

**Step 3: Update implementation**

Add to `domain/meishiki.py` imports and field:

```python
# Add import
from sanmei_core.domain.gogyo_balance import GoGyoBalance

# Add field to Meishiki class:
    gogyo_balance: GoGyoBalance
```

Update `calculators/meishiki_calculator.py`:

```python
# Add import
from sanmei_core.calculators.gogyo_balance import calculate_gogyo_balance

# In calculate() method, after shukumei_chuusatsu calculation, add:
        gogyo_balance = calculate_gogyo_balance(pillars, hidden_stems)

# Add to Meishiki constructor:
            gogyo_balance=gogyo_balance,
```

**Step 4: Run ALL tests**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v`
Expected: ALL PASS

**Step 5: Commit**

```
feat(sanmei-core): integrate gogyo balance into Meishiki
```

---

### Task 7: 位相法ドメインモデル

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/isouhou.py`
- Test: `packages/sanmei-core/tests/unit/domain/test_isouhou.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/domain/test_isouhou.py
"""位相法ドメインモデルのテスト."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.isouhou import (
    BranchInteraction,
    BranchInteractionType,
    IsouhouResult,
    StemInteraction,
    StemInteractionType,
)
from sanmei_core.domain.kanshi import TenStem, TwelveBranch


class TestStemInteractionType:
    def test_gou(self) -> None:
        assert StemInteractionType.GOU.value == "合"


class TestBranchInteractionType:
    def test_all_types(self) -> None:
        assert len(BranchInteractionType) == 6
        assert BranchInteractionType.RIKUGOU.value == "六合"
        assert BranchInteractionType.SANGOU.value == "三合局"
        assert BranchInteractionType.ROKUCHUU.value == "六冲"
        assert BranchInteractionType.KEI.value == "刑"
        assert BranchInteractionType.JIKEI.value == "自刑"
        assert BranchInteractionType.RIKUGAI.value == "六害"


class TestStemInteraction:
    def test_creation(self) -> None:
        si = StemInteraction(
            type=StemInteractionType.GOU,
            stems=(TenStem.KINOE, TenStem.TSUCHINOTO),
            result_gogyo=GoGyo.EARTH,
        )
        assert si.type == StemInteractionType.GOU
        assert si.stems == (TenStem.KINOE, TenStem.TSUCHINOTO)
        assert si.result_gogyo == GoGyo.EARTH


class TestBranchInteraction:
    def test_creation_with_gogyo(self) -> None:
        bi = BranchInteraction(
            type=BranchInteractionType.RIKUGOU,
            branches=(TwelveBranch.NE, TwelveBranch.USHI),
            result_gogyo=GoGyo.EARTH,
        )
        assert bi.result_gogyo == GoGyo.EARTH

    def test_creation_without_gogyo(self) -> None:
        bi = BranchInteraction(
            type=BranchInteractionType.ROKUCHUU,
            branches=(TwelveBranch.NE, TwelveBranch.UMA),
            result_gogyo=None,
        )
        assert bi.result_gogyo is None

    def test_three_branches_for_sangou(self) -> None:
        bi = BranchInteraction(
            type=BranchInteractionType.SANGOU,
            branches=(TwelveBranch.I, TwelveBranch.U, TwelveBranch.HITSUJI),
            result_gogyo=GoGyo.WOOD,
        )
        assert len(bi.branches) == 3


class TestIsouhouResult:
    def test_empty(self) -> None:
        result = IsouhouResult(stem_interactions=(), branch_interactions=())
        assert len(result.stem_interactions) == 0
        assert len(result.branch_interactions) == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_isouhou.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/isouhou.py
"""位相法（いそうほう）のドメインモデル."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.kanshi import TenStem, TwelveBranch


class StemInteractionType(Enum):
    """十干の相互作用."""

    GOU = "合"


class BranchInteractionType(Enum):
    """十二支の相互作用."""

    RIKUGOU = "六合"
    SANGOU = "三合局"
    ROKUCHUU = "六冲"
    KEI = "刑"
    JIKEI = "自刑"
    RIKUGAI = "六害"


class StemInteraction(BaseModel, frozen=True):
    """十干の相互作用結果."""

    type: StemInteractionType
    stems: tuple[TenStem, TenStem]
    result_gogyo: GoGyo


class BranchInteraction(BaseModel, frozen=True):
    """十二支の相互作用結果."""

    type: BranchInteractionType
    branches: tuple[TwelveBranch, ...]
    result_gogyo: GoGyo | None


class IsouhouResult(BaseModel, frozen=True):
    """位相法の分析結果."""

    stem_interactions: tuple[StemInteraction, ...]
    branch_interactions: tuple[BranchInteraction, ...]
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_isouhou.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add isouhou domain model
```

---

### Task 8: 位相法テーブル

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/tables/isouhou.py`
- Test: `packages/sanmei-core/tests/unit/tables/test_isouhou.py`

**Context:** Ch.8 のデータを全てテーブルに実装。テストでテーブル値を全件検証する。

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/tables/test_isouhou.py
"""位相法テーブルのテスト."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.tables.isouhou import (
    JIKEI,
    RIKUGAI,
    RIKUGOU,
    ROKUCHUU,
    SANGOU,
    SANKEI,
    STEM_GOU,
)


class TestStemGou:
    def test_has_5_pairs(self) -> None:
        assert len(STEM_GOU) == 5

    def test_kinoe_tsuchinoto_earth(self) -> None:
        """甲・己 → 土."""
        assert STEM_GOU[frozenset({TenStem.KINOE, TenStem.TSUCHINOTO})] == GoGyo.EARTH

    def test_kinoto_kanoe_metal(self) -> None:
        """乙・庚 → 金."""
        assert STEM_GOU[frozenset({TenStem.KINOTO, TenStem.KANOE})] == GoGyo.METAL

    def test_hinoe_kanoto_water(self) -> None:
        """丙・辛 → 水."""
        assert STEM_GOU[frozenset({TenStem.HINOE, TenStem.KANOTO})] == GoGyo.WATER

    def test_hinoto_mizunoe_wood(self) -> None:
        """丁・壬 → 木."""
        assert STEM_GOU[frozenset({TenStem.HINOTO, TenStem.MIZUNOE})] == GoGyo.WOOD

    def test_tsuchinoe_mizunoto_fire(self) -> None:
        """戊・癸 → 火."""
        assert STEM_GOU[frozenset({TenStem.TSUCHINOE, TenStem.MIZUNOTO})] == GoGyo.FIRE


class TestRikugou:
    def test_has_6_pairs(self) -> None:
        assert len(RIKUGOU) == 6

    def test_ne_ushi_earth(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.NE, TwelveBranch.USHI})] == GoGyo.EARTH

    def test_tora_i_wood(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.TORA, TwelveBranch.I})] == GoGyo.WOOD

    def test_u_inu_fire(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.U, TwelveBranch.INU})] == GoGyo.FIRE

    def test_tatsu_tori_metal(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.TATSU, TwelveBranch.TORI})] == GoGyo.METAL

    def test_mi_saru_water(self) -> None:
        assert RIKUGOU[frozenset({TwelveBranch.MI, TwelveBranch.SARU})] == GoGyo.WATER

    def test_uma_hitsuji_fire(self) -> None:
        """午・未 → 火（火・土の説もあるが標準では火）."""
        assert RIKUGOU[frozenset({TwelveBranch.UMA, TwelveBranch.HITSUJI})] == GoGyo.FIRE


class TestSangou:
    def test_has_4_sets(self) -> None:
        assert len(SANGOU) == 4

    def test_wood_i_u_hitsuji(self) -> None:
        wood_set = next(
            (s, g) for s, g in SANGOU if g == GoGyo.WOOD
        )
        assert wood_set[0] == frozenset({TwelveBranch.I, TwelveBranch.U, TwelveBranch.HITSUJI})

    def test_fire_tora_uma_inu(self) -> None:
        fire_set = next(
            (s, g) for s, g in SANGOU if g == GoGyo.FIRE
        )
        assert fire_set[0] == frozenset({TwelveBranch.TORA, TwelveBranch.UMA, TwelveBranch.INU})

    def test_metal_mi_tori_ushi(self) -> None:
        metal_set = next(
            (s, g) for s, g in SANGOU if g == GoGyo.METAL
        )
        assert metal_set[0] == frozenset({TwelveBranch.MI, TwelveBranch.TORI, TwelveBranch.USHI})

    def test_water_saru_ne_tatsu(self) -> None:
        water_set = next(
            (s, g) for s, g in SANGOU if g == GoGyo.WATER
        )
        assert water_set[0] == frozenset({TwelveBranch.SARU, TwelveBranch.NE, TwelveBranch.TATSU})


class TestRokuchuu:
    def test_has_6_pairs(self) -> None:
        assert len(ROKUCHUU) == 6

    def test_ne_uma(self) -> None:
        assert frozenset({TwelveBranch.NE, TwelveBranch.UMA}) in ROKUCHUU

    def test_ushi_hitsuji(self) -> None:
        assert frozenset({TwelveBranch.USHI, TwelveBranch.HITSUJI}) in ROKUCHUU

    def test_tora_saru(self) -> None:
        assert frozenset({TwelveBranch.TORA, TwelveBranch.SARU}) in ROKUCHUU

    def test_u_tori(self) -> None:
        assert frozenset({TwelveBranch.U, TwelveBranch.TORI}) in ROKUCHUU

    def test_tatsu_inu(self) -> None:
        assert frozenset({TwelveBranch.TATSU, TwelveBranch.INU}) in ROKUCHUU

    def test_mi_i(self) -> None:
        assert frozenset({TwelveBranch.MI, TwelveBranch.I}) in ROKUCHUU


class TestSankei:
    def test_has_2_groups(self) -> None:
        assert len(SANKEI) == 2

    def test_tora_mi_saru(self) -> None:
        assert frozenset({TwelveBranch.TORA, TwelveBranch.MI, TwelveBranch.SARU}) in SANKEI

    def test_ushi_inu_hitsuji(self) -> None:
        assert frozenset({TwelveBranch.USHI, TwelveBranch.INU, TwelveBranch.HITSUJI}) in SANKEI


class TestJikei:
    def test_has_4_branches(self) -> None:
        assert len(JIKEI) == 4

    def test_members(self) -> None:
        assert TwelveBranch.TATSU in JIKEI
        assert TwelveBranch.UMA in JIKEI
        assert TwelveBranch.TORI in JIKEI
        assert TwelveBranch.I in JIKEI


class TestRikugai:
    def test_has_6_pairs(self) -> None:
        assert len(RIKUGAI) == 6

    def test_ne_hitsuji(self) -> None:
        assert frozenset({TwelveBranch.NE, TwelveBranch.HITSUJI}) in RIKUGAI

    def test_ushi_uma(self) -> None:
        assert frozenset({TwelveBranch.USHI, TwelveBranch.UMA}) in RIKUGAI

    def test_tora_mi(self) -> None:
        assert frozenset({TwelveBranch.TORA, TwelveBranch.MI}) in RIKUGAI

    def test_u_tatsu(self) -> None:
        assert frozenset({TwelveBranch.U, TwelveBranch.TATSU}) in RIKUGAI

    def test_saru_i(self) -> None:
        assert frozenset({TwelveBranch.SARU, TwelveBranch.I}) in RIKUGAI

    def test_tori_inu(self) -> None:
        assert frozenset({TwelveBranch.TORI, TwelveBranch.INU}) in RIKUGAI
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/tables/test_isouhou.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/tables/isouhou.py
"""位相法テーブル（合・冲・刑・害）.

docs/domain/08_Chapter8_Gou_Chuu_Kei_Gai.md 準拠。
"""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

# --- 十干合 ---
STEM_GOU: dict[frozenset[TenStem], GoGyo] = {
    frozenset({TenStem.KINOE, TenStem.TSUCHINOTO}): GoGyo.EARTH,
    frozenset({TenStem.KINOTO, TenStem.KANOE}): GoGyo.METAL,
    frozenset({TenStem.HINOE, TenStem.KANOTO}): GoGyo.WATER,
    frozenset({TenStem.HINOTO, TenStem.MIZUNOE}): GoGyo.WOOD,
    frozenset({TenStem.TSUCHINOE, TenStem.MIZUNOTO}): GoGyo.FIRE,
}

# --- 六合 ---
RIKUGOU: dict[frozenset[TwelveBranch], GoGyo] = {
    frozenset({TwelveBranch.NE, TwelveBranch.USHI}): GoGyo.EARTH,
    frozenset({TwelveBranch.TORA, TwelveBranch.I}): GoGyo.WOOD,
    frozenset({TwelveBranch.U, TwelveBranch.INU}): GoGyo.FIRE,
    frozenset({TwelveBranch.TATSU, TwelveBranch.TORI}): GoGyo.METAL,
    frozenset({TwelveBranch.MI, TwelveBranch.SARU}): GoGyo.WATER,
    frozenset({TwelveBranch.UMA, TwelveBranch.HITSUJI}): GoGyo.FIRE,
}

# --- 三合局 ---
SANGOU: list[tuple[frozenset[TwelveBranch], GoGyo]] = [
    (frozenset({TwelveBranch.I, TwelveBranch.U, TwelveBranch.HITSUJI}), GoGyo.WOOD),
    (frozenset({TwelveBranch.TORA, TwelveBranch.UMA, TwelveBranch.INU}), GoGyo.FIRE),
    (frozenset({TwelveBranch.MI, TwelveBranch.TORI, TwelveBranch.USHI}), GoGyo.METAL),
    (frozenset({TwelveBranch.SARU, TwelveBranch.NE, TwelveBranch.TATSU}), GoGyo.WATER),
]

# --- 六冲 ---
ROKUCHUU: set[frozenset[TwelveBranch]] = {
    frozenset({TwelveBranch.NE, TwelveBranch.UMA}),
    frozenset({TwelveBranch.USHI, TwelveBranch.HITSUJI}),
    frozenset({TwelveBranch.TORA, TwelveBranch.SARU}),
    frozenset({TwelveBranch.U, TwelveBranch.TORI}),
    frozenset({TwelveBranch.TATSU, TwelveBranch.INU}),
    frozenset({TwelveBranch.MI, TwelveBranch.I}),
}

# --- 三刑 ---
SANKEI: list[frozenset[TwelveBranch]] = [
    frozenset({TwelveBranch.TORA, TwelveBranch.MI, TwelveBranch.SARU}),
    frozenset({TwelveBranch.USHI, TwelveBranch.INU, TwelveBranch.HITSUJI}),
]

# --- 自刑 ---
JIKEI: set[TwelveBranch] = {
    TwelveBranch.TATSU,
    TwelveBranch.UMA,
    TwelveBranch.TORI,
    TwelveBranch.I,
}

# --- 六害 ---
RIKUGAI: set[frozenset[TwelveBranch]] = {
    frozenset({TwelveBranch.NE, TwelveBranch.HITSUJI}),
    frozenset({TwelveBranch.USHI, TwelveBranch.UMA}),
    frozenset({TwelveBranch.TORA, TwelveBranch.MI}),
    frozenset({TwelveBranch.U, TwelveBranch.TATSU}),
    frozenset({TwelveBranch.SARU, TwelveBranch.I}),
    frozenset({TwelveBranch.TORI, TwelveBranch.INU}),
}
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/tables/test_isouhou.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add isouhou lookup tables
```

---

### Task 9: 位相法算出ロジック

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/isouhou.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_isouhou.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_isouhou.py
"""位相法算出のテスト."""

from __future__ import annotations

from sanmei_core.calculators.isouhou import (
    analyze_branch_interactions,
    analyze_isouhou,
    analyze_stem_interactions,
)
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.isouhou import BranchInteractionType, StemInteractionType
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars


class TestAnalyzeStemInteractions:
    def test_gou_detected(self) -> None:
        """甲・己 → 合（土）."""
        result = analyze_stem_interactions([TenStem.KINOE, TenStem.TSUCHINOTO])
        assert len(result) == 1
        assert result[0].type == StemInteractionType.GOU
        assert result[0].result_gogyo == GoGyo.EARTH

    def test_no_gou(self) -> None:
        """合にならない組み合わせ."""
        result = analyze_stem_interactions([TenStem.KINOE, TenStem.HINOE])
        assert len(result) == 0

    def test_multiple_stems(self) -> None:
        """3天干の場合、全ペアを検査."""
        # 甲・己・庚 → 甲己合(土) + 乙庚合は発生しない（乙ではなく甲）
        result = analyze_stem_interactions(
            [TenStem.KINOE, TenStem.TSUCHINOTO, TenStem.KANOE]
        )
        assert len(result) == 1  # 甲己合のみ


class TestAnalyzeBranchInteractions:
    def test_rikugou_detected(self) -> None:
        """子・丑 → 六合（土）."""
        result = analyze_branch_interactions([TwelveBranch.NE, TwelveBranch.USHI])
        types = {i.type for i in result}
        assert BranchInteractionType.RIKUGOU in types

    def test_rokuchuu_detected(self) -> None:
        """子・午 → 六冲."""
        result = analyze_branch_interactions([TwelveBranch.NE, TwelveBranch.UMA])
        types = {i.type for i in result}
        assert BranchInteractionType.ROKUCHUU in types

    def test_sangou_detected(self) -> None:
        """亥・卯・未 → 三合局（木）."""
        result = analyze_branch_interactions(
            [TwelveBranch.I, TwelveBranch.U, TwelveBranch.HITSUJI]
        )
        types = {i.type for i in result}
        assert BranchInteractionType.SANGOU in types
        sangou = next(i for i in result if i.type == BranchInteractionType.SANGOU)
        assert sangou.result_gogyo == GoGyo.WOOD

    def test_sankei_detected(self) -> None:
        """寅・巳・申 → 三刑."""
        result = analyze_branch_interactions(
            [TwelveBranch.TORA, TwelveBranch.MI, TwelveBranch.SARU]
        )
        types = {i.type for i in result}
        assert BranchInteractionType.KEI in types

    def test_jikei_detected(self) -> None:
        """午・午 → 自刑."""
        result = analyze_branch_interactions([TwelveBranch.UMA, TwelveBranch.UMA])
        types = {i.type for i in result}
        assert BranchInteractionType.JIKEI in types

    def test_rikugai_detected(self) -> None:
        """子・未 → 六害."""
        result = analyze_branch_interactions([TwelveBranch.NE, TwelveBranch.HITSUJI])
        types = {i.type for i in result}
        assert BranchInteractionType.RIKUGAI in types

    def test_no_interaction(self) -> None:
        """相互作用なし."""
        result = analyze_branch_interactions([TwelveBranch.NE, TwelveBranch.TORA])
        assert len(result) == 0

    def test_multiple_interactions(self) -> None:
        """同じペアで複数の相互作用が検出されうる."""
        # 丑・午 → 六害
        result = analyze_branch_interactions([TwelveBranch.USHI, TwelveBranch.UMA])
        types = {i.type for i in result}
        assert BranchInteractionType.RIKUGAI in types


class TestAnalyzeIsouhou:
    def test_basic_pillars(self) -> None:
        """三柱の位相法分析."""
        pillars = ThreePillars(
            year=Kanshi(stem=TenStem.KINOE, branch=TwelveBranch.NE, index=0),
            month=Kanshi(stem=TenStem.TSUCHINOTO, branch=TwelveBranch.UMA, index=5),
            day=Kanshi(stem=TenStem.HINOE, branch=TwelveBranch.TORA, index=2),
        )
        result = analyze_isouhou(pillars)
        # 甲・己合 → stem interaction
        stem_types = {si.type for si in result.stem_interactions}
        assert StemInteractionType.GOU in stem_types
        # 子・午冲 → branch interaction
        branch_types = {bi.type for bi in result.branch_interactions}
        assert BranchInteractionType.ROKUCHUU in branch_types

    def test_no_interactions(self) -> None:
        """相互作用のない命式."""
        pillars = ThreePillars(
            year=Kanshi(stem=TenStem.KINOE, branch=TwelveBranch.TORA, index=50),
            month=Kanshi(stem=TenStem.HINOE, branch=TwelveBranch.UMA, index=42),
            day=Kanshi(stem=TenStem.KANOE, branch=TwelveBranch.INU, index=46),
        )
        result = analyze_isouhou(pillars)
        # 甲・丙・庚 → 合なし
        assert len(result.stem_interactions) == 0
        # 寅午戌 → 三合局（火）が検出される
        branch_types = {bi.type for bi in result.branch_interactions}
        assert BranchInteractionType.SANGOU in branch_types
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_isouhou.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/isouhou.py
"""位相法（合・冲・刑・害）の判定."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations

from sanmei_core.domain.isouhou import (
    BranchInteraction,
    BranchInteractionType,
    IsouhouResult,
    StemInteraction,
    StemInteractionType,
)
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.tables.isouhou import (
    JIKEI,
    RIKUGAI,
    RIKUGOU,
    ROKUCHUU,
    SANGOU,
    SANKEI,
    STEM_GOU,
)


def analyze_stem_interactions(
    stems: Sequence[TenStem],
) -> list[StemInteraction]:
    """天干の組み合わせから合を検出."""
    result: list[StemInteraction] = []
    for a, b in combinations(stems, 2):
        key = frozenset({a, b})
        if key in STEM_GOU:
            result.append(
                StemInteraction(
                    type=StemInteractionType.GOU,
                    stems=(a, b),
                    result_gogyo=STEM_GOU[key],
                )
            )
    return result


def analyze_branch_interactions(
    branches: Sequence[TwelveBranch],
) -> list[BranchInteraction]:
    """地支の組み合わせから六合・三合・冲・刑・害を検出."""
    result: list[BranchInteraction] = []
    branch_set = frozenset(branches)

    # 六合（2支ペア）
    for a, b in combinations(branches, 2):
        key = frozenset({a, b})
        if key in RIKUGOU:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.RIKUGOU,
                    branches=(a, b),
                    result_gogyo=RIKUGOU[key],
                )
            )

    # 三合局（3支）
    for sangou_set, gogyo in SANGOU:
        if sangou_set <= branch_set:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.SANGOU,
                    branches=tuple(sangou_set),
                    result_gogyo=gogyo,
                )
            )

    # 六冲（2支ペア）
    for a, b in combinations(branches, 2):
        key = frozenset({a, b})
        if key in ROKUCHUU:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.ROKUCHUU,
                    branches=(a, b),
                    result_gogyo=None,
                )
            )

    # 三刑（3支）
    for sankei_set in SANKEI:
        if sankei_set <= branch_set:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.KEI,
                    branches=tuple(sankei_set),
                    result_gogyo=None,
                )
            )

    # 自刑（同じ支が2つ以上）
    for branch in branches:
        if branch in JIKEI and branches.count(branch) >= 2:  # type: ignore[arg-type]
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.JIKEI,
                    branches=(branch, branch),
                    result_gogyo=None,
                )
            )
            break  # 同一自刑は1回だけ

    # 六害（2支ペア）
    for a, b in combinations(branches, 2):
        key = frozenset({a, b})
        if key in RIKUGAI:
            result.append(
                BranchInteraction(
                    type=BranchInteractionType.RIKUGAI,
                    branches=(a, b),
                    result_gogyo=None,
                )
            )

    return result


def analyze_isouhou(pillars: ThreePillars) -> IsouhouResult:
    """命式の三柱に対して位相法を適用."""
    stems = [pillars.year.stem, pillars.month.stem, pillars.day.stem]
    branches = [pillars.year.branch, pillars.month.branch, pillars.day.branch]

    return IsouhouResult(
        stem_interactions=tuple(analyze_stem_interactions(stems)),
        branch_interactions=tuple(analyze_branch_interactions(branches)),
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_isouhou.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add isouhou calculator
```

---

### Task 10: 大運・年運ドメインモデル

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/domain/fortune.py`
- Test: `packages/sanmei-core/tests/unit/domain/test_fortune.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/domain/test_fortune.py
"""大運・年運ドメインモデルのテスト."""

from __future__ import annotations

from sanmei_core.domain.fortune import (
    FortuneInteraction,
    Gender,
    Nenun,
    Taiun,
    TaiunChart,
)
from sanmei_core.domain.isouhou import IsouhouResult
from sanmei_core.domain.kanshi import Kanshi


class TestGender:
    def test_male(self) -> None:
        assert Gender.MALE.value == "男"

    def test_female(self) -> None:
        assert Gender.FEMALE.value == "女"


class TestTaiun:
    def test_creation(self) -> None:
        kanshi = Kanshi.from_index(0)
        taiun = Taiun(kanshi=kanshi, start_age=3, end_age=12)
        assert taiun.kanshi == kanshi
        assert taiun.start_age == 3
        assert taiun.end_age == 12


class TestTaiunChart:
    def test_creation(self) -> None:
        periods = (
            Taiun(kanshi=Kanshi.from_index(1), start_age=3, end_age=12),
            Taiun(kanshi=Kanshi.from_index(2), start_age=13, end_age=22),
        )
        chart = TaiunChart(direction="順行", start_age=3, periods=periods)
        assert chart.direction == "順行"
        assert chart.start_age == 3
        assert len(chart.periods) == 2

    def test_reverse_direction(self) -> None:
        chart = TaiunChart(direction="逆行", start_age=7, periods=())
        assert chart.direction == "逆行"


class TestNenun:
    def test_creation(self) -> None:
        kanshi = Kanshi.from_index(40)
        nenun = Nenun(year=2024, kanshi=kanshi, age=30)
        assert nenun.year == 2024
        assert nenun.age == 30


class TestFortuneInteraction:
    def test_creation(self) -> None:
        kanshi = Kanshi.from_index(0)
        isouhou = IsouhouResult(stem_interactions=(), branch_interactions=())
        fi = FortuneInteraction(
            period_kanshi=kanshi,
            isouhou=isouhou,
            affected_stars=None,
        )
        assert fi.period_kanshi == kanshi
        assert fi.affected_stars is None
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_fortune.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/domain/fortune.py
"""大運・年運のドメインモデル."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel

from sanmei_core.domain.isouhou import IsouhouResult
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.star import MajorStar


class Gender(Enum):
    """性別."""

    MALE = "男"
    FEMALE = "女"


class Taiun(BaseModel, frozen=True):
    """大運の1期間（10年）."""

    kanshi: Kanshi
    start_age: int
    end_age: int


class TaiunChart(BaseModel, frozen=True):
    """大運表."""

    direction: Literal["順行", "逆行"]
    start_age: int
    periods: tuple[Taiun, ...]


class Nenun(BaseModel, frozen=True):
    """年運（1年分）."""

    year: int
    kanshi: Kanshi
    age: int


class FortuneInteraction(BaseModel, frozen=True):
    """運勢と命式の相互作用."""

    period_kanshi: Kanshi
    isouhou: IsouhouResult
    affected_stars: tuple[MajorStar, ...] | None
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/domain/test_fortune.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add fortune domain model
```

---

### Task 11: SchoolProtocol 拡張 + StandardSchool 更新

**Files:**
- Modify: `packages/sanmei-core/src/sanmei_core/protocols/school.py`
- Modify: `packages/sanmei-core/src/sanmei_core/schools/standard.py`
- Modify: `packages/sanmei-core/tests/unit/schools/test_standard.py`

**Step 1: Write the failing test**

```python
# Add to packages/sanmei-core/tests/unit/schools/test_standard.py

    def test_get_taiun_start_age_rounding(self) -> None:
        """標準流派は切り捨て."""
        school = StandardSchool()
        assert school.get_taiun_start_age_rounding() == "floor"
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/schools/test_standard.py::TestStandardSchool::test_get_taiun_start_age_rounding -v`
Expected: FAIL with `AttributeError`

**Step 3: Update implementation**

Add to `protocols/school.py`:

```python
from typing import Literal, Protocol
```

Add method to `SchoolProtocol`:

```python
    def get_taiun_start_age_rounding(self) -> Literal["floor", "round"]:
        """大運起算年齢の端数処理方法."""
        ...
```

Add to `schools/standard.py` `StandardSchool` class:

```python
    def get_taiun_start_age_rounding(self) -> Literal["floor", "round"]:
        """大運起算年齢の端数処理: 切り捨て."""
        return "floor"
```

**Step 4: Run ALL tests**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v`
Expected: ALL PASS

**Step 5: Commit**

```
feat(sanmei-core): extend SchoolProtocol with taiun rounding
```

---

### Task 12: 大運算出ロジック

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/fortune.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_fortune.py`

**Context:** 大運アルゴリズムの核心部分。日干の陰陽×性別で順行/逆行判定 → 節入り日までの日数 → 起算年齢 → 月柱から干支を辿る。

テストでは MockSetsuiriProvider を使用して天文計算から独立させる。

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_fortune.py
"""大運・年運算出のテスト."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sanmei_core.calculators.fortune import (
    calculate_nenun,
    calculate_taiun,
    determine_direction,
)
from sanmei_core.constants import JST
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.fortune import Gender
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.meishiki import (
    MajorStarChart,
    Meishiki,
    SubsidiaryStarChart,
)
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType
from sanmei_core.protocols.setsuiri import SetsuiriProvider


class MockSetsuiriProvider:
    """テスト用: 固定の節入り日データを返す."""

    def __init__(self, data: dict[int, list[SetsuiriDate]]) -> None:
        self._data = data

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        return self._data.get(year, [])

    def get_risshun(self, year: int) -> SetsuiriDate:
        dates = self.get_setsuiri_dates(year)
        return next(d for d in dates if d.solar_term == SolarTerm.RISSHUN)


def _make_setsuiri(year: int, month: int, day: int, term: SolarTerm) -> SetsuiriDate:
    return SetsuiriDate(
        year=year,
        month=1,  # 算命学月（テストでは未使用）
        datetime_utc=datetime(year, month, day, 0, 0, tzinfo=timezone.utc),
        solar_term=term,
    )


def _make_mock_provider_2024() -> MockSetsuiriProvider:
    """2024年の節入り日データ（簡略版）."""
    return MockSetsuiriProvider(
        {
            2024: [
                _make_setsuiri(2024, 2, 4, SolarTerm.RISSHUN),
                _make_setsuiri(2024, 3, 5, SolarTerm.KEICHITSU),
                _make_setsuiri(2024, 4, 4, SolarTerm.SEIMEI),
                _make_setsuiri(2024, 5, 5, SolarTerm.RIKKA),
                _make_setsuiri(2024, 6, 5, SolarTerm.BOUSHU),
                _make_setsuiri(2024, 7, 6, SolarTerm.SHOUSHO),
                _make_setsuiri(2024, 8, 7, SolarTerm.RISSHUU),
                _make_setsuiri(2024, 9, 7, SolarTerm.HAKURO),
                _make_setsuiri(2024, 10, 8, SolarTerm.KANRO),
                _make_setsuiri(2024, 11, 7, SolarTerm.RITTOU),
                _make_setsuiri(2024, 12, 7, SolarTerm.TAISETSU),
                _make_setsuiri(2025, 1, 5, SolarTerm.SHOUKAN),
            ],
            2025: [
                _make_setsuiri(2025, 2, 3, SolarTerm.RISSHUN),
                _make_setsuiri(2025, 3, 5, SolarTerm.KEICHITSU),
                _make_setsuiri(2025, 4, 4, SolarTerm.SEIMEI),
                _make_setsuiri(2025, 5, 5, SolarTerm.RIKKA),
                _make_setsuiri(2025, 6, 5, SolarTerm.BOUSHU),
                _make_setsuiri(2025, 7, 7, SolarTerm.SHOUSHO),
                _make_setsuiri(2025, 8, 7, SolarTerm.RISSHUU),
                _make_setsuiri(2025, 9, 7, SolarTerm.HAKURO),
                _make_setsuiri(2025, 10, 8, SolarTerm.KANRO),
                _make_setsuiri(2025, 11, 7, SolarTerm.RITTOU),
                _make_setsuiri(2025, 12, 7, SolarTerm.TAISETSU),
                _make_setsuiri(2026, 1, 5, SolarTerm.SHOUKAN),
            ],
        }
    )


def _make_meishiki(
    month_kanshi_index: int,
    day_stem: TenStem = TenStem.KINOE,
) -> Meishiki:
    """テスト用の最小限の命式."""
    return Meishiki(
        pillars=ThreePillars(
            year=Kanshi.from_index(0),
            month=Kanshi.from_index(month_kanshi_index),
            day=Kanshi(stem=day_stem, branch=TwelveBranch.NE, index=0),
        ),
        hidden_stems={
            "year": HiddenStems(main=TenStem.MIZUNOTO),
            "month": HiddenStems(main=TenStem.MIZUNOTO),
            "day": HiddenStems(main=TenStem.MIZUNOTO),
        },
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
        tenchuusatsu=Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        ),
        shukumei_chuusatsu=(),
        gogyo_balance=None,  # type: ignore[arg-type]
    )


class TestDetermineDirection:
    def test_you_male_forward(self) -> None:
        """陽干＋男性 → 順行."""
        assert determine_direction(TenStem.KINOE, Gender.MALE) == "順行"

    def test_in_female_forward(self) -> None:
        """陰干＋女性 → 順行."""
        assert determine_direction(TenStem.KINOTO, Gender.FEMALE) == "順行"

    def test_in_male_reverse(self) -> None:
        """陰干＋男性 → 逆行."""
        assert determine_direction(TenStem.KINOTO, Gender.MALE) == "逆行"

    def test_you_female_reverse(self) -> None:
        """陽干＋女性 → 逆行."""
        assert determine_direction(TenStem.KINOE, Gender.FEMALE) == "逆行"


class TestCalculateTaiun:
    def test_forward_periods(self) -> None:
        """順行: 月柱から六十干支を順に辿る."""
        provider = _make_mock_provider_2024()
        meishiki = _make_meishiki(month_kanshi_index=14, day_stem=TenStem.KINOE)
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        chart = calculate_taiun(
            meishiki, birth_dt, Gender.MALE, provider, rounding="floor", num_periods=3
        )
        assert chart.direction == "順行"
        assert len(chart.periods) == 3
        # 月柱 index=14 の次 → 15, 16, 17
        assert chart.periods[0].kanshi.index == 15
        assert chart.periods[1].kanshi.index == 16
        assert chart.periods[2].kanshi.index == 17

    def test_reverse_periods(self) -> None:
        """逆行: 月柱から六十干支を逆に辿る."""
        provider = _make_mock_provider_2024()
        meishiki = _make_meishiki(month_kanshi_index=14, day_stem=TenStem.KINOTO)
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        chart = calculate_taiun(
            meishiki, birth_dt, Gender.MALE, provider, rounding="floor", num_periods=3
        )
        assert chart.direction == "逆行"
        assert chart.periods[0].kanshi.index == 13
        assert chart.periods[1].kanshi.index == 12
        assert chart.periods[2].kanshi.index == 11

    def test_start_age_calculated(self) -> None:
        """起算年齢が正しく計算される."""
        provider = _make_mock_provider_2024()
        meishiki = _make_meishiki(month_kanshi_index=14, day_stem=TenStem.KINOE)
        # 2024-04-20 生まれ、順行 → 次の節入り(立夏 5/5)まで15日 → 15÷3=5歳
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        chart = calculate_taiun(
            meishiki, birth_dt, Gender.MALE, provider, rounding="floor", num_periods=1
        )
        assert chart.start_age == 5
        assert chart.periods[0].start_age == 5
        assert chart.periods[0].end_age == 14

    def test_period_ages_sequential(self) -> None:
        """各期間の年齢が10年刻みで連続する."""
        provider = _make_mock_provider_2024()
        meishiki = _make_meishiki(month_kanshi_index=14, day_stem=TenStem.KINOE)
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        chart = calculate_taiun(
            meishiki, birth_dt, Gender.MALE, provider, rounding="floor", num_periods=3
        )
        for i in range(1, len(chart.periods)):
            assert chart.periods[i].start_age == chart.periods[i - 1].end_age + 1


class TestCalculateNenun:
    def test_basic_range(self) -> None:
        """指定年範囲の年運を算出."""
        provider = _make_mock_provider_2024()
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        result = calculate_nenun(birth_dt, provider, year_range=(2024, 2026))
        assert len(result) == 3  # 2024, 2025, 2026
        assert result[0].year == 2024
        assert result[1].year == 2025
        assert result[2].year == 2026

    def test_age_calculated(self) -> None:
        """年齢が正しく計算される."""
        provider = _make_mock_provider_2024()
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        result = calculate_nenun(birth_dt, provider, year_range=(2024, 2025))
        assert result[0].age == 0
        assert result[1].age == 1

    def test_kanshi_is_year_kanshi(self) -> None:
        """年運の干支はその年の年柱干支."""
        provider = _make_mock_provider_2024()
        birth_dt = datetime(2024, 4, 20, 12, 0, tzinfo=JST)

        result = calculate_nenun(birth_dt, provider, year_range=(2024, 2024))
        # 2024年 = 甲辰 → index = (2024-4)%60 = 2020%60 = 40
        assert result[0].kanshi.index == 40
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_fortune.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/fortune.py
"""大運・年運の算出."""

from __future__ import annotations

from datetime import datetime, tzinfo
from typing import Literal

from sanmei_core.constants import JST
from sanmei_core.domain.fortune import Gender, Nenun, Taiun, TaiunChart
from sanmei_core.domain.kanshi import Kanshi, TenStem
from sanmei_core.domain.meishiki import Meishiki
from sanmei_core.protocols.setsuiri import SetsuiriProvider
from sanmei_core.tables.gogyo import STEM_TO_INYOU
from sanmei_core.domain.gogyo import InYou


def determine_direction(
    day_stem: TenStem, gender: Gender
) -> Literal["順行", "逆行"]:
    """日干の陰陽 × 性別 で順行/逆行を判定."""
    is_you = STEM_TO_INYOU[day_stem] == InYou.YOU
    is_male = gender == Gender.MALE
    if is_you == is_male:
        return "順行"
    return "逆行"


def _find_nearest_setsuiri_days(
    birth_dt: datetime,
    provider: SetsuiriProvider,
    direction: Literal["順行", "逆行"],
    tz: tzinfo,
) -> int:
    """誕生日から最寄りの節入り日までの日数を算出."""
    local_birth = birth_dt.astimezone(tz)
    year = local_birth.year

    # 当年と前後年の節入り日を全て集める
    all_dates = []
    for y in (year - 1, year, year + 1):
        try:
            all_dates.extend(provider.get_setsuiri_dates(y))
        except Exception:  # noqa: BLE001
            pass

    # UTC に統一してソート
    setsuiri_utcs = sorted(d.datetime_utc for d in all_dates)

    if direction == "順行":
        # 次の節入り日まで
        for s in setsuiri_utcs:
            s_local = s.astimezone(tz)
            if s_local > local_birth:
                return (s_local.date() - local_birth.date()).days
    else:
        # 前の節入り日まで
        for s in reversed(setsuiri_utcs):
            s_local = s.astimezone(tz)
            if s_local <= local_birth:
                return (local_birth.date() - s_local.date()).days

    return 0


def calculate_taiun(
    meishiki: Meishiki,
    birth_datetime: datetime,
    gender: Gender,
    setsuiri_provider: SetsuiriProvider,
    rounding: Literal["floor", "round"] = "floor",
    num_periods: int = 10,
    tz: tzinfo | None = None,
) -> TaiunChart:
    """大運を算出."""
    if tz is None:
        tz = JST

    direction = determine_direction(meishiki.pillars.day.stem, gender)
    days = _find_nearest_setsuiri_days(birth_datetime, setsuiri_provider, direction, tz)

    if rounding == "floor":
        start_age = days // 3
    else:
        start_age = round(days / 3)

    # 月柱から順行 or 逆行で干支を辿る
    month_index = meishiki.pillars.month.index
    step = 1 if direction == "順行" else -1

    periods: list[Taiun] = []
    for i in range(num_periods):
        kanshi_index = (month_index + step * (i + 1)) % 60
        period_start = start_age + i * 10
        period_end = period_start + 9
        periods.append(
            Taiun(
                kanshi=Kanshi.from_index(kanshi_index),
                start_age=period_start,
                end_age=period_end,
            )
        )

    return TaiunChart(
        direction=direction,
        start_age=start_age,
        periods=tuple(periods),
    )


def calculate_nenun(
    birth_datetime: datetime,
    setsuiri_provider: SetsuiriProvider,
    year_range: tuple[int, int],
    tz: tzinfo | None = None,
) -> list[Nenun]:
    """年運を算出. 年運の干支 = その年の年柱干支."""
    if tz is None:
        tz = JST

    local_birth = birth_datetime.astimezone(tz)
    birth_year = local_birth.year
    from_year, to_year = year_range

    result: list[Nenun] = []
    for year in range(from_year, to_year + 1):
        kanshi_index = (year - 4) % 60
        age = year - birth_year
        result.append(
            Nenun(
                year=year,
                kanshi=Kanshi.from_index(kanshi_index),
                age=age,
            )
        )
    return result
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_fortune.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add taiun and nenun calculators
```

---

### Task 13: 大運×命式の相互作用分析

**Files:**
- Create: `packages/sanmei-core/src/sanmei_core/calculators/fortune_analyzer.py`
- Test: `packages/sanmei-core/tests/unit/calculators/test_fortune_analyzer.py`

**Step 1: Write the failing test**

```python
# packages/sanmei-core/tests/unit/calculators/test_fortune_analyzer.py
"""大運×命式の相互作用分析テスト."""

from __future__ import annotations

from sanmei_core.calculators.fortune_analyzer import analyze_fortune_interaction
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.isouhou import BranchInteractionType, StemInteractionType
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.meishiki import (
    MajorStarChart,
    Meishiki,
    SubsidiaryStarChart,
)
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType


def _make_meishiki(
    year_stem: TenStem,
    year_branch: TwelveBranch,
    month_stem: TenStem,
    month_branch: TwelveBranch,
    day_stem: TenStem,
    day_branch: TwelveBranch,
) -> Meishiki:
    return Meishiki(
        pillars=ThreePillars(
            year=Kanshi(stem=year_stem, branch=year_branch, index=0),
            month=Kanshi(stem=month_stem, branch=month_branch, index=1),
            day=Kanshi(stem=day_stem, branch=day_branch, index=2),
        ),
        hidden_stems={
            "year": HiddenStems(main=TenStem.MIZUNOTO),
            "month": HiddenStems(main=TenStem.MIZUNOTO),
            "day": HiddenStems(main=TenStem.MIZUNOTO),
        },
        major_stars=MajorStarChart(
            north=MajorStar.KANSAKU, east=MajorStar.KANSAKU,
            center=MajorStar.KANSAKU, west=MajorStar.KANSAKU,
            south=MajorStar.KANSAKU,
        ),
        subsidiary_stars=SubsidiaryStarChart(
            year=SubsidiaryStar.TENPOU, month=SubsidiaryStar.TENPOU,
            day=SubsidiaryStar.TENPOU,
        ),
        tenchuusatsu=Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        ),
        shukumei_chuusatsu=(),
        gogyo_balance=None,  # type: ignore[arg-type]
    )


class TestAnalyzeFortuneInteraction:
    def test_stem_gou_detected(self) -> None:
        """大運天干と命式天干の合を検出."""
        meishiki = _make_meishiki(
            TenStem.KINOE, TwelveBranch.NE,
            TenStem.HINOE, TwelveBranch.TORA,
            TenStem.KANOE, TwelveBranch.UMA,
        )
        # 大運干支が己(TSUCHINOTO) → 甲(KINOE)との合
        period_kanshi = Kanshi(stem=TenStem.TSUCHINOTO, branch=TwelveBranch.MI, index=5)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        stem_types = {si.type for si in fi.isouhou.stem_interactions}
        assert StemInteractionType.GOU in stem_types

    def test_branch_rokuchuu_detected(self) -> None:
        """大運地支と命式地支の六冲を検出."""
        meishiki = _make_meishiki(
            TenStem.KINOE, TwelveBranch.NE,
            TenStem.HINOE, TwelveBranch.TORA,
            TenStem.KANOE, TwelveBranch.UMA,
        )
        # 大運地支が午(UMA) → 子(NE)との六冲
        period_kanshi = Kanshi(stem=TenStem.HINOTO, branch=TwelveBranch.UMA, index=43)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        branch_types = {bi.type for bi in fi.isouhou.branch_interactions}
        assert BranchInteractionType.ROKUCHUU in branch_types

    def test_no_interaction(self) -> None:
        """相互作用なし."""
        meishiki = _make_meishiki(
            TenStem.KINOE, TwelveBranch.TORA,
            TenStem.HINOE, TwelveBranch.UMA,
            TenStem.KANOE, TwelveBranch.INU,
        )
        period_kanshi = Kanshi(stem=TenStem.MIZUNOE, branch=TwelveBranch.NE, index=48)
        fi = analyze_fortune_interaction(meishiki, period_kanshi)
        assert len(fi.isouhou.stem_interactions) == 0
        # NE + TORA/UMA/INU → no direct pair interaction (NE-TORA no match)
```

**Step 2: Run test to verify it fails**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_fortune_analyzer.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# packages/sanmei-core/src/sanmei_core/calculators/fortune_analyzer.py
"""命式×運勢の相互作用分析."""

from __future__ import annotations

from sanmei_core.calculators.isouhou import (
    analyze_branch_interactions,
    analyze_stem_interactions,
)
from sanmei_core.domain.fortune import FortuneInteraction
from sanmei_core.domain.isouhou import IsouhouResult
from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.meishiki import Meishiki


def analyze_fortune_interaction(
    meishiki: Meishiki,
    period_kanshi: Kanshi,
) -> FortuneInteraction:
    """大運/年運の干支と命式の相互作用を分析.

    命式の三柱の天干・地支と大運/年運の天干・地支の間で
    合冲刑害を検出する。
    """
    # 命式の天干 + 大運天干
    all_stems = [
        meishiki.pillars.year.stem,
        meishiki.pillars.month.stem,
        meishiki.pillars.day.stem,
        period_kanshi.stem,
    ]
    stem_interactions = analyze_stem_interactions(all_stems)

    # 命式の地支 + 大運地支
    all_branches = [
        meishiki.pillars.year.branch,
        meishiki.pillars.month.branch,
        meishiki.pillars.day.branch,
        period_kanshi.branch,
    ]
    branch_interactions = analyze_branch_interactions(all_branches)

    # 命式内部の相互作用は除外（大運/年運との相互作用のみ）
    # → period_kanshi の stem/branch が含まれるもののみフィルタ
    filtered_stems = [
        si for si in stem_interactions if period_kanshi.stem in si.stems
    ]
    filtered_branches = [
        bi for bi in branch_interactions if period_kanshi.branch in bi.branches
    ]

    return FortuneInteraction(
        period_kanshi=period_kanshi,
        isouhou=IsouhouResult(
            stem_interactions=tuple(filtered_stems),
            branch_interactions=tuple(filtered_branches),
        ),
        affected_stars=None,
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests/unit/calculators/test_fortune_analyzer.py -v`
Expected: PASS

**Step 5: Commit**

```
feat(sanmei-core): add fortune interaction analyzer
```

---

### Task 14: 公開 API エクスポート + 品質ゲート

**Files:**
- Modify: `packages/sanmei-core/src/sanmei_core/__init__.py`

**Step 1: Update exports**

Add all new public types and functions to `__init__.py`:

```python
# New imports to add:
from sanmei_core.calculators.fortune import calculate_nenun, calculate_taiun
from sanmei_core.calculators.fortune_analyzer import analyze_fortune_interaction
from sanmei_core.calculators.gogyo_balance import calculate_gogyo_balance
from sanmei_core.calculators.isouhou import (
    analyze_branch_interactions,
    analyze_isouhou,
    analyze_stem_interactions,
)
from sanmei_core.calculators.shukumei_chuusatsu import calculate_shukumei_chuusatsu
from sanmei_core.domain.fortune import FortuneInteraction, Gender, Nenun, Taiun, TaiunChart
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount
from sanmei_core.domain.isouhou import (
    BranchInteraction,
    BranchInteractionType,
    IsouhouResult,
    StemInteraction,
    StemInteractionType,
)
from sanmei_core.domain.shukumei_chuusatsu import (
    ShukumeiChuusatsu,
    ShukumeiChuusatsuPosition,
)

# New items to add to __all__:
    "BranchInteraction",
    "BranchInteractionType",
    "FortuneInteraction",
    "Gender",
    "GoGyoBalance",
    "GoGyoCount",
    "IsouhouResult",
    "Nenun",
    "ShukumeiChuusatsu",
    "ShukumeiChuusatsuPosition",
    "StemInteraction",
    "StemInteractionType",
    "Taiun",
    "TaiunChart",
    "analyze_branch_interactions",
    "analyze_fortune_interaction",
    "analyze_isouhou",
    "analyze_stem_interactions",
    "calculate_gogyo_balance",
    "calculate_nenun",
    "calculate_shukumei_chuusatsu",
    "calculate_taiun",
```

**Step 2: Run quality gate**

Run: `just check`
Expected: lint PASS, typecheck PASS, all tests PASS

**Step 3: Check coverage**

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests --cov=sanmei_core --cov-report=term-missing -v`
Expected: Coverage >= 80%

**Step 4: Commit**

```
feat(sanmei-core): export kantei expansion public API and pass quality gate
```
