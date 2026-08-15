"""Domain Modelで利用するEnum定義。

外部入力(Pydantic Schema等)との境界でも同じEnumを再利用してよいが、
Enumの値そのものはDatabase固有の表現に依存させない。
"""

from __future__ import annotations

from enum import StrEnum


class MealType(StrEnum):
    """MealLogの食事区分。"""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class WorkoutType(StrEnum):
    """WorkoutLogの運動種別。"""

    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    SPORTS = "sports"
    OTHER = "other"


class WorkoutIntensity(StrEnum):
    """WorkoutLogの運動強度。"""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SleepQuality(StrEnum):
    """SleepLogの主観的な睡眠品質。"""

    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class RecipeSource(StrEnum):
    """Recipeの生成元。"""

    MANUAL = "manual"
    AI_GENERATED = "ai_generated"
