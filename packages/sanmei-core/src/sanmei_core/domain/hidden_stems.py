"""蔵干（ぞうかん）のドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel

from sanmei_core.domain.kanshi import TenStem


class HiddenStems(BaseModel, frozen=True):
    """蔵干.

    各十二支の内部に格納された十干。本気（主）・中気（副）・余気（従）の最大3つ。
    """

    main: TenStem
    middle: TenStem | None = None
    minor: TenStem | None = None
