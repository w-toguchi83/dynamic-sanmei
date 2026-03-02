"""使命星（しめいせい）の算出.

使命星は「年干の干合相手」と「日干」から十大主星を引く。
  1. 年干の干合相手を取得（甲↔己, 乙↔庚, 丙↔辛, 丁↔壬, 戊↔癸）
  2. determine_major_star(日干, 干合相手) で十大主星を取得
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.domain.kanshi import TenStem
from sanmei_core.domain.star import MajorStar
from sanmei_core.tables.isouhou import get_kangou_partner

if TYPE_CHECKING:
    from sanmei_core.protocols.school import SchoolProtocol


def calculate_shimeisei(
    day_stem: TenStem,
    year_stem: TenStem,
    school: SchoolProtocol,
) -> MajorStar:
    """使命星を算出.

    Args:
        day_stem: 日干
        year_stem: 年干
        school: 流派

    Returns:
        使命星（十大主星のいずれか）
    """
    kangou_partner = get_kangou_partner(year_stem)
    return school.determine_major_star(day_stem, kangou_partner)
