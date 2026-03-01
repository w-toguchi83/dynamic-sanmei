"""SchoolRegistry のテスト."""

from __future__ import annotations

import pytest
from sanmei_core.domain.errors import SanmeiError
from sanmei_core.schools.registry import SchoolRegistry
from sanmei_core.schools.standard import StandardSchool


class TestSchoolRegistry:
    def test_register_and_get(self) -> None:
        registry = SchoolRegistry()
        school = StandardSchool()
        registry.register(school)
        assert registry.get("standard") is school

    def test_get_unknown_raises(self) -> None:
        registry = SchoolRegistry()
        with pytest.raises(SanmeiError, match="unknown"):
            registry.get("unknown")

    def test_default_returns_first_registered(self) -> None:
        registry = SchoolRegistry()
        school = StandardSchool()
        registry.register(school)
        assert registry.default() is school

    def test_default_empty_raises(self) -> None:
        registry = SchoolRegistry()
        with pytest.raises(SanmeiError, match="No schools"):
            registry.default()

    def test_list_schools(self) -> None:
        registry = SchoolRegistry()
        registry.register(StandardSchool())
        assert registry.list_schools() == ["standard"]

    def test_create_default_has_standard(self) -> None:
        registry = SchoolRegistry.create_default()
        assert registry.default().name == "standard"
