from datetime import datetime, timedelta, timezone

import pytest
from sanmei_core import (
    Gender,
    MeishikiCalculator,
    SchoolRegistry,
    analyze_compatibility,
    analyze_isouhou,
    calculate_nenun,
    calculate_taiun,
    calculate_taiun_shiki,
)

JST = timezone(timedelta(hours=9))
BIRTH_DT = datetime(2000, 1, 15, 14, 30, tzinfo=JST)
BIRTH_DT_B = datetime(1990, 5, 20, 10, 0, tzinfo=JST)


@pytest.fixture
def school():
    registry = SchoolRegistry.create_default()
    return registry.default()


@pytest.fixture
def meishiki(school):
    calc = MeishikiCalculator(school)
    return calc.calculate(BIRTH_DT)


@pytest.fixture
def taiun_chart(meishiki, school):
    return calculate_taiun(
        meishiki,
        BIRTH_DT,
        Gender.MALE,
        school.get_setsuiri_provider(),
        rounding=school.get_taiun_start_age_rounding(),
    )


@pytest.fixture
def month_kanshi_kanji(meishiki):
    return meishiki.pillars.month.kanji


@pytest.fixture
def nenun_list(school):
    return calculate_nenun(
        BIRTH_DT,
        school.get_setsuiri_provider(),
        year_range=(2020, 2025),
    )


@pytest.fixture
def isouhou_result(meishiki):
    return analyze_isouhou(meishiki.pillars)


@pytest.fixture
def shiki_chart(meishiki, taiun_chart, school):
    return calculate_taiun_shiki(meishiki, taiun_chart, school)


@pytest.fixture
def meishiki_b(school):
    calc = MeishikiCalculator(school)
    return calc.calculate(BIRTH_DT_B)


@pytest.fixture
def compatibility_result(meishiki, meishiki_b):
    return analyze_compatibility(meishiki, meishiki_b)
