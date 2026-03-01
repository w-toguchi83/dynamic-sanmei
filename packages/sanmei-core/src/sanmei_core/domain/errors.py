"""算命学コアの例外定義."""


class SanmeiError(Exception):
    """sanmei-core の基底例外."""


class DateOutOfRangeError(SanmeiError):
    """対象範囲外の日付 (1864-2100) が指定された."""

    def __init__(self, year: int) -> None:
        super().__init__(f"Year {year} is out of supported range (1864-2100)")
        self.year = year


class SetsuiriNotFoundError(SanmeiError):
    """指定年の節入りデータが見つからない."""

    def __init__(self, year: int) -> None:
        super().__init__(f"Setsuiri data not found for year {year}")
        self.year = year
