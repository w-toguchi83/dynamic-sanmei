"""十大主星・十二大従星の Enum テスト."""

from __future__ import annotations

from sanmei_core.domain.star import MajorStar, SubsidiaryStar


class TestMajorStar:
    def test_count(self) -> None:
        assert len(MajorStar) == 10

    def test_values(self) -> None:
        assert MajorStar.KANSAKU.value == "貫索星"
        assert MajorStar.SEKIMON.value == "石門星"
        assert MajorStar.HOUKAKU.value == "鳳閣星"
        assert MajorStar.CHOUJYO.value == "調舒星"
        assert MajorStar.ROKUZON.value == "禄存星"
        assert MajorStar.SHIROKU.value == "司禄星"
        assert MajorStar.SHAKI.value == "車騎星"
        assert MajorStar.KENGYU.value == "牽牛星"
        assert MajorStar.RYUKOU.value == "龍高星"
        assert MajorStar.GYOKUDO.value == "玉堂星"


class TestSubsidiaryStar:
    def test_count(self) -> None:
        assert len(SubsidiaryStar) == 12

    def test_values(self) -> None:
        assert SubsidiaryStar.TENPOU.value == "天報星"
        assert SubsidiaryStar.TENIN.value == "天印星"
        assert SubsidiaryStar.TENKI.value == "天貴星"
        assert SubsidiaryStar.TENKOU.value == "天恍星"
        assert SubsidiaryStar.TENNAN.value == "天南星"
        assert SubsidiaryStar.TENROKU.value == "天禄星"
        assert SubsidiaryStar.TENSHOU.value == "天将星"
        assert SubsidiaryStar.TENDOU.value == "天堂星"
        assert SubsidiaryStar.TENKO.value == "天胡星"
        assert SubsidiaryStar.TENKYOKU.value == "天極星"
        assert SubsidiaryStar.TENKU.value == "天庫星"
        assert SubsidiaryStar.TENCHI.value == "天馳星"
