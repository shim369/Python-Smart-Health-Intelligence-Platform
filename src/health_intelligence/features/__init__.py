"""Feature Engineering Layer。

architecture.md Section 12.1: 健康データを分析・MLで利用可能な
特徴量へ変換する。副作用を持たない純粋関数として実装し、
Analyzer(analysis/)とML Dataset生成の両方から再利用する。
"""

from health_intelligence.features.daily_features import (
    DailyFeatures,
    compute_daily_features,
)
from health_intelligence.features.nutrition_features import (
    NutritionFeatures,
    compute_nutrition_features,
)
from health_intelligence.features.sleep_features import (
    SleepFeatures,
    compute_sleep_features,
)
from health_intelligence.features.weekly_features import (
    WeeklyFeatures,
    compute_weekly_features,
)
from health_intelligence.features.weight_features import (
    WeightFeatures,
    compute_weight_features,
)
from health_intelligence.features.workout_features import (
    WorkoutFeatures,
    compute_workout_features,
)

__all__ = [
    "DailyFeatures",
    "NutritionFeatures",
    "SleepFeatures",
    "WeeklyFeatures",
    "WeightFeatures",
    "WorkoutFeatures",
    "compute_daily_features",
    "compute_nutrition_features",
    "compute_sleep_features",
    "compute_weekly_features",
    "compute_weight_features",
    "compute_workout_features",
]
