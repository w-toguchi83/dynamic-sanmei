"""十大主星（じゅうだいしゅせい）・十二大従星（じゅうにだいじゅうせい）."""

from __future__ import annotations

from enum import Enum


class MajorStar(Enum):
    """十大主星."""

    KANSAKU = "貫索星"  # 比劫・陽
    SEKIMON = "石門星"  # 比劫・陰
    HOUKAKU = "鳳閣星"  # 食傷・陽
    CHOUJYO = "調舒星"  # 食傷・陰
    ROKUZON = "禄存星"  # 財星・陽
    SHIROKU = "司禄星"  # 財星・陰
    SHAKI = "車騎星"  # 官星・陽
    KENGYU = "牽牛星"  # 官星・陰
    RYUKOU = "龍高星"  # 印綬・陽
    GYOKUDO = "玉堂星"  # 印綬・陰


class SubsidiaryStar(Enum):
    """十二大従星."""

    TENPOU = "天報星"  # 胎
    TENIN = "天印星"  # 養
    TENKI = "天貴星"  # 長生
    TENKOU = "天恍星"  # 沐浴
    TENNAN = "天南星"  # 冠帯
    TENROKU = "天禄星"  # 建禄
    TENSHOU = "天将星"  # 帝旺
    TENDOU = "天堂星"  # 衰
    TENKO = "天胡星"  # 病
    TENKYOKU = "天極星"  # 死
    TENKU = "天庫星"  # 墓
    TENCHI = "天馳星"  # 絶
