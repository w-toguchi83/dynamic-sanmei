"""大運・年運ドメインモデルのテスト."""

from __future__ import annotations

from sanmei_core.domain.fortune import (
    FortuneInteraction,
    Gender,
    Nenun,
    Taiun,
    TaiunChart,
)
from sanmei_core.domain.isouhou import IsouhouResult
from sanmei_core.domain.kanshi import Kanshi


class TestGender:
    def test_male(self) -> None:
        assert Gender.MALE.value == "男"

    def test_female(self) -> None:
        assert Gender.FEMALE.value == "女"


class TestTaiun:
    def test_creation(self) -> None:
        kanshi = Kanshi.from_index(0)
        taiun = Taiun(kanshi=kanshi, start_age=3, end_age=12)
        assert taiun.kanshi == kanshi
        assert taiun.start_age == 3
        assert taiun.end_age == 12


class TestTaiunChart:
    def test_creation(self) -> None:
        periods = (
            Taiun(kanshi=Kanshi.from_index(1), start_age=3, end_age=12),
            Taiun(kanshi=Kanshi.from_index(2), start_age=13, end_age=22),
        )
        chart = TaiunChart(direction="順行", start_age=3, periods=periods)
        assert chart.direction == "順行"
        assert chart.start_age == 3
        assert len(chart.periods) == 2

    def test_reverse_direction(self) -> None:
        chart = TaiunChart(direction="逆行", start_age=7, periods=())
        assert chart.direction == "逆行"


class TestNenun:
    def test_creation(self) -> None:
        kanshi = Kanshi.from_index(40)
        nenun = Nenun(year=2024, kanshi=kanshi, age=30)
        assert nenun.year == 2024
        assert nenun.age == 30


class TestFortuneInteraction:
    def test_creation(self) -> None:
        kanshi = Kanshi.from_index(0)
        isouhou = IsouhouResult(stem_interactions=(), branch_interactions=())
        fi = FortuneInteraction(
            period_kanshi=kanshi,
            isouhou=isouhou,
            affected_stars=None,
        )
        assert fi.period_kanshi == kanshi
        assert fi.affected_stars is None
