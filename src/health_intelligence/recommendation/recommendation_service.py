"""RecommendationService。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from health_intelligence.analysis import (
    NutritionAnalyzer,
    SleepAnalyzer,
    WeightAnalyzer,
    WorkoutAnalyzer,
    compute_health_score,
)
from health_intelligence.features import (
    compute_nutrition_features,
    compute_sleep_features,
    compute_weight_features,
    compute_workout_features,
)
from health_intelligence.recommendation import (
    RecommendationReport,
    RuleBasedRecommendationEngine,
)
from health_intelligence.repositories.unit_of_work import UnitOfWork

_RECENT_WINDOW_DAYS = 7
"""食事・睡眠・運動の評価に使う直近日数(週間サイクルに合わせる)。"""
_WEIGHT_WINDOW_DAYS = 30
"""体重の変化傾向を見るための直近日数。日々のブレに引きずられない
よう、他の指標より長めの期間を取る。"""


class RecommendationService:
    """Recommendationに関するユースケースを担当するService。

    Feature Engineering(Phase 3)・Analysis(Phase 3)・Rule-based
    Recommendation Engine(Phase 5)を組み合わせ、ユーザーの直近ログ
    からRecommendationReportを生成する。

    MLによるRecommendation統合はPhase 8/8Bで追加する
    (architecture.md Section 11.5 ML Recommendation Strategy)。
    """

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory
        self._nutrition_analyzer = NutritionAnalyzer()
        self._weight_analyzer = WeightAnalyzer()
        self._sleep_analyzer = SleepAnalyzer()
        self._workout_analyzer = WorkoutAnalyzer()
        self._recommendation_engine = RuleBasedRecommendationEngine()

    def get_recommendations(self, user_id: UUID) -> RecommendationReport:
        now = datetime.now(UTC)
        recent_since = now - timedelta(days=_RECENT_WINDOW_DAYS)
        weight_since = now - timedelta(days=_WEIGHT_WINDOW_DAYS)

        with self._uow_factory() as uow:
            meal_logs = [
                m for m in uow.meal_logs.list_by_user(user_id) if m.consumed_at >= recent_since
            ]
            sleep_logs = [
                s for s in uow.sleep_logs.list_by_user(user_id) if s.wake_time >= recent_since
            ]
            workout_logs = [
                w for w in uow.workout_logs.list_by_user(user_id) if w.performed_at >= recent_since
            ]
            weight_logs = [
                w for w in uow.weight_logs.list_by_user(user_id) if w.recorded_at >= weight_since
            ]

        nutrition_features = compute_nutrition_features(meal_logs)
        weight_features = compute_weight_features(weight_logs)
        sleep_features = compute_sleep_features(sleep_logs)
        workout_features = compute_workout_features(workout_logs)

        health_score = compute_health_score(
            nutrition=self._nutrition_analyzer.analyze(nutrition_features),
            weight=self._weight_analyzer.analyze(weight_features),
            sleep=self._sleep_analyzer.analyze(sleep_features),
            workout=self._workout_analyzer.analyze(workout_features),
        )

        recommendations = self._recommendation_engine.generate(health_score)

        return RecommendationReport(health_score=health_score, recommendations=recommendations)
