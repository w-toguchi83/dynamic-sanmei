from datetime import UTC, datetime

from sanmei_core.domain.calendar import SetsuiriDate, SolarTerm


class TestSolarTerm:
    def test_setsu_terms_count(self) -> None:
        """節気は12個."""
        setsu = [t for t in SolarTerm if t.is_setsu]
        assert len(setsu) == 12

    def test_chuu_terms_count(self) -> None:
        """中気は12個."""
        chuu = [t for t in SolarTerm if not t.is_setsu]
        assert len(chuu) == 12

    def test_risshun_longitude(self) -> None:
        assert SolarTerm.RISSHUN.longitude == 315.0

    def test_keichitsu_longitude(self) -> None:
        assert SolarTerm.KEICHITSU.longitude == 345.0

    def test_shunbun_is_chuu(self) -> None:
        """春分は中気."""
        assert not SolarTerm.SHUNBUN.is_setsu

    def test_risshun_is_setsu(self) -> None:
        """立春は節気."""
        assert SolarTerm.RISSHUN.is_setsu

    def test_risshun_sanmei_month(self) -> None:
        """立春は算命学1月（寅月）."""
        assert SolarTerm.RISSHUN.sanmei_month == 1


class TestSetsuiriDate:
    def test_create(self) -> None:
        sd = SetsuiriDate(
            year=2024,
            month=1,
            datetime_utc=datetime(2024, 2, 4, 8, 27, tzinfo=UTC),
            solar_term=SolarTerm.RISSHUN,
        )
        assert sd.year == 2024
        assert sd.month == 1
        assert sd.solar_term == SolarTerm.RISSHUN
