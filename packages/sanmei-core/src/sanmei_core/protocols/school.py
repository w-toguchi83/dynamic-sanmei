"""SchoolProtocol — 流派固有ロジックの統合インターフェース."""

from __future__ import annotations

from typing import Protocol

from sanmei_core.domain.hidden_stems import HiddenStems
from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.domain.star import MajorStar
from sanmei_core.protocols.setsuiri import SetsuiriProvider


class SchoolProtocol(Protocol):
    """流派固有ロジックの統合インターフェース.

    蔵干テーブル・十大主星判定・十二運帝旺支・節入り日計算の
    全差異点を一つの Protocol にまとめる。
    """

    @property
    def name(self) -> str:
        """流派名."""
        ...

    def get_hidden_stems(self, branch: TwelveBranch) -> HiddenStems:
        """地支から蔵干を取得."""
        ...

    def determine_major_star(self, day_stem: TenStem, target_stem: TenStem) -> MajorStar:
        """日干と対象干から十大主星を判定."""
        ...

    def get_teiou_branch(self, stem: TenStem) -> TwelveBranch:
        """十干の帝旺支（十二大従星算出用）を取得."""
        ...

    def get_setsuiri_provider(self) -> SetsuiriProvider:
        """節入り日プロバイダを取得."""
        ...
