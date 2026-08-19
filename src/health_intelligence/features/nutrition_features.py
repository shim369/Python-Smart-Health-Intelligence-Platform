"""栄養特徴量(PFCバランス)。"""

from __future__ import annotations

from dataclasses import dataclass

from health_intelligence.domain.models import MealLog

# 1gあたりのカロリー(一般的な換算値、いわゆる4-9-4)
_PROTEIN_KCAL_PER_G = 4.0
_FAT_KCAL_PER_G = 9.0
_CARBOHYDRATE_KCAL_PER_G = 4.0


@dataclass(frozen=True, kw_only=True, slots=True)
class NutritionFeatures:
    """PFCバランスとカロリー目標との差分。"""

    total_calories: float
    protein_ratio: float
    """タンパク質由来カロリーの割合(0.0〜1.0)。"""
    fat_ratio: float
    carbohydrate_ratio: float
    calories_diff_from_target: float | None
    """target_caloriesを指定した場合のみ計算する(実測 - 目標)。"""


def compute_nutrition_features(
    meal_logs: list[MealLog], *, target_calories: float | None = None
) -> NutritionFeatures:
    """指定した期間分のMealLogからPFCバランスを計算する。

    呼び出し側であらかじめ対象期間でフィルタ済みのmeal_logsを渡す想定。
    """
    total_calories = sum(m.calories for m in meal_logs)
    protein_kcal = sum(m.protein_g for m in meal_logs) * _PROTEIN_KCAL_PER_G
    fat_kcal = sum(m.fat_g for m in meal_logs) * _FAT_KCAL_PER_G
    carbohydrate_kcal = (
        sum(m.carbohydrate_g for m in meal_logs) * _CARBOHYDRATE_KCAL_PER_G
    )
    pfc_total_kcal = protein_kcal + fat_kcal + carbohydrate_kcal

    if pfc_total_kcal == 0:
        protein_ratio = fat_ratio = carbohydrate_ratio = 0.0
    else:
        protein_ratio = protein_kcal / pfc_total_kcal
        fat_ratio = fat_kcal / pfc_total_kcal
        carbohydrate_ratio = carbohydrate_kcal / pfc_total_kcal

    calories_diff_from_target = (
        total_calories - target_calories if target_calories is not None else None
    )

    return NutritionFeatures(
        total_calories=total_calories,
        protein_ratio=protein_ratio,
        fat_ratio=fat_ratio,
        carbohydrate_ratio=carbohydrate_ratio,
        calories_diff_from_target=calories_diff_from_target,
    )
