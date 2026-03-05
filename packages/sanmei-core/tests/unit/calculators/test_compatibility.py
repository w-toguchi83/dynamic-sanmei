"""相性鑑定のテスト."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sanmei_core import MeishikiCalculator, SchoolRegistry
from sanmei_core.calculators.compatibility import (
    _analyze_cross_isouhou,
    _analyze_gogyo_complement,
    _analyze_nikkan,
    _analyze_tenchuusatsu_compat,
    analyze_compatibility,
)
from sanmei_core.domain.compatibility import NikkanRelationType
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.kanshi import TenStem

JST = timezone(timedelta(hours=9))


def _make_school():  # noqa: ANN202
    return SchoolRegistry.create_default().default()


def _make_meishiki(year: int, month: int, day: int, hour: int = 0, minute: int = 0):  # noqa: ANN202
    school = _make_school()
    calc = MeishikiCalculator(school)
    dt = datetime(year, month, day, hour, minute, tzinfo=JST)
    return calc.calculate(dt)


class TestAnalyzeNikkan:
    def test_kangou(self) -> None:
        """甲・己 → 干合（土）."""
        result = _analyze_nikkan(TenStem.KINOE, TenStem.TSUCHINOTO)
        assert result.relation_type == NikkanRelationType.KANGOU
        assert result.kangou_gogyo == GoGyo.EARTH

    def test_hikaku(self) -> None:
        """同五行 → 比和."""
        result = _analyze_nikkan(TenStem.KINOE, TenStem.KINOTO)
        assert result.relation_type == NikkanRelationType.HIKAKU
        assert result.gogyo_a == GoGyo.WOOD
        assert result.gogyo_b == GoGyo.WOOD

    def test_sougou(self) -> None:
        """木→火 → 相生."""
        result = _analyze_nikkan(TenStem.KINOE, TenStem.HINOE)
        assert result.relation_type == NikkanRelationType.SOUGOU

    def test_sougou_reverse(self) -> None:
        """火→木 → 相生（逆方向でも相生）."""
        result = _analyze_nikkan(TenStem.HINOE, TenStem.KINOE)
        assert result.relation_type == NikkanRelationType.SOUGOU

    def test_soukoku(self) -> None:
        """木→土 → 相剋."""
        result = _analyze_nikkan(TenStem.KINOE, TenStem.TSUCHINOE)
        assert result.relation_type == NikkanRelationType.SOUKOKU

    def test_soukoku_reverse(self) -> None:
        """土→木（木剋土の逆）→ 相剋."""
        result = _analyze_nikkan(TenStem.TSUCHINOE, TenStem.KINOE)
        assert result.relation_type == NikkanRelationType.SOUKOKU

    def test_kangou_all_pairs(self) -> None:
        """全5組の干合ペアをチェック."""
        pairs = [
            (TenStem.KINOE, TenStem.TSUCHINOTO, GoGyo.EARTH),
            (TenStem.KINOTO, TenStem.KANOE, GoGyo.METAL),
            (TenStem.HINOE, TenStem.KANOTO, GoGyo.WATER),
            (TenStem.HINOTO, TenStem.MIZUNOE, GoGyo.WOOD),
            (TenStem.TSUCHINOE, TenStem.MIZUNOTO, GoGyo.FIRE),
        ]
        for stem_a, stem_b, expected_gogyo in pairs:
            result = _analyze_nikkan(stem_a, stem_b)
            assert result.relation_type == NikkanRelationType.KANGOU
            assert result.kangou_gogyo == expected_gogyo

    def test_no_kangou_gogyo_when_not_kangou(self) -> None:
        """干合でない場合はkangou_gogyoがNone."""
        result = _analyze_nikkan(TenStem.KINOE, TenStem.HINOE)
        assert result.kangou_gogyo is None


class TestAnalyzeGogyoComplement:
    def test_complement(self) -> None:
        """五行補完の基本テスト."""
        meishiki_a = _make_meishiki(2000, 1, 15, 14, 30)
        meishiki_b = _make_meishiki(1990, 5, 20, 10, 0)
        result = _analyze_gogyo_complement(meishiki_a, meishiki_b)
        # 結果が正しい型であることを確認
        assert isinstance(result.lacking_a, tuple)
        assert isinstance(result.lacking_b, tuple)
        assert isinstance(result.complemented_by_a, tuple)
        assert isinstance(result.complemented_by_b, tuple)
        # 補完されたものは相手の欠にあるもの
        for g in result.complemented_by_b:
            assert g in result.lacking_a
        for g in result.complemented_by_a:
            assert g in result.lacking_b


class TestAnalyzeTenchuusatsuCompat:
    def test_basic(self) -> None:
        """天中殺の相性チェック."""
        meishiki_a = _make_meishiki(2000, 1, 15)
        meishiki_b = _make_meishiki(1995, 8, 20)
        result = _analyze_tenchuusatsu_compat(meishiki_a, meishiki_b)
        assert result.type_a == meishiki_a.tenchuusatsu.type
        assert result.type_b == meishiki_b.tenchuusatsu.type
        # 天中殺支が命式に含まれるかは地支次第
        assert isinstance(result.a_branches_in_b, tuple)
        assert isinstance(result.b_branches_in_a, tuple)


class TestAnalyzeCrossIsouhou:
    def test_basic(self) -> None:
        """クロスチャートの位相法分析."""
        meishiki_a = _make_meishiki(2000, 1, 15, 14, 30)
        meishiki_b = _make_meishiki(1990, 5, 20, 10, 0)
        result = _analyze_cross_isouhou(meishiki_a, meishiki_b)
        assert isinstance(result.stem_interactions, tuple)
        assert isinstance(result.branch_interactions, tuple)


class TestAnalyzeCompatibility:
    def test_full_analysis(self) -> None:
        """総合相性分析."""
        meishiki_a = _make_meishiki(2000, 1, 15, 14, 30)
        meishiki_b = _make_meishiki(1990, 5, 20, 10, 0)
        result = analyze_compatibility(meishiki_a, meishiki_b)

        assert result.nikkan_relation.stem_a == meishiki_a.pillars.day.stem
        assert result.nikkan_relation.stem_b == meishiki_b.pillars.day.stem
        assert result.nikkan_relation.relation_type in NikkanRelationType
        assert result.gogyo_complement is not None
        assert result.tenchuusatsu_compatibility is not None
        assert result.cross_isouhou is not None

    def test_same_person(self) -> None:
        """同一人物の相性（比和+同天中殺）."""
        meishiki = _make_meishiki(2000, 1, 15, 14, 30)
        result = analyze_compatibility(meishiki, meishiki)

        assert result.nikkan_relation.relation_type == NikkanRelationType.HIKAKU
        assert result.nikkan_relation.gogyo_a == result.nikkan_relation.gogyo_b
        assert result.tenchuusatsu_compatibility.type_a == result.tenchuusatsu_compatibility.type_b

    def test_pydantic_serialization(self) -> None:
        """Pydantic シリアライズ."""
        meishiki_a = _make_meishiki(2000, 1, 15)
        meishiki_b = _make_meishiki(1995, 8, 20)
        result = analyze_compatibility(meishiki_a, meishiki_b)
        data = result.model_dump(mode="json")
        assert "nikkan_relation" in data
        assert "gogyo_complement" in data
        assert "tenchuusatsu_compatibility" in data
        assert "cross_isouhou" in data
