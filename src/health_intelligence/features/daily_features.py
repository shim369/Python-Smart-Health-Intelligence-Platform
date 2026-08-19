"""日次特徴量。

architecture.md Section 12.1: 1日分の健康データを集計し、週次特徴量・
Analyzer・ML Dataset生成で再利用可能な単位にする。副作用を持たない
純粋関数として実装する。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from health_intelligence.domain.models import MealLog, SleepLog, WeightLog, WorkoutLog


@dataclass(frozen=True, kw_only=True, slots=True)
class DailyFeatures:
    """1日分の集計値。該当ログが無い項目はNoneとする。"""

    target_date: date
    calories: float | None
    protein_g: float | None
    fat_g: float | None
    carbohydrate_g: float | None
    sleep_duration_minutes: int | None
    workout_duration_minutes: int | None
    weight_kg: float | None


def compute_daily_features(
    target_date: date,
    *,
    meal_logs: list[MealLog],
    sleep_logs: list[SleepLog],
    workout_logs: list[WorkoutLog],
    weight_logs: list[WeightLog],
) -> DailyFeatures:
    """指定日のログ群からDailyFeaturesを計算する。

    各引数は呼び出し側であらかじめ対象日でフィルタ済みのものを渡しても、
    フィルタ前の全期間分を渡してもよい(この関数内で`target_date`との
    突合を行う)。

    workout_duration_minutesは有酸素運動(CARDIO)のduration_minutesの
    合計のみを対象とする。筋力トレーニング(STRENGTH)は所要時間を
    記録していないため計上されない(workout_features.pyの
    total_strength_volume_kgで別途評価する)。
    """
    day_meals = [m for m in meal_logs if m.consumed_at.date() == target_date]
    day_sleeps = [s for s in sleep_logs if s.wake_time.date() == target_date]
    day_workouts = [w for w in workout_logs if w.performed_at.date() == target_date]
    day_weights = [w for w in weight_logs if w.recorded_at.date() == target_date]

    calories = sum(m.calories for m in day_meals) if day_meals else None
    protein_g = sum(m.protein_g for m in day_meals) if day_meals else None
    fat_g = sum(m.fat_g for m in day_meals) if day_meals else None
    carbohydrate_g = sum(m.carbohydrate_g for m in day_meals) if day_meals else None

    sleep_duration_minutes = (
        sum(s.duration_minutes for s in day_sleeps) if day_sleeps else None
    )

    workout_duration_minutes = None
    if day_workouts:
        total = 0
        for workout in day_workouts:
            for exercise in workout.exercises:
                if exercise.duration_minutes is not None:
                    total += exercise.duration_minutes
        workout_duration_minutes = total

    weight_kg = day_weights[-1].weight_kg if day_weights else None

    return DailyFeatures(
        target_date=target_date,
        calories=calories,
        protein_g=protein_g,
        fat_g=fat_g,
        carbohydrate_g=carbohydrate_g,
        sleep_duration_minutes=sleep_duration_minutes,
        workout_duration_minutes=workout_duration_minutes,
        weight_kg=weight_kg,
    )
