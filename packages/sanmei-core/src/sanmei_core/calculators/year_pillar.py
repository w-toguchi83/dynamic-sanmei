"""年柱計算 — 立春を境界として年干支を算出."""

from __future__ import annotations

from datetime import datetime, tzinfo

from sanmei_core.constants import JST
from sanmei_core.domain.calendar import SetsuiriDate
from sanmei_core.domain.kanshi import Kanshi


def year_pillar(
    dt: datetime,
    risshun: SetsuiriDate,
    *,
    tz: tzinfo | None = None,
) -> Kanshi:
    """年柱の干支を算出.

    立春より前なら前年の干支、立春以降なら当年の干支を使用。
    基準: 西暦4年 = 甲子 (index 0)。

    Args:
        dt: 対象日時
        risshun: 当年の立春データ
        tz: タイムゾーン。None の場合は JST。

    Returns:
        年柱の干支
    """
    if tz is None:
        tz = JST
    local_dt = dt.astimezone(tz)
    risshun_local = risshun.datetime_utc.astimezone(tz)

    year = local_dt.year
    if local_dt < risshun_local:
        year -= 1

    index = (year - 4) % 60
    return Kanshi.from_index(index)
