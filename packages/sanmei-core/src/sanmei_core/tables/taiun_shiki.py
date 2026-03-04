"""大運四季表のマッピングテーブル."""

from sanmei_core.domain.kanshi import TwelveBranch
from sanmei_core.domain.star import SubsidiaryStar
from sanmei_core.domain.taiun_shiki import LifeCycle, Season

BRANCH_TO_SEASON: dict[TwelveBranch, Season] = {
    TwelveBranch.TORA: Season.SPRING,
    TwelveBranch.U: Season.SPRING,
    TwelveBranch.TATSU: Season.SPRING,
    TwelveBranch.MI: Season.SUMMER,
    TwelveBranch.UMA: Season.SUMMER,
    TwelveBranch.HITSUJI: Season.SUMMER,
    TwelveBranch.SARU: Season.AUTUMN,
    TwelveBranch.TORI: Season.AUTUMN,
    TwelveBranch.INU: Season.AUTUMN,
    TwelveBranch.I: Season.WINTER,
    TwelveBranch.NE: Season.WINTER,
    TwelveBranch.USHI: Season.WINTER,
}

SUBSIDIARY_STAR_TO_LIFE_CYCLE: dict[SubsidiaryStar, LifeCycle] = {
    SubsidiaryStar.TENPOU: LifeCycle.TAIJI,
    SubsidiaryStar.TENIN: LifeCycle.AKAGO,
    SubsidiaryStar.TENKI: LifeCycle.JIDOU,
    SubsidiaryStar.TENKOU: LifeCycle.SEISHONEN,
    SubsidiaryStar.TENNAN: LifeCycle.SEINEN,
    SubsidiaryStar.TENROKU: LifeCycle.SOUNEN,
    SubsidiaryStar.TENSHOU: LifeCycle.KACHOU,
    SubsidiaryStar.TENDOU: LifeCycle.ROUJIN,
    SubsidiaryStar.TENKO: LifeCycle.BYOUNIN,
    SubsidiaryStar.TENKYOKU: LifeCycle.SHININ,
    SubsidiaryStar.TENKU: LifeCycle.NYUUBO,
    SubsidiaryStar.TENCHI: LifeCycle.ANOYO,
}
