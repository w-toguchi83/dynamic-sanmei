"""大運四季表ドメインモデルのテスト."""

import pytest
from pydantic import ValidationError
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.taiun_shiki import LifeCycle, Season, TaiunShikiChart, TaiunShikiEntry


class TestSeason:
    def test_values(self) -> None:
        assert Season.SPRING.value == "春"
        assert Season.SUMMER.value == "夏"
        assert Season.AUTUMN.value == "秋"
        assert Season.WINTER.value == "冬"

    def test_count(self) -> None:
        assert len(Season) == 4


class TestLifeCycle:
    def test_all_twelve(self) -> None:
        assert len(LifeCycle) == 12

    def test_first_and_last(self) -> None:
        assert LifeCycle.TAIJI.value == "胎児"
        assert LifeCycle.ANOYO.value == "あの世"

    def test_middle_values(self) -> None:
        assert LifeCycle.SEINEN.value == "青年"
        assert LifeCycle.ROUJIN.value == "老人"
        assert LifeCycle.SHININ.value == "死人"
        assert LifeCycle.NYUUBO.value == "入墓"


class TestTaiunShikiEntry:
    def test_construction(self) -> None:
        entry = TaiunShikiEntry(
            label="第1句",
            kanshi=Kanshi.from_index(2),  # 丙寅
            start_age=5,
            end_age=14,
            season=Season.SPRING,
            hidden_stems=HiddenStems(
                hongen=TenStem.KINOE,
                chuugen=TenStem.HINOE,
                shogen=TenStem.TSUCHINOE,
            ),
            major_star=MajorStar.HOUKAKU,
            subsidiary_star=SubsidiaryStar.TENNAN,
            life_cycle=LifeCycle.SEINEN,
        )
        assert entry.label == "第1句"
        assert entry.kanshi.kanji == "丙寅"
        assert entry.season == Season.SPRING
        assert entry.life_cycle == LifeCycle.SEINEN

    def test_frozen(self) -> None:
        entry = TaiunShikiEntry(
            label="月干支",
            kanshi=Kanshi.from_index(0),
            start_age=0,
            end_age=4,
            season=Season.WINTER,
            hidden_stems=HiddenStems(hongen=TenStem.MIZUNOTO),
            major_star=MajorStar.KANSAKU,
            subsidiary_star=SubsidiaryStar.TENPOU,
            life_cycle=LifeCycle.TAIJI,
        )
        with pytest.raises(ValidationError):
            entry.label = "changed"  # type: ignore[misc]


class TestTaiunShikiChart:
    def test_construction(self) -> None:
        entry = TaiunShikiEntry(
            label="月干支",
            kanshi=Kanshi.from_index(0),
            start_age=0,
            end_age=4,
            season=Season.WINTER,
            hidden_stems=HiddenStems(hongen=TenStem.MIZUNOTO),
            major_star=MajorStar.KANSAKU,
            subsidiary_star=SubsidiaryStar.TENPOU,
            life_cycle=LifeCycle.TAIJI,
        )
        chart = TaiunShikiChart(
            direction="順行",
            start_age=5,
            entries=(entry,),
        )
        assert chart.direction == "順行"
        assert len(chart.entries) == 1
