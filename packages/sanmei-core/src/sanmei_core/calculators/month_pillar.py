"""月柱計算 — 節入り日から月干支を算出."""

from __future__ import annotations

from datetime import datetime, tzinfo

from sanmei_core.constants import JST
from sanmei_core.domain.calendar import SetsuiriDate
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.tables.month_stem import get_month_stem


def month_pillar(
    dt: datetime,
    setsuiri_dates: list[SetsuiriDate],
    year_stem: TenStem,
    *,
    tz: tzinfo | None = None,
) -> Kanshi:
    """月柱の干支を算出.

    節入り日リストから該当月を特定し、五虎遁年法で月干を決定。

    Args:
        dt: 対象日時
        setsuiri_dates: 当年の12節入り日（立春〜小寒）
        year_stem: 年柱の天干（五虎遁年法の入力）
        tz: タイムゾーン。None の場合は JST。

    Returns:
        月柱の干支
    """
    if tz is None:
        tz = JST
    local_dt = dt.astimezone(tz)

    # 節入り日を時系列ソート
    sorted_dates = sorted(setsuiri_dates, key=lambda s: s.datetime_utc)

    # date がどの節入り日の間に入るかを判定
    sanmei_month = _find_sanmei_month(local_dt, sorted_dates, tz)

    # 月支: 寅(2) から算命学月番号分オフセット
    branch = TwelveBranch((TwelveBranch.TORA.value + sanmei_month - 1) % 12)

    # 月干: 五虎遁年法
    stem = get_month_stem(year_stem, sanmei_month)

    # 六十干支 index を算出
    index = _stem_branch_to_index(stem, branch)
    return Kanshi(stem=stem, branch=branch, index=index)


def _find_sanmei_month(
    local_dt: datetime,
    sorted_dates: list[SetsuiriDate],
    tz: tzinfo,
) -> int:
    """対象日時が属する算命学月を特定.

    Returns:
        算命学月 (1=寅月〜12=丑月)
    """
    # 逆順に走査し、最初に「節入り日 <= local_dt」となる月を見つける
    for sd in reversed(sorted_dates):
        setsuiri_local = sd.datetime_utc.astimezone(tz)
        if local_dt >= setsuiri_local:
            return sd.month

    # 全節入り日より前 → 前年の丑月(12月)
    return 12


def _stem_branch_to_index(stem: TenStem, branch: TwelveBranch) -> int:
    """天干と地支から六十干支の index を算出."""
    # stem = index % 10, branch = index % 12
    # 中国剰余定理: index = (6 * stem - 5 * branch) % 60
    return (6 * stem.value - 5 * branch.value) % 60
