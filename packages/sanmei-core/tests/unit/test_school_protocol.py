"""SchoolProtocol の構造型テスト."""

from __future__ import annotations

from typing import Literal

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar
from sanmei_core.protocols.school import SchoolProtocol
from sanmei_core.protocols.setsuiri import SetsuiriProvider


class _StubSchool:
    """SchoolProtocol を満たすスタブ."""

    @property
    def name(self) -> str:
        return "stub"

    def get_hidden_stems(self, branch: TwelveBranch) -> HiddenStems:
        return HiddenStems(hongen=TenStem.KINOE)

    def determine_major_star(self, day_stem: TenStem, target_stem: TenStem) -> MajorStar:
        return MajorStar.KANSAKU

    def get_teiou_branch(self, stem: TenStem) -> TwelveBranch:
        return TwelveBranch.U

    def get_setsuiri_provider(self) -> SetsuiriProvider:
        raise NotImplementedError

    def get_taiun_start_age_rounding(self) -> Literal["floor", "round"]:
        return "floor"


def test_stub_satisfies_protocol() -> None:
    school: SchoolProtocol = _StubSchool()
    assert school.name == "stub"
    assert school.get_hidden_stems(TwelveBranch.NE).hongen == TenStem.KINOE
    assert school.determine_major_star(TenStem.KINOE, TenStem.KINOE) == MajorStar.KANSAKU
    assert school.get_teiou_branch(TenStem.KINOE) == TwelveBranch.U
