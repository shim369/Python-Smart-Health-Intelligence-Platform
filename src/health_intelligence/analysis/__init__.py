"""Analysis Layer。

Feature Engineering(features/)の出力を受け取り、0〜100のスコアと
所見を返す4つのAnalyzerと、それらを統合するHealth Scoreを提供する。
"""

from health_intelligence.analysis.health_score import HealthScore, compute_health_score
from health_intelligence.analysis.nutrition_analyzer import NutritionAnalyzer
from health_intelligence.analysis.sleep_analyzer import SleepAnalyzer
from health_intelligence.analysis.types import AnalysisResult
from health_intelligence.analysis.weight_analyzer import WeightAnalyzer
from health_intelligence.analysis.workout_analyzer import WorkoutAnalyzer

__all__ = [
    "AnalysisResult",
    "HealthScore",
    "NutritionAnalyzer",
    "SleepAnalyzer",
    "WeightAnalyzer",
    "WorkoutAnalyzer",
    "compute_health_score",
]
