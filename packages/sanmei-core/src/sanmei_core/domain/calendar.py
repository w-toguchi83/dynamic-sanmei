"""算命暦の節入り日・二十四節気モデル."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class SolarTerm(Enum):
    """二十四節気.

    value は (太陽黄経, 節気かどうか, 算命学月 or None) のタプル。
    算命学月は節気のみに割り当て（1=寅月〜12=丑月）。中気は None。
    """

    # --- 春 ---
    RISSHUN = (315.0, True, 1)  # 立春
    USUI = (330.0, False, None)  # 雨水
    KEICHITSU = (345.0, True, 2)  # 啓蟄
    SHUNBUN = (0.0, False, None)  # 春分
    SEIMEI = (15.0, True, 3)  # 清明
    KOKUU = (30.0, False, None)  # 穀雨
    # --- 夏 ---
    RIKKA = (45.0, True, 4)  # 立夏
    SHOUMAN = (60.0, False, None)  # 小満
    BOUSHU = (75.0, True, 5)  # 芒種
    GESHI = (90.0, False, None)  # 夏至
    SHOUSHO = (105.0, True, 6)  # 小暑
    TAISHO = (120.0, False, None)  # 大暑
    # --- 秋 ---
    RISSHUU = (135.0, True, 7)  # 立秋
    SHOSHO = (150.0, False, None)  # 処暑
    HAKURO = (165.0, True, 8)  # 白露
    SHUUBUN = (180.0, False, None)  # 秋分
    KANRO = (195.0, True, 9)  # 寒露
    SOUKOU = (210.0, False, None)  # 霜降
    # --- 冬 ---
    RITTOU = (225.0, True, 10)  # 立冬
    SHOUSETSU = (240.0, False, None)  # 小雪
    TAISETSU = (255.0, True, 11)  # 大雪
    TOUJI = (270.0, False, None)  # 冬至
    SHOUKAN = (285.0, True, 12)  # 小寒
    DAIKAN = (300.0, False, None)  # 大寒

    @property
    def longitude(self) -> float:
        """太陽黄経（度）."""
        val: float = self.value[0]
        return val

    @property
    def is_setsu(self) -> bool:
        """節気かどうか（True なら月境界）."""
        val: bool = self.value[1]
        return val

    @property
    def sanmei_month(self) -> int | None:
        """算命学上の月番号（1=寅月〜12=丑月）。中気は None."""
        val: int | None = self.value[2]
        return val


class SetsuiriDate(BaseModel, frozen=True):
    """節入り日.

    特定の年・月における節気の正確な時刻を表す。
    datetime_utc は UTC で保持し、タイムゾーン変換は利用時に行う。
    """

    year: int
    month: int  # 算命学上の月 (1-12, 寅月=1)
    datetime_utc: datetime
    solar_term: SolarTerm
