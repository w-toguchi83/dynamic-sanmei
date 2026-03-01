"""Click custom parameter types."""

from __future__ import annotations

from typing import Any

import click
from sanmei_core import Gender

_GENDER_MAP: dict[str, Gender] = {
    "男": Gender.MALE,
    "male": Gender.MALE,
    "m": Gender.MALE,
    "女": Gender.FEMALE,
    "female": Gender.FEMALE,
    "f": Gender.FEMALE,
}


class GenderType(click.ParamType):
    """Gender parameter accepting 男/male/m and 女/female/f."""

    name = "gender"

    def convert(
        self,
        value: Any,  # noqa: ANN401
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> Gender:
        if isinstance(value, Gender):
            return value
        if not isinstance(value, str):
            self.fail(f"Expected string, got {type(value).__name__}", param, ctx)
        key = value.lower().strip()
        if key in _GENDER_MAP:
            return _GENDER_MAP[key]
        self.fail(
            f"'{value}' は無効な性別です。使用可能: 男/male/m, 女/female/f",
            param,
            ctx,
        )
