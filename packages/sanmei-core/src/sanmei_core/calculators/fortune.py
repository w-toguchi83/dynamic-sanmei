"""大運・年運の算出."""

from __future__ import annotations

from datetime import datetime, tzinfo
from typing import Literal

from sanmei_core.constants import JST
from sanmei_core.domain.fortune import Gender, Nenun, Taiun, TaiunChart
from sanmei_core.domain.gogyo import InYou
from sanmei_core.domain.kanshi import Kanshi, TenStem
from sanmei_core.domain.meishiki import Meishiki
from sanmei_core.protocols.setsuiri import SetsuiriProvider
from sanmei_core.tables.gogyo import STEM_TO_INYOU


def determine_direction(day_stem: TenStem, gender: Gender) -> Literal["順行", "逆行"]:
    """日干の陰陽 x 性別 で順行/逆行を判定.

    陽干+男性 or 陰干+女性 -> 順行
    陰干+男性 or 陽干+女性 -> 逆行
    """
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
    """誕生日から最寄りの節入り日までの日数を算出.

    順行: 誕生日の後の最初の節入り日までの日数
    逆行: 誕生日の前の最後の節入り日からの日数
    """
    local_birth = birth_dt.astimezone(tz)
    year = local_birth.year

    all_dates = []
    for y in (year - 1, year, year + 1):
        all_dates.extend(provider.get_setsuiri_dates(y))

    setsuiri_utcs = sorted(d.datetime_utc for d in all_dates)

    if direction == "順行":
        for s in setsuiri_utcs:
            s_local = s.astimezone(tz)
            if s_local > local_birth:
                return (s_local.date() - local_birth.date()).days
    else:
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
    """大運を算出.

    1. 日干と性別から順行/逆行を判定
    2. 誕生日から最寄りの節入り日までの日数を算出
    3. 日数 / 3 = 起算年齢（3日で1歳）
    4. 月柱の干支から順/逆に辿って大運の干支列を生成
    """
    if tz is None:
        tz = JST

    direction = determine_direction(meishiki.pillars.day.stem, gender)
    days = _find_nearest_setsuiri_days(birth_datetime, setsuiri_provider, direction, tz)

    if rounding == "floor":
        start_age = days // 3
    else:
        start_age = round(days / 3)

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
    setsuiri_provider: SetsuiriProvider,  # noqa: ARG001
    year_range: tuple[int, int],
    tz: tzinfo | None = None,
) -> list[Nenun]:
    """年運を算出.

    年運の干支 = その年の年柱干支（西暦から一意に決まる）。
    年齢 = 対象年 - 生年。

    setsuiri_provider は将来の拡張（節入り考慮の年齢計算等）のために
    シグネチャに含めている。
    """
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
