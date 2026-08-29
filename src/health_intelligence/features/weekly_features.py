"""週間特徴量。

DailyFeaturesの並び(通常は直近7日分)を週間集計値へ変換する。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from health_intelligence.features.daily_features import DailyFeatures


@dataclass(frozen=True, kw_only=True, slots=True)
class WeeklyFeatures:
    """渡されたDailyFeaturesの範囲における週間集計値。"""

    average_calories: float | None
    average_protein_g: float | None
    average_fat_g: float | None
    average_carbohydrate_g: float | None
    average_sleep_duration_minutes: float | None
    workout_count: int
    """運動を記録した日数。"""
    total_workout_duration_minutes: int


def _average(values: Sequence[float]) -> float | None:
    """平均を計算する。

    `list[float]`ではなく`Sequence[float]`で受け取ることで、
    `list[int]`(睡眠時間等)もそのまま渡せるようにしている
    (listは非変、Sequenceは共変であるため。mypyのarg-type対応)。
    """
    return sum(values) / len(values) if values else None


def compute_weekly_features(daily_features: list[DailyFeatures]) -> WeeklyFeatures:
    """DailyFeaturesのリスト(通常は直近7日分)から週間特徴量を計算する。"""
    calories = [d.calories for d in daily_features if d.calories is not None]
    protein = [d.protein_g for d in daily_features if d.protein_g is not None]
    fat = [d.fat_g for d in daily_features if d.fat_g is not None]
    carbohydrate = [d.carbohydrate_g for d in daily_features if d.carbohydrate_g is not None]
    sleep = [
        d.sleep_duration_minutes for d in daily_features if d.sleep_duration_minutes is not None
    ]
    workout_days = [d for d in daily_features if d.workout_duration_minutes]

    return WeeklyFeatures(
        average_calories=_average(calories),
        average_protein_g=_average(protein),
        average_fat_g=_average(fat),
        average_carbohydrate_g=_average(carbohydrate),
        average_sleep_duration_minutes=_average(sleep),
        workout_count=len(workout_days),
        total_workout_duration_minutes=sum(d.workout_duration_minutes or 0 for d in daily_features),
    )
