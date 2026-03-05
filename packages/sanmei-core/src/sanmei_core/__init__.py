"""算命学コアロジック - 純粋計算ライブラリ."""

from sanmei_core.calculators.compatibility import analyze_compatibility
from sanmei_core.calculators.fortune import (
    calculate_nenun,
    calculate_taiun,
    determine_direction,
)
from sanmei_core.calculators.fortune_analyzer import analyze_fortune_interaction
from sanmei_core.calculators.gogyo_balance import calculate_gogyo_balance
from sanmei_core.calculators.isouhou import (
    analyze_branch_interactions,
    analyze_isouhou,
    analyze_stem_interactions,
)
from sanmei_core.calculators.meishiki_calculator import MeishikiCalculator
from sanmei_core.calculators.pillar_calculator import SanmeiCalendar
from sanmei_core.calculators.shimeisei import calculate_shimeisei
from sanmei_core.calculators.shukumei_chuusatsu import calculate_shukumei_chuusatsu
from sanmei_core.calculators.solar_longitude import MeeusSetsuiriProvider
from sanmei_core.calculators.taiun_shiki import calculate_taiun_shiki
from sanmei_core.calculators.zoukan_tokutei import determine_active_hidden_stem
from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.domain.compatibility import (
    CompatibilityResult,
    CrossIsouhou,
    GoGyoComplement,
    NikkanRelation,
    NikkanRelationType,
    TenchuusatsuCompatibility,
)
from sanmei_core.domain.errors import (
    DateOutOfRangeError,
    SanmeiError,
    SetsuiriNotFoundError,
)
from sanmei_core.domain.fortune import (
    FortuneInteraction,
    Gender,
    Nenun,
    Taiun,
    TaiunChart,
)
from sanmei_core.domain.gogyo import GoGyo, InYou
from sanmei_core.domain.gogyo_balance import GoGyoBalance, GoGyoCount
from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.isouhou import (
    BranchInteraction,
    BranchInteractionType,
    IsouhouResult,
    StemInteraction,
    StemInteractionType,
)
from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch
from sanmei_core.domain.meishiki import MajorStarChart, Meishiki, SubsidiaryStarChart
from sanmei_core.domain.pillar import ThreePillars
from sanmei_core.domain.shukumei_chuusatsu import (
    ShukumeiChuusatsu,
    ShukumeiChuusatsuPosition,
)
from sanmei_core.domain.star import MajorStar, SubsidiaryStar
from sanmei_core.domain.taiun_shiki import (
    LifeCycle,
    Season,
    TaiunShikiChart,
    TaiunShikiEntry,
)
from sanmei_core.domain.tenchuusatsu import Tenchuusatsu, TenchuusatsuType
from sanmei_core.domain.zoukan_tokutei import ActiveHiddenStem, HiddenStemType, ZoukanTokutei
from sanmei_core.protocols.school import SchoolProtocol
from sanmei_core.protocols.setsuiri import SetsuiriProvider
from sanmei_core.schools.registry import SchoolRegistry
from sanmei_core.schools.standard import StandardSchool

__all__ = [
    "ActiveHiddenStem",
    "CompatibilityResult",
    "CrossIsouhou",
    "BranchInteraction",
    "BranchInteractionType",
    "DateOutOfRangeError",
    "FortuneInteraction",
    "Gender",
    "GoGyo",
    "GoGyoBalance",
    "GoGyoComplement",
    "GoGyoCount",
    "HiddenStemType",
    "HiddenStems",
    "InYou",
    "IsouhouResult",
    "Kanshi",
    "LifeCycle",
    "MajorStar",
    "MajorStarChart",
    "MeeusSetsuiriProvider",
    "Meishiki",
    "MeishikiCalculator",
    "Nenun",
    "NikkanRelation",
    "NikkanRelationType",
    "SanmeiCalendar",
    "SanmeiError",
    "SchoolProtocol",
    "SchoolRegistry",
    "Season",
    "SetsuiriDate",
    "SetsuiriNotFoundError",
    "SetsuiriProvider",
    "ShukumeiChuusatsu",
    "ShukumeiChuusatsuPosition",
    "SolarTerm",
    "StandardSchool",
    "StemInteraction",
    "StemInteractionType",
    "SubsidiaryStar",
    "SubsidiaryStarChart",
    "Taiun",
    "TaiunChart",
    "TaiunShikiChart",
    "TaiunShikiEntry",
    "TenStem",
    "Tenchuusatsu",
    "TenchuusatsuCompatibility",
    "TenchuusatsuType",
    "ThreePillars",
    "TwelveBranch",
    "ZoukanTokutei",
    "analyze_branch_interactions",
    "analyze_compatibility",
    "analyze_fortune_interaction",
    "analyze_isouhou",
    "analyze_stem_interactions",
    "calculate_gogyo_balance",
    "calculate_nenun",
    "calculate_shimeisei",
    "calculate_shukumei_chuusatsu",
    "calculate_taiun",
    "calculate_taiun_shiki",
    "determine_active_hidden_stem",
    "determine_direction",
]
