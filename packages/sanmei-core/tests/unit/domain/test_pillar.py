from sanmei_core.domain.kanshi import Kanshi
from sanmei_core.domain.pillar import ThreePillars


def test_three_pillars_creation() -> None:
    year = Kanshi.from_index(0)  # 甲子
    month = Kanshi.from_index(2)  # 丙寅
    day = Kanshi.from_index(10)  # 甲戌
    pillars = ThreePillars(year=year, month=month, day=day)
    assert pillars.year.kanji == "甲子"
    assert pillars.month.kanji == "丙寅"
    assert pillars.day.kanji == "甲戌"
