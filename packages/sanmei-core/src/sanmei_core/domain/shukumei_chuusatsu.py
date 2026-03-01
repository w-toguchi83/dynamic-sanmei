"""宿命中殺（しゅくめいちゅうさつ）のドメインモデル."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ShukumeiChuusatsuPosition(Enum):
    """宿命中殺が当たる位置."""

    YEAR_BRANCH = "年支中殺"
    MONTH_BRANCH = "月支中殺"
    DAY_BRANCH = "日支中殺"
    YEAR_STEM = "年干中殺"
    MONTH_STEM = "月干中殺"


class ShukumeiChuusatsu(BaseModel, frozen=True):
    """宿命中殺."""

    position: ShukumeiChuusatsuPosition
