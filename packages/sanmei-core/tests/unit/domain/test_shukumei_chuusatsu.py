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
