"""六十干支サイクルテーブル."""

from sanmei_core.domain.kanshi import Kanshi

SIXTY_KANSHI: tuple[Kanshi, ...] = tuple(Kanshi.from_index(i) for i in range(60))
