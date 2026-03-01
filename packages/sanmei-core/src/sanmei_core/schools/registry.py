"""SchoolRegistry — 流派レジストリ."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sanmei_core.domain.errors import SanmeiError

if TYPE_CHECKING:
    from sanmei_core.protocols.school import SchoolProtocol


class SchoolRegistry:
    """流派の登録・取得を行うレジストリ."""

    def __init__(self) -> None:
        self._schools: dict[str, SchoolProtocol] = {}
        self._default_name: str | None = None

    def register(self, school: SchoolProtocol) -> None:
        """流派を登録."""
        self._schools[school.name] = school
        if self._default_name is None:
            self._default_name = school.name

    def get(self, name: str) -> SchoolProtocol:
        """名前で流派を取得."""
        if name not in self._schools:
            msg = f"School '{name}' is unknown. Available: {list(self._schools)}"
            raise SanmeiError(msg)
        return self._schools[name]

    def default(self) -> SchoolProtocol:
        """デフォルト流派を取得."""
        if self._default_name is None:
            msg = "No schools registered"
            raise SanmeiError(msg)
        return self._schools[self._default_name]

    def list_schools(self) -> list[str]:
        """登録済み流派名のリスト."""
        return list(self._schools)

    @classmethod
    def create_default(cls) -> SchoolRegistry:
        """標準流派を登録済みのレジストリを生成."""
        from sanmei_core.schools.standard import StandardSchool

        registry = cls()
        registry.register(StandardSchool())
        return registry
