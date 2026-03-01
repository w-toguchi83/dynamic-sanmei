"""JSON形式フォーマッター."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def to_json(data: Any) -> str:  # noqa: ANN401
    """Pydantic モデルまたはリストをJSON文字列に変換."""
    raw: Any
    if isinstance(data, BaseModel):
        raw = data.model_dump(mode="json")
    elif isinstance(data, list):
        raw = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in data
        ]
    else:
        raw = data
    return json.dumps(raw, ensure_ascii=False, indent=2, default=str)
