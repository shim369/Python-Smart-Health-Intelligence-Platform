"""WeightChangeSampleを特徴量行列へ変換する。"""

from __future__ import annotations

from health_intelligence.ml.dataset import WeightChangeSample

FEATURE_NAMES = [
    "calories",
    "protein_g",
    "fat_g",
    "carbohydrate_g",
    "sleep_duration_minutes",
    "workout_duration_minutes",
    "weight_kg",
]


def samples_to_matrix(
    samples: list[WeightChangeSample],
) -> tuple[list[list[float]], list[float]]:
    """`FEATURE_NAMES`の順序に対応する特徴量行列Xと目的変数yを返す。"""
    x = [
        [
            s.calories,
            s.protein_g,
            s.fat_g,
            s.carbohydrate_g,
            s.sleep_duration_minutes,
            s.workout_duration_minutes,
            s.weight_kg,
        ]
        for s in samples
    ]
    y = [s.next_day_weight_change_kg for s in samples]
    return x, y
