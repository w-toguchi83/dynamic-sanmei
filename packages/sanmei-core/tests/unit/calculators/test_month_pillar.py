from datetime import UTC, datetime, timedelta, timezone

from sanmei_core.calculators.month_pillar import month_pillar
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.kanshi import TenStem, TwelveBranch

JST = timezone(timedelta(hours=9))

# 節気の太陽黄経順（算命学月1〜12）に対応する SolarTerm
_SETSU_TERMS = [
    SolarTerm.RISSHUN,  # 1月 寅
    SolarTerm.KEICHITSU,  # 2月 卯
    SolarTerm.SEIMEI,  # 3月 辰
    SolarTerm.RIKKA,  # 4月 巳
    SolarTerm.BOUSHU,  # 5月 午
    SolarTerm.SHOUSHO,  # 6月 未
    SolarTerm.RISSHUU,  # 7月 申
    SolarTerm.HAKURO,  # 8月 酉
    SolarTerm.KANRO,  # 9月 戌
    SolarTerm.RITTOU,  # 10月 亥
    SolarTerm.TAISETSU,  # 11月 子
    SolarTerm.SHOUKAN,  # 12月 丑
]

# 2024年のおおよその節入り日（JST、テスト用固定データ）
_SETSUIRI_2024_JST = [
    (2024, 2, 4, 17),  # 立春
    (2024, 3, 5, 11),  # 啓蟄
    (2024, 4, 4, 16),  # 清明
    (2024, 5, 5, 9),  # 立夏
    (2024, 6, 5, 13),  # 芒種
    (2024, 7, 6, 23),  # 小暑
    (2024, 8, 7, 9),  # 立秋
    (2024, 9, 7, 12),  # 白露
    (2024, 10, 8, 4),  # 寒露
    (2024, 11, 7, 7),  # 立冬
    (2024, 12, 7, 0),  # 大雪
    (2025, 1, 5, 11),  # 小寒（翌年1月）
]


def _make_setsuiri_dates() -> list[SetsuiriDate]:
    result = []
    for i, (y, m, d, h) in enumerate(_SETSUIRI_2024_JST):
        jst_dt = datetime(y, m, d, h, 0, tzinfo=JST)
        result.append(
            SetsuiriDate(
                year=2024,
                month=i + 1,
                datetime_utc=jst_dt.astimezone(UTC),
                solar_term=_SETSU_TERMS[i],
            )
        )
    return result


class TestMonthPillar:
    def test_march_2024_is_u_month(self) -> None:
        """2024年3月15日 → 啓蟄(3/5)後、清明(4/4)前 → 卯月（算命学2月）.

        月支 = 卯(3)。年干=甲 → 寅月天干=丙 → 卯月天干=丁。
        """
        dates = _make_setsuiri_dates()
        year_stem = TenStem.KINOE  # 甲年
        dt = datetime(2024, 3, 15, 12, 0, tzinfo=JST)
        k = month_pillar(dt, dates, year_stem, tz=JST)
        assert k.branch == TwelveBranch.U  # 卯
        assert k.stem == TenStem.HINOTO  # 丁

    def test_feb_2024_before_risshun_is_previous_chou(self) -> None:
        """2024年2月1日 → 立春(2/4)前 → 丑月（算命学12月）.

        前年の最後の月。year_stem は前年(癸)のもの。
        癸年 → 寅月天干=甲 → 丑月(12月)天干 = (甲+11) % 10 = 乙
        """
        dates = _make_setsuiri_dates()
        year_stem = TenStem.MIZUNOTO  # 癸年（前年）
        dt = datetime(2024, 2, 1, 12, 0, tzinfo=JST)
        k = month_pillar(dt, dates, year_stem, tz=JST)
        assert k.branch == TwelveBranch.USHI  # 丑

    def test_risshun_boundary_exact(self) -> None:
        """立春の瞬間 → 寅月."""
        dates = _make_setsuiri_dates()
        year_stem = TenStem.KINOE
        dt = datetime(2024, 2, 4, 17, 0, tzinfo=JST)
        k = month_pillar(dt, dates, year_stem, tz=JST)
        assert k.branch == TwelveBranch.TORA  # 寅

    def test_all_five_year_stem_patterns(self) -> None:
        """五虎遁年法の全5パターンで寅月の月干を検証."""
        dates = _make_setsuiri_dates()
        dt = datetime(2024, 2, 10, 12, 0, tzinfo=JST)  # 寅月中
        expected_pairs = [
            (TenStem.KINOE, TenStem.HINOE),  # 甲 → 丙寅
            (TenStem.KINOTO, TenStem.TSUCHINOE),  # 乙 → 戊寅
            (TenStem.HINOE, TenStem.KANOE),  # 丙 → 庚寅
            (TenStem.HINOTO, TenStem.MIZUNOE),  # 丁 → 壬寅
            (TenStem.TSUCHINOE, TenStem.KINOE),  # 戊 → 甲寅
        ]
        for year_stem, expected_month_stem in expected_pairs:
            k = month_pillar(dt, dates, year_stem, tz=JST)
            assert k.stem == expected_month_stem, f"year_stem={year_stem.name}"
            assert k.branch == TwelveBranch.TORA
