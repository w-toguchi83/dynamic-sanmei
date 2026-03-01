from sanmei_core.domain.kanshi import Kanshi, TenStem, TwelveBranch


class TestTenStem:
    def test_count(self) -> None:
        assert len(TenStem) == 10

    def test_values_are_sequential(self) -> None:
        for i, stem in enumerate(TenStem):
            assert stem.value == i

    def test_kinoe_is_zero(self) -> None:
        assert TenStem.KINOE.value == 0

    def test_mizunoto_is_nine(self) -> None:
        assert TenStem.MIZUNOTO.value == 9


class TestTwelveBranch:
    def test_count(self) -> None:
        assert len(TwelveBranch) == 12

    def test_values_are_sequential(self) -> None:
        for i, branch in enumerate(TwelveBranch):
            assert branch.value == i

    def test_ne_is_zero(self) -> None:
        assert TwelveBranch.NE.value == 0

    def test_i_is_eleven(self) -> None:
        assert TwelveBranch.I.value == 11


class TestKanshi:
    def test_from_index_kinoe_ne(self) -> None:
        """甲子 = index 0"""
        k = Kanshi.from_index(0)
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.NE
        assert k.index == 0

    def test_from_index_kinoe_inu(self) -> None:
        """甲戌 = index 10"""
        k = Kanshi.from_index(10)
        assert k.stem == TenStem.KINOE
        assert k.branch == TwelveBranch.INU
        assert k.index == 10

    def test_from_index_mizunoto_i(self) -> None:
        """癸亥 = index 59 (最後)"""
        k = Kanshi.from_index(59)
        assert k.stem == TenStem.MIZUNOTO
        assert k.branch == TwelveBranch.I
        assert k.index == 59

    def test_from_index_wraps_at_60(self) -> None:
        assert Kanshi.from_index(60) == Kanshi.from_index(0)

    def test_sixty_cycle_has_no_duplicates(self) -> None:
        all_kanshi = [Kanshi.from_index(i) for i in range(60)]
        pairs = [(k.stem, k.branch) for k in all_kanshi]
        assert len(set(pairs)) == 60

    def test_kanji_name(self) -> None:
        k = Kanshi.from_index(0)
        assert k.kanji == "甲子"
