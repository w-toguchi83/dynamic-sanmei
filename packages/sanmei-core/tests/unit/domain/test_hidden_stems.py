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
