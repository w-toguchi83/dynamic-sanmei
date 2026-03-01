from datetime import UTC, datetime

from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm
from sanmei_core.protocols.setsuiri import SetsuiriProvider


class StubProvider:
    """SetsuiriProvider Protocol を満たすスタブ."""

    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        return [
            SetsuiriDate(
                year=year,
                month=1,
                datetime_utc=datetime(year, 2, 4, 8, 0, tzinfo=UTC),
                solar_term=SolarTerm.RISSHUN,
            ),
        ]

    def get_risshun(self, year: int) -> SetsuiriDate:
        return self.get_setsuiri_dates(year)[0]


def test_stub_satisfies_protocol() -> None:
    provider: SetsuiriProvider = StubProvider()
    result = provider.get_risshun(2024)
    assert result.solar_term == SolarTerm.RISSHUN
