"""五虎遁年法 — 年干から月干を決定するテーブル."""

from sanmei_core.domain.kanshi import TenStem

# 年干 → 寅月（算命学1月）の天干
# 甲・己 → 丙, 乙・庚 → 戊, 丙・辛 → 庚, 丁・壬 → 壬, 戊・癸 → 甲
_TORA_STEM: dict[TenStem, TenStem] = {
    TenStem.KINOE: TenStem.HINOE,
    TenStem.TSUCHINOTO: TenStem.HINOE,
    TenStem.KINOTO: TenStem.TSUCHINOE,
    TenStem.KANOE: TenStem.TSUCHINOE,
    TenStem.HINOE: TenStem.KANOE,
    TenStem.KANOTO: TenStem.KANOE,
    TenStem.HINOTO: TenStem.MIZUNOE,
    TenStem.MIZUNOE: TenStem.MIZUNOE,
    TenStem.TSUCHINOE: TenStem.KINOE,
    TenStem.MIZUNOTO: TenStem.KINOE,
}


def get_month_stem(year_stem: TenStem, sanmei_month: int) -> TenStem:
    """五虎遁年法で月干を算出.

    Args:
        year_stem: 年柱の天干
        sanmei_month: 算命学上の月 (1=寅月〜12=丑月)

    Returns:
        該当月の天干
    """
    tora_stem = _TORA_STEM[year_stem]
    return TenStem((tora_stem.value + sanmei_month - 1) % 10)
