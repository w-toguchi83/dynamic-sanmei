"""五行・陰陽の Enum テスト."""

from __future__ import annotations

from sanmei_core.domain.gogyo import GoGyo, InYou


class TestGoGyo:
    def test_count(self) -> None:
        assert len(GoGyo) == 5

    def test_values(self) -> None:
        assert GoGyo.WOOD == 0
        assert GoGyo.FIRE == 1
        assert GoGyo.EARTH == 2
        assert GoGyo.METAL == 3
        assert GoGyo.WATER == 4

    def test_kanji(self) -> None:
        assert GoGyo.WOOD.kanji == "木"
        assert GoGyo.FIRE.kanji == "火"
        assert GoGyo.EARTH.kanji == "土"
        assert GoGyo.METAL.kanji == "金"
        assert GoGyo.WATER.kanji == "水"


class TestInYou:
    def test_count(self) -> None:
        assert len(InYou) == 2

    def test_values(self) -> None:
        assert InYou.YOU == 0
        assert InYou.IN == 1

    def test_kanji(self) -> None:
        assert InYou.YOU.kanji == "陽"
        assert InYou.IN.kanji == "陰"
