"""蔵干（ぞうかん）のドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel

from sanmei_core.domain.kanshi import TenStem


class HiddenStems(BaseModel, frozen=True):
    """蔵干（二十八元）.

    各十二支の内部に格納された十干。本元（主）・中元（副）・初元（従）の最大3つ。
    算命学の体系に基づく。中元は三合会局で決定される。
    """

    hongen: TenStem
    """本元: その地支を象徴する主干。"""
    chuugen: TenStem | None = None
    """中元: 三合会局に基づく干。"""
    shogen: TenStem | None = None
    """初元: 節入り直後に現れる前季の残り気。"""
