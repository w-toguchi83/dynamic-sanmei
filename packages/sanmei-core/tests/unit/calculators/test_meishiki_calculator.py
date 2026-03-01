"""MeishikiCalculator 統合テスト."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError
from sanmei_core.calculators.meishiki_calculator import MeishikiCalculator
from sanmei_core.constants import JST
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
        """Appendix A サンプル: 1985年4月10日."""
        school = StandardSchool()
        calc = MeishikiCalculator(school)
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
        with pytest.raises(ValidationError):
            meishiki.pillars = None  # type: ignore[misc]
