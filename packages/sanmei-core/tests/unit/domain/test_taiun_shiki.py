"""大運四季表ドメインモデルのテスト."""

from sanmei_core.domain.taiun_shiki import LifeCycle, Season


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
