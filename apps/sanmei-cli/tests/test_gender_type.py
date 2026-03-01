import pytest
from click import BadParameter
from sanmei_core import Gender

from sanmei_cli.types import GenderType


class TestGenderType:
    def setup_method(self):
        self.type = GenderType()

    @pytest.mark.parametrize(
        ("input_val", "expected"),
        [
            ("男", Gender.MALE),
            ("male", Gender.MALE),
            ("Male", Gender.MALE),
            ("MALE", Gender.MALE),
            ("m", Gender.MALE),
            ("M", Gender.MALE),
            ("女", Gender.FEMALE),
            ("female", Gender.FEMALE),
            ("Female", Gender.FEMALE),
            ("FEMALE", Gender.FEMALE),
            ("f", Gender.FEMALE),
            ("F", Gender.FEMALE),
        ],
    )
    def test_valid_gender(self, input_val, expected):
        assert self.type.convert(input_val, None, None) == expected

    def test_passthrough_gender_enum(self):
        assert self.type.convert(Gender.MALE, None, None) == Gender.MALE

    def test_invalid_gender(self):
        with pytest.raises(BadParameter):
            self.type.convert("invalid", None, None)
