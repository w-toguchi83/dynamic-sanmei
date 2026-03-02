"""使命星の算出テスト."""

from __future__ import annotations

import pytest
from sanmei_core.calculators.shimeisei import calculate_shimeisei
from sanmei_core.domain.kanshi import TenStem
from sanmei_core.domain.star import MajorStar
from sanmei_core.schools.standard import StandardSchool


class TestCalculateShimeisei:
    """使命星算出のテスト.

    使命星 = determine_major_star(日干, get_kangou_partner(年干))
    干合: 甲↔己, 乙↔庚, 丙↔辛, 丁↔壬, 戊↔癸
    """

    def test_tarou_example(self) -> None:
        """書籍の太郎さん例: 日干=庚, 年干=戊 → 干合相手=癸 → 調舒星."""
        school = StandardSchool()
        result = calculate_shimeisei(
            day_stem=TenStem.KANOE,  # 庚
            year_stem=TenStem.TSUCHINOE,  # 戊
            school=school,
        )
        assert result == MajorStar.CHOUJYO  # 調舒星

    @pytest.mark.parametrize(
        ("day_stem", "year_stem", "expected"),
        [
            # 年干=甲 → 干合相手=己
            (TenStem.KINOE, TenStem.KINOE, MajorStar.SHIROKU),  # 甲×己: 木剋土・異=司禄星
            (TenStem.HINOE, TenStem.KINOE, MajorStar.CHOUJYO),  # 丙×己: 火生土・異=調舒星
            # 年干=乙 → 干合相手=庚
            (TenStem.KINOE, TenStem.KINOTO, MajorStar.SHAKI),  # 甲×庚: 金剋木(官)・同=車騎星
            (TenStem.KANOE, TenStem.KINOTO, MajorStar.KANSAKU),  # 庚×庚: 比劫・同=貫索星
            # 年干=丙 → 干合相手=辛
            (TenStem.KINOE, TenStem.HINOE, MajorStar.KENGYU),  # 甲×辛: 金剋木(官)・異=牽牛星
            (TenStem.KANOTO, TenStem.HINOE, MajorStar.KANSAKU),  # 辛×辛: 比劫・同=貫索星
            # 年干=丁 → 干合相手=壬
            (TenStem.KINOE, TenStem.HINOTO, MajorStar.RYUKOU),  # 甲×壬: 水生木(印)・同=龍高星
            (TenStem.MIZUNOE, TenStem.HINOTO, MajorStar.KANSAKU),  # 壬×壬: 比劫・同=貫索星
            # 年干=戊 → 干合相手=癸
            (TenStem.KINOE, TenStem.TSUCHINOE, MajorStar.GYOKUDO),  # 甲×癸: 水生木(印)・異=玉堂星
            (TenStem.KANOE, TenStem.TSUCHINOE, MajorStar.CHOUJYO),  # 庚×癸: 金生水(食)・異=調舒星
            # 年干=己 → 干合相手=甲
            (TenStem.KINOE, TenStem.TSUCHINOTO, MajorStar.KANSAKU),  # 甲×甲: 比劫・同=貫索星
            (TenStem.KANOE, TenStem.TSUCHINOTO, MajorStar.ROKUZON),  # 庚×甲: 金剋木(財)・同=禄存星
            # 年干=庚 → 干合相手=乙
            (TenStem.KINOE, TenStem.KANOE, MajorStar.SEKIMON),  # 甲×乙: 比劫・異=石門星
            (TenStem.KANOE, TenStem.KANOE, MajorStar.SHIROKU),  # 庚×乙: 金剋木(財)・異=司禄星
            # 年干=辛 → 干合相手=丙
            (TenStem.KINOE, TenStem.KANOTO, MajorStar.HOUKAKU),  # 甲×丙: 木生火(食)・同=鳳閣星
            (TenStem.KANOE, TenStem.KANOTO, MajorStar.SHAKI),  # 庚×丙: 火剋金(官)・同=車騎星
            # 年干=壬 → 干合相手=丁
            (TenStem.KINOE, TenStem.MIZUNOE, MajorStar.CHOUJYO),  # 甲×丁: 木生火(食)・異=調舒星
            (TenStem.KANOE, TenStem.MIZUNOE, MajorStar.KENGYU),  # 庚×丁: 火剋金(官)・異=牽牛星
            # 年干=癸 → 干合相手=戊
            (TenStem.KINOE, TenStem.MIZUNOTO, MajorStar.ROKUZON),  # 甲×戊: 木剋土(財)・同=禄存星
            (TenStem.KANOE, TenStem.MIZUNOTO, MajorStar.RYUKOU),  # 庚×戊: 土生金(印)・同=龍高星
        ],
        ids=[
            "甲×甲(→己)=司禄星",
            "丙×甲(→己)=調舒星",
            "甲×乙(→庚)=車騎星",
            "庚×乙(→庚)=貫索星",
            "甲×丙(→辛)=牽牛星",
            "辛×丙(→辛)=貫索星",
            "甲×丁(→壬)=龍高星",
            "壬×丁(→壬)=貫索星",
            "甲×戊(→癸)=玉堂星",
            "庚×戊(→癸)=調舒星_太郎例",
            "甲×己(→甲)=貫索星",
            "庚×己(→甲)=禄存星",
            "甲×庚(→乙)=石門星",
            "庚×庚(→乙)=司禄星",
            "甲×辛(→丙)=鳳閣星",
            "庚×辛(→丙)=車騎星",
            "甲×壬(→丁)=調舒星",
            "庚×壬(→丁)=牽牛星",
            "甲×癸(→戊)=禄存星",
            "庚×癸(→戊)=龍高星",
        ],
    )
    def test_various_combinations(
        self,
        day_stem: TenStem,
        year_stem: TenStem,
        expected: MajorStar,
    ) -> None:
        """様々な日干×年干の組み合わせで使命星が正しく算出される."""
        school = StandardSchool()
        result = calculate_shimeisei(
            day_stem=day_stem,
            year_stem=year_stem,
            school=school,
        )
        assert result == expected

    def test_returns_major_star_type(self) -> None:
        """戻り値が MajorStar 型であること."""
        school = StandardSchool()
        result = calculate_shimeisei(
            day_stem=TenStem.KINOE,
            year_stem=TenStem.KINOE,
            school=school,
        )
        assert isinstance(result, MajorStar)
