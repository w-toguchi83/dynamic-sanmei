"""宿命中殺算出のテスト."""

from __future__ import annotations

import pytest
from sanmei_core.calculators.shukumei_chuusatsu import calculate_shukumei_chuusatsu
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.shukumei_chuusatsu import ShukumeiChuusatsuPosition
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType


def _make_pillars(
    year_branch: TwelveBranch,
    month_branch: TwelveBranch,
    day_branch: TwelveBranch,
) -> ThreePillars:
    """テスト用三柱を作成（stemは適当）."""
    return ThreePillars(
        year=Kanshi(stem=TenStem.KINOE, branch=year_branch, index=0),
        month=Kanshi(stem=TenStem.KINOTO, branch=month_branch, index=1),
        day=Kanshi(stem=TenStem.HINOE, branch=day_branch, index=2),
    )


class TestCalculateShukumeiChuusatsu:
    def test_no_shukumei_chuusatsu(self) -> None:
        """三柱のどの地支も天中殺支に含まれない → 空リスト."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        )
        pillars = _make_pillars(TwelveBranch.NE, TwelveBranch.TORA, TwelveBranch.UMA)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        assert result == []

    def test_year_branch_chuusatsu(self) -> None:
        """年支が天中殺支 → 年支中殺 + 年干中殺."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.INU_I,
            branches=(TwelveBranch.INU, TwelveBranch.I),
        )
        pillars = _make_pillars(TwelveBranch.INU, TwelveBranch.TORA, TwelveBranch.UMA)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        positions = {sc.position for sc in result}
        assert ShukumeiChuusatsuPosition.YEAR_BRANCH in positions
        assert ShukumeiChuusatsuPosition.YEAR_STEM in positions

    def test_month_branch_chuusatsu(self) -> None:
        """月支が天中殺支 → 月支中殺 + 月干中殺."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.TORA_U,
            branches=(TwelveBranch.TORA, TwelveBranch.U),
        )
        pillars = _make_pillars(TwelveBranch.NE, TwelveBranch.U, TwelveBranch.UMA)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        positions = {sc.position for sc in result}
        assert ShukumeiChuusatsuPosition.MONTH_BRANCH in positions
        assert ShukumeiChuusatsuPosition.MONTH_STEM in positions

    def test_day_branch_chuusatsu(self) -> None:
        """日支が天中殺支 → 日支中殺のみ（日干中殺は存在しない）."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.NE_USHI,
            branches=(TwelveBranch.NE, TwelveBranch.USHI),
        )
        pillars = _make_pillars(TwelveBranch.TORA, TwelveBranch.UMA, TwelveBranch.NE)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        positions = {sc.position for sc in result}
        assert ShukumeiChuusatsuPosition.DAY_BRANCH in positions
        assert ShukumeiChuusatsuPosition.YEAR_STEM not in positions
        assert ShukumeiChuusatsuPosition.MONTH_STEM not in positions

    def test_multiple_positions(self) -> None:
        """複数の柱が天中殺支に当たる場合."""
        tc = Tenchuusatsu(
            type=TenchuusatsuType.NE_USHI,
            branches=(TwelveBranch.NE, TwelveBranch.USHI),
        )
        pillars = _make_pillars(TwelveBranch.NE, TwelveBranch.USHI, TwelveBranch.NE)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        positions = {sc.position for sc in result}
        assert ShukumeiChuusatsuPosition.YEAR_BRANCH in positions
        assert ShukumeiChuusatsuPosition.YEAR_STEM in positions
        assert ShukumeiChuusatsuPosition.MONTH_BRANCH in positions
        assert ShukumeiChuusatsuPosition.MONTH_STEM in positions
        assert ShukumeiChuusatsuPosition.DAY_BRANCH in positions

    @pytest.mark.parametrize(
        "tc_type",
        list(TenchuusatsuType),
    )
    def test_returns_list_for_all_tenchuusatsu_types(self, tc_type: TenchuusatsuType) -> None:
        """全天中殺タイプで正常にリストを返す."""
        from sanmei_core.calculators.tenchuusatsu import _GROUP_MAP

        branches = next(b for t, b in _GROUP_MAP if t == tc_type)
        tc = Tenchuusatsu(type=tc_type, branches=branches)
        pillars = _make_pillars(TwelveBranch.TORA, TwelveBranch.UMA, TwelveBranch.TORI)
        result = calculate_shukumei_chuusatsu(pillars, tc)
        assert isinstance(result, list)
