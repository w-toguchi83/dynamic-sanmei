"""三柱（年柱・月柱・日柱）のドメインモデル."""

from pydantic import BaseModel

from sanmei_core.domain.kanshi import Kanshi


class ThreePillars(BaseModel, frozen=True):
    """三柱."""

    year: Kanshi
    month: Kanshi
    day: Kanshi
