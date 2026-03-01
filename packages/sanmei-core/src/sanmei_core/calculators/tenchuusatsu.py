"""天中殺の算出."""

from __future__ import annotations

from sanmei_core.domain.kanshi import Kanshi, TwelveBranch
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType

_GROUP_MAP: tuple[tuple[TenchuusatsuType, tuple[TwelveBranch, TwelveBranch]], ...] = (
    (TenchuusatsuType.INU_I, (TwelveBranch.INU, TwelveBranch.I)),
    (TenchuusatsuType.SARU_TORI, (TwelveBranch.SARU, TwelveBranch.TORI)),
    (TenchuusatsuType.UMA_HITSUJI, (TwelveBranch.UMA, TwelveBranch.HITSUJI)),
    (TenchuusatsuType.TATSU_MI, (TwelveBranch.TATSU, TwelveBranch.MI)),
    (TenchuusatsuType.TORA_U, (TwelveBranch.TORA, TwelveBranch.U)),
    (TenchuusatsuType.NE_USHI, (TwelveBranch.NE, TwelveBranch.USHI)),
)


def calculate_tenchuusatsu(day_kanshi: Kanshi) -> Tenchuusatsu:
    """日柱の干支から天中殺を算出.

    六十干支を10干ずつ6グループに分割。
    各グループで十二支のうち2つが欠ける → その2支が天中殺支。
    """
    group = day_kanshi.index // 10
    tc_type, branches = _GROUP_MAP[group]
    return Tenchuusatsu(type=tc_type, branches=branches)
