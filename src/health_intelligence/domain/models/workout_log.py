"""WorkoutLog Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from health_intelligence.domain.enums import WorkoutIntensity, WorkoutType


@dataclass(frozen=True, kw_only=True, slots=True)
class WorkoutLog:
    """運動記録を表すDomain Model。"""

    workout_log_id: UUID
    user_id: UUID
    performed_at: datetime
    workout_type: WorkoutType
    duration_minutes: int
    intensity: WorkoutIntensity
    calories_burned: float | None = None
