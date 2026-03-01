from sanmei_core.domain.errors import (
    DateOutOfRangeError,
    SanmeiError,
    SetsuiriNotFoundError,
)


def test_sanmei_error_is_exception() -> None:
    assert issubclass(SanmeiError, Exception)


def test_date_out_of_range_is_sanmei_error() -> None:
    err = DateOutOfRangeError(1800)
    assert isinstance(err, SanmeiError)
    assert "1800" in str(err)


def test_setsuiri_not_found_is_sanmei_error() -> None:
    err = SetsuiriNotFoundError(2025)
    assert isinstance(err, SanmeiError)
    assert "2025" in str(err)
