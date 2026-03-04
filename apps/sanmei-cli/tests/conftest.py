from datetime import datetime, timedelta, timezone

import pytest
from sanmei_core import (
    Gender,
    MeishikiCalculator,
    SchoolRegistry,
    analyze_isouhou,
    calculate_nenun,
    calculate_taiun,
)

JST = timezone(timedelta(hours=9))
BIRTH_DT = datetime(2000, 1, 15, 14, 30, tzinfo=JST)


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
