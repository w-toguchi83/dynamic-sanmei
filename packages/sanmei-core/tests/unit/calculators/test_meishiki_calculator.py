"""MeishikiCalculator 統合テスト."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError
from sanmei_core.calculators.meishiki_calculator import MeishikiCalculator
from sanmei_core.constants import JST
from sanmei_core.domain.star import MajorStar
from sanmei_core.domain.tenchuusatsu import TenchuusatsuType
from sanmei_core.domain.zoukan_tokutei import HiddenStemType, ZoukanTokutei
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
        assert meishiki.hidden_stems["year"].hongen is not None
        assert meishiki.hidden_stems["month"].hongen is not None
        assert meishiki.hidden_stems["day"].hongen is not None

        # 天中殺の type が有効であること
        assert isinstance(meishiki.tenchuusatsu.type, TenchuusatsuType)

    def test_meishiki_has_shukumei_chuusatsu(self) -> None:
        """命式に宿命中殺フィールドが含まれる."""
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        assert isinstance(meishiki.shukumei_chuusatsu, tuple)

    def test_meishiki_has_gogyo_balance(self) -> None:
        """命式に五行バランスフィールドが含まれる."""
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        assert meishiki.gogyo_balance is not None
        assert meishiki.gogyo_balance.total_count.total > 0
        assert meishiki.gogyo_balance.day_stem_gogyo is not None

    def test_meishiki_has_shimeisei(self) -> None:
        """命式に使命星フィールドが含まれる."""
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        assert isinstance(meishiki.shimeisei, MajorStar)

    def test_meishiki_has_zoukan_tokutei(self) -> None:
        """命式に蔵干特定フィールドが含まれる."""
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        assert isinstance(meishiki.zoukan_tokutei, ZoukanTokutei)
        assert meishiki.zoukan_tokutei.days_from_setsuiri >= 1
        assert meishiki.zoukan_tokutei.year.stem is not None
        assert meishiki.zoukan_tokutei.month.stem is not None
        assert meishiki.zoukan_tokutei.day.stem is not None

    def test_book_example_1988_11_01(self) -> None:
        """書籍サンプル: 1988年11月1日 → 25日 → 全本元.

        10月節入り=10月8日(寒露), 11月1日 → (11/1 - 10/8).days + 1 = 25日
        年支=辰(25日→本元戊), 月支=戌(25日→本元戊), 日支=申(25日→本元庚)
        """
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(1988, 11, 1, 0, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        zt = meishiki.zoukan_tokutei
        assert zt.year.element == HiddenStemType.HONGEN
        assert zt.month.element == HiddenStemType.HONGEN
        assert zt.day.element == HiddenStemType.HONGEN

    def test_meishiki_is_frozen(self) -> None:
        school = StandardSchool()
        calc = MeishikiCalculator(school)
        dt = datetime(2024, 1, 1, 12, 0, tzinfo=JST)
        meishiki = calc.calculate(dt)
        # frozen model → attribute assignment raises
        with pytest.raises(ValidationError):
            meishiki.pillars = None  # type: ignore[misc,assignment]
