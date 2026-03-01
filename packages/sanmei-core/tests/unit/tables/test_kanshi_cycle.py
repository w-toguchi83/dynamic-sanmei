from sanmei_core.domain.kanshi import TenStem, TwelveBranch
from sanmei_core.tables.kanshi_cycle import SIXTY_KANSHI


def test_sixty_kanshi_length() -> None:
    assert len(SIXTY_KANSHI) == 60


def test_first_is_kinoe_ne() -> None:
    """甲子."""
    assert SIXTY_KANSHI[0].stem == TenStem.KINOE
    assert SIXTY_KANSHI[0].branch == TwelveBranch.NE


def test_last_is_mizunoto_i() -> None:
    """癸亥."""
    assert SIXTY_KANSHI[59].stem == TenStem.MIZUNOTO
    assert SIXTY_KANSHI[59].branch == TwelveBranch.I


def test_all_unique() -> None:
    pairs = [(k.stem, k.branch) for k in SIXTY_KANSHI]
    assert len(set(pairs)) == 60


def test_index_matches_position() -> None:
    for i, k in enumerate(SIXTY_KANSHI):
        assert k.index == i
