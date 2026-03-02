"""蔵干モデルのテスト."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem


class TestHiddenStems:
    def test_all_three(self) -> None:
        hs = HiddenStems(hongen=TenStem.KINOE, chuugen=TenStem.HINOE, shogen=TenStem.TSUCHINOE)
        assert hs.hongen == TenStem.KINOE
        assert hs.chuugen == TenStem.HINOE
        assert hs.shogen == TenStem.TSUCHINOE

    def test_hongen_only(self) -> None:
        hs = HiddenStems(hongen=TenStem.MIZUNOTO, chuugen=None, shogen=None)
        assert hs.hongen == TenStem.MIZUNOTO
        assert hs.chuugen is None
        assert hs.shogen is None

    def test_hongen_and_chuugen(self) -> None:
        hs = HiddenStems(hongen=TenStem.MIZUNOE, chuugen=TenStem.KINOE, shogen=None)
        assert hs.chuugen == TenStem.KINOE
        assert hs.shogen is None

    def test_frozen(self) -> None:
        hs = HiddenStems(hongen=TenStem.KINOE, chuugen=None, shogen=None)
        with pytest.raises(ValidationError):
            hs.hongen = TenStem.KINOTO  # type: ignore[misc]
