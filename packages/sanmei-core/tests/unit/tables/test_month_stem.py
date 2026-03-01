from sanmei_core.domain.kanshi import TenStem
from sanmei_core.tables.month_stem import get_month_stem


class TestGoKoTonNenHou:
    """五虎遁年法テスト — 年干から各月の天干を決定."""

    def test_kinoe_year_tora_month(self) -> None:
        """甲年の寅月（1月）は丙."""
        assert get_month_stem(TenStem.KINOE, 1) == TenStem.HINOE

    def test_ki_year_tora_month(self) -> None:
        """己年の寅月（1月）も丙."""
        assert get_month_stem(TenStem.TSUCHINOTO, 1) == TenStem.HINOE

    def test_kinoe_year_u_month(self) -> None:
        """甲年の卯月（2月）は丁."""
        assert get_month_stem(TenStem.KINOE, 2) == TenStem.HINOTO

    def test_kinoto_year_tora_month(self) -> None:
        """乙年の寅月（1月）は戊."""
        assert get_month_stem(TenStem.KINOTO, 1) == TenStem.TSUCHINOE

    def test_all_five_patterns_tora(self) -> None:
        """五虎遁年法の全5パターン（寅月）."""
        expected = {
            TenStem.KINOE: TenStem.HINOE,  # 甲 → 丙
            TenStem.KINOTO: TenStem.TSUCHINOE,  # 乙 → 戊
            TenStem.HINOE: TenStem.KANOE,  # 丙 → 庚
            TenStem.HINOTO: TenStem.MIZUNOE,  # 丁 → 壬
            TenStem.TSUCHINOE: TenStem.KINOE,  # 戊 → 甲
            TenStem.TSUCHINOTO: TenStem.HINOE,  # 己 → 丙
            TenStem.KANOE: TenStem.TSUCHINOE,  # 庚 → 戊
            TenStem.KANOTO: TenStem.KANOE,  # 辛 → 庚
            TenStem.MIZUNOE: TenStem.MIZUNOE,  # 壬 → 壬
            TenStem.MIZUNOTO: TenStem.KINOE,  # 癸 → 甲
        }
        for year_stem, expected_month_stem in expected.items():
            assert get_month_stem(year_stem, 1) == expected_month_stem, f"year_stem={year_stem.name}"

    def test_month_12_wraps(self) -> None:
        """甲年の丑月（12月）は丁."""
        # 丙(寅) + 11 = 丁(丑) ... (2 + 11) % 10 = 3 = 丁
        assert get_month_stem(TenStem.KINOE, 12) == TenStem.HINOTO
