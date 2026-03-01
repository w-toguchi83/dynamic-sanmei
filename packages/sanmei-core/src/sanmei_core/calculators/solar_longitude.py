"""太陽黄経計算（Jean Meeus アルゴリズム）と MeeusSetsuiriProvider.

Jean Meeus, *Astronomical Algorithms*, 2nd Edition, Chapter 25 に基づく。
VSOP87 簡略版を使用。精度: ±0.01° (≒ ±15分)。
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm

# --- Julian Day Number 変換 ---

_J2000 = 2451545.0  # 2000-01-01 12:00 TT の JDE


def datetime_to_jde(dt: datetime) -> float:
    """datetime (UTC) → Julian Ephemeris Day.

    簡略化のため ΔT（TT-UTC 差）は無視。
    対象範囲(1864-2100)では最大 ΔT ≈ 70秒で、時単位精度には影響なし。
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    delta = dt - datetime(2000, 1, 1, 12, 0, 0)
    return _J2000 + delta.total_seconds() / 86400.0


def jde_to_datetime(jde: float) -> datetime:
    """Julian Ephemeris Day → datetime (UTC)."""
    delta_days = jde - _J2000
    return datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC) + timedelta(days=delta_days)


# --- 太陽黄経計算 (Meeus Chapter 25) ---


def solar_longitude(jde: float) -> float:
    """JDE から太陽の視黄経（度）を計算.

    Meeus, Astronomical Algorithms, 2nd ed., Chapter 25.
    低精度バージョン（Table 25.C の主要項）。
    """
    # Julian centuries from J2000.0
    t = (jde - _J2000) / 36525.0

    # 太陽の平均黄経 (L0) — degree
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    l0 = l0 % 360

    # 太陽の平均近点角 (M) — degree
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    m_rad = math.radians(m % 360)

    # 中心差 (C)
    c = (
        (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m_rad)
        + (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
        + 0.000289 * math.sin(3 * m_rad)
    )

    # 太陽の真黄経
    sun_lon = l0 + c

    # 章動と光行差の補正 (簡略)
    omega = 125.04 - 1934.136 * t
    omega_rad = math.radians(omega)
    apparent_lon = sun_lon - 0.00569 - 0.00478 * math.sin(omega_rad)

    return apparent_lon % 360


# --- 節入り日計算 ---

# 節気（月境界）の SolarTerm を算命学月順に列挙
_SETSU_TERMS: tuple[SolarTerm, ...] = (
    SolarTerm.RISSHUN,  # 1月 寅 315°
    SolarTerm.KEICHITSU,  # 2月 卯 345°
    SolarTerm.SEIMEI,  # 3月 辰 15°
    SolarTerm.RIKKA,  # 4月 巳 45°
    SolarTerm.BOUSHU,  # 5月 午 75°
    SolarTerm.SHOUSHO,  # 6月 未 105°
    SolarTerm.RISSHUU,  # 7月 申 135°
    SolarTerm.HAKURO,  # 8月 酉 165°
    SolarTerm.KANRO,  # 9月 戌 195°
    SolarTerm.RITTOU,  # 10月 亥 225°
    SolarTerm.TAISETSU,  # 11月 子 255°
    SolarTerm.SHOUKAN,  # 12月 丑 285°
)

# 各節気のおおよその月日（探索範囲の初期推定用）
_APPROX_MONTH_DAY: tuple[tuple[int, int], ...] = (
    (2, 4),  # 立春
    (3, 6),  # 啓蟄
    (4, 5),  # 清明
    (5, 6),  # 立夏
    (6, 6),  # 芒種
    (7, 7),  # 小暑
    (8, 7),  # 立秋
    (9, 8),  # 白露
    (10, 8),  # 寒露
    (11, 7),  # 立冬
    (12, 7),  # 大雪
    (1, 6),  # 小寒（翌年1月）
)


def _find_solar_term_time(
    year: int,
    target_longitude: float,
    approx_month: int,
    approx_day: int,
) -> datetime:
    """二分探索で太陽黄経が target_longitude に達する UTC 時刻を求める.

    探索精度: 約1分。
    """
    # 小寒は翌年1月
    search_year = year + 1 if approx_month == 1 else year
    center = datetime(search_year, approx_month, approx_day, 12, 0, tzinfo=UTC)
    # ±15日の範囲で探索
    lo_jde = datetime_to_jde(center - timedelta(days=15))
    hi_jde = datetime_to_jde(center + timedelta(days=15))

    target = target_longitude

    # 黄経は 0°/360° をまたぐことがあるので正規化
    def _normalized_longitude(jde: float) -> float:
        lon = solar_longitude(jde)
        if target > 180:
            # target が 315° 等の場合、0° 付近を +360 にして連続化
            if lon < 180:
                lon += 360
        return lon

    target_normalized = target

    for _ in range(64):  # 十分な反復回数
        mid_jde = (lo_jde + hi_jde) / 2
        mid_lon = _normalized_longitude(mid_jde)
        if mid_lon < target_normalized:
            lo_jde = mid_jde
        else:
            hi_jde = mid_jde
        if (hi_jde - lo_jde) < 0.0005:  # ≈ 43秒
            break

    result_jde = (lo_jde + hi_jde) / 2
    return jde_to_datetime(result_jde)


# --- MeeusSetsuiriProvider ---


class MeeusSetsuiriProvider:
    """Jean Meeus のアルゴリズムに基づく SetsuiriProvider 実装.

    太陽黄経を計算し、各節気の正確な時刻を二分探索で特定する。
    精度: ±15分（時単位要件に十分）。
    対象範囲: 1864-2100年。
    """

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        """指定年の12節入り日を算出."""
        results: list[SetsuiriDate] = []
        for i, term in enumerate(_SETSU_TERMS):
            approx_m, approx_d = _APPROX_MONTH_DAY[i]
            dt_utc = _find_solar_term_time(
                year,
                term.longitude,
                approx_m,
                approx_d,
            )
            results.append(
                SetsuiriDate(
                    year=year,
                    month=i + 1,
                    datetime_utc=dt_utc,
                    solar_term=term,
                )
            )
        return results

    def get_risshun(self, year: int) -> SetsuiriDate:
        """指定年の立春を算出."""
        approx_m, approx_d = _APPROX_MONTH_DAY[0]
        dt_utc = _find_solar_term_time(
            year,
            SolarTerm.RISSHUN.longitude,
            approx_m,
            approx_d,
        )
        return SetsuiriDate(
            year=year,
            month=1,
            datetime_utc=dt_utc,
            solar_term=SolarTerm.RISSHUN,
        )
