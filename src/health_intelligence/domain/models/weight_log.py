"""WeightLog Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class WeightLog:
    """体重記録を表すDomain Model。"""

    weight_log_id: UUID
    user_id: UUID
    recorded_at: datetime
    weight_kg: float
