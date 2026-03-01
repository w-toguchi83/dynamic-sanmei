"""五行バランス算出のテスト."""

from __future__ import annotations

from sanmei_core.calculators.gogyo_balance import calculate_gogyo_balance
from sanmei_core.domain.gogyo import GoGyo
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars


def _make_pillars(
    year_stem: TenStem,
    month_stem: TenStem,
    day_stem: TenStem,
) -> ThreePillars:
    return ThreePillars(
        year=Kanshi(stem=year_stem, branch=TwelveBranch.NE, index=0),
        month=Kanshi(stem=month_stem, branch=TwelveBranch.NE, index=0),
        day=Kanshi(stem=day_stem, branch=TwelveBranch.NE, index=0),
    )


class TestCalculateGogyoBalance:
    def test_stem_count_all_wood(self) -> None:
        """天干が全て木（甲甲甲）の場合、stem_count.wood == 3."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.KINOE, TenStem.KINOE)
        hidden = {
            "year": HiddenStems(main=TenStem.MIZUNOTO),
            "month": HiddenStems(main=TenStem.MIZUNOTO),
            "day": HiddenStems(main=TenStem.MIZUNOTO),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.stem_count.wood == 3
        assert balance.stem_count.fire == 0

    def test_branch_count_includes_hidden_stems(self) -> None:
        """蔵干の本気・中気・余気が全てカウントされる."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.KINOE, TenStem.KINOE)
        # 寅の蔵干: 甲(木), 丙(火), 戊(土)
        hidden = {
            "year": HiddenStems(
                main=TenStem.KINOE,
                middle=TenStem.HINOE,
                minor=TenStem.TSUCHINOE,
            ),
            "month": HiddenStems(main=TenStem.KINOE),
            "day": HiddenStems(main=TenStem.MIZUNOTO),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.branch_count.wood == 2  # 甲 + 甲
        assert balance.branch_count.fire == 1  # 丙
        assert balance.branch_count.earth == 1  # 戊
        assert balance.branch_count.water == 1  # 癸

    def test_total_count_is_sum(self) -> None:
        """total_count は stem_count + branch_count."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.HINOE, TenStem.KANOE)
        hidden = {
            "year": HiddenStems(main=TenStem.MIZUNOTO),
            "month": HiddenStems(main=TenStem.MIZUNOTO),
            "day": HiddenStems(main=TenStem.MIZUNOTO),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.total_count.wood == balance.stem_count.wood + balance.branch_count.wood
        assert balance.total_count.fire == balance.stem_count.fire + balance.branch_count.fire
        assert balance.total_count.total == balance.stem_count.total + balance.branch_count.total

    def test_dominant_is_highest(self) -> None:
        """dominant は最も多い五行."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.KINOTO, TenStem.KINOE)
        hidden = {
            "year": HiddenStems(main=TenStem.KINOE),
            "month": HiddenStems(main=TenStem.KINOE),
            "day": HiddenStems(main=TenStem.KINOE),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.dominant == GoGyo.WOOD

    def test_lacking_identifies_missing(self) -> None:
        """lacking は不在の五行を列挙."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.KINOTO, TenStem.KINOE)
        hidden = {
            "year": HiddenStems(main=TenStem.KINOE),
            "month": HiddenStems(main=TenStem.KINOE),
            "day": HiddenStems(main=TenStem.KINOE),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        lacking = set(balance.lacking)
        assert GoGyo.FIRE in lacking
        assert GoGyo.EARTH in lacking
        assert GoGyo.METAL in lacking
        assert GoGyo.WATER in lacking

    def test_day_stem_gogyo(self) -> None:
        """day_stem_gogyo は日干の五行."""
        pillars = _make_pillars(TenStem.KINOE, TenStem.HINOE, TenStem.MIZUNOE)
        hidden = {
            "year": HiddenStems(main=TenStem.KINOE),
            "month": HiddenStems(main=TenStem.KINOE),
            "day": HiddenStems(main=TenStem.KINOE),
        }
        balance = calculate_gogyo_balance(pillars, hidden)
        assert balance.day_stem_gogyo == GoGyo.WATER
