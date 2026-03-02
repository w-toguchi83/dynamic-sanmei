"""年月日干支のドメインモデル."""

from pydantic import BaseModel

from sanmei_core.domain.kanshi import Kanshi


class ThreePillars(BaseModel, frozen=True):
    """年・月・日の干支."""

    year: Kanshi
    month: Kanshi
    day: Kanshi
