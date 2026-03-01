"""五行バランスドメインモデルのテスト."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
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

    def test_frozen(self) -> None:
        stem = GoGyoCount(wood=1)
        branch = GoGyoCount()
        total = GoGyoCount(wood=1)
        balance = GoGyoBalance(
            stem_count=stem,
            branch_count=branch,
            total_count=total,
            dominant=GoGyo.WOOD,
            lacking=(),
            day_stem_gogyo=GoGyo.FIRE,
        )
        with pytest.raises(ValidationError):
            balance.dominant = GoGyo.FIRE  # type: ignore[misc]
