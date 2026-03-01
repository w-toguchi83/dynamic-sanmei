"""日柱計算 — 西暦日付から日干支を算出."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sanmei_core.constants import JST
from sanmei_core.domain.kanshi import Kanshi

if TYPE_CHECKING:
    from datetime import tzinfo

# 基準日: 1900-01-01 = 甲戌 (六十干支 index 10)
_REFERENCE_DATE = date(1900, 1, 1)
_REFERENCE_INDEX = 10


def day_pillar(dt: datetime, *, tz: tzinfo | None = None) -> Kanshi:
    """日柱の干支を算出.

    Args:
        dt: 対象日時（timezone-aware を推奨）
        tz: 日付判定に使うタイムゾーン。None の場合は JST。

    Returns:
        日柱の干支
    """
    if tz is None:
        tz = JST
    local_dt = dt.astimezone(tz)
    local_date = local_dt.date()
    diff = (local_date - _REFERENCE_DATE).days
    index = (_REFERENCE_INDEX + diff) % 60
    return Kanshi.from_index(index)
