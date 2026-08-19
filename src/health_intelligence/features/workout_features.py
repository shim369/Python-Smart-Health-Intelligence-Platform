"""運動特徴量。"""

from __future__ import annotations

from dataclasses import dataclass

from health_intelligence.domain.enums import ExerciseCategory
from health_intelligence.domain.models import WorkoutLog


@dataclass(frozen=True, kw_only=True, slots=True)
class WorkoutFeatures:
    session_count: int
    """期間内のWorkoutLog(セッション)数。"""
    total_cardio_minutes: int
    total_strength_volume_kg: float
    """筋力トレーニングの総ボリューム(reps × weight_kgの合計)。
    自重種目(weight_kg=None)のセットは対象外(0扱い)とする。"""


def compute_workout_features(workout_logs: list[WorkoutLog]) -> WorkoutFeatures:
    session_count = len(workout_logs)
    total_cardio_minutes = 0
    total_strength_volume_kg = 0.0

    for log in workout_logs:
        for exercise in log.exercises:
            if exercise.category == ExerciseCategory.CARDIO:
                total_cardio_minutes += exercise.duration_minutes or 0
            else:
                for workout_set in exercise.sets:
                    if workout_set.weight_kg is not None:
                        total_strength_volume_kg += (
                            workout_set.reps * workout_set.weight_kg
                        )

    return WorkoutFeatures(
        session_count=session_count,
        total_cardio_minutes=total_cardio_minutes,
        total_strength_volume_kg=total_strength_volume_kg,
    )
