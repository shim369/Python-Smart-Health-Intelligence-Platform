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
    compute_daily_features,
    compute_nutrition_features,
    compute_sleep_features,
    compute_weight_features,
    compute_workout_features,
)
from health_intelligence.ml.dataset import DataQualityReport, check_data_quality
from health_intelligence.ml.weight_predictor import WeightPredictorService
from health_intelligence.recommendation import (
    Recommendation,
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

    Weight領域についてはML採用判断(ml/model_registry.py)を参照し、
    採用されていればAI予測をRecommendationへ追加する。未採用・判断
    未保存・データ不足・推論エラーの場合はRule-basedのみで動作する
    (architecture.md Section 11.5/11.6)。
    """

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        weight_predictor: WeightPredictorService | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._nutrition_analyzer = NutritionAnalyzer()
        self._weight_analyzer = WeightAnalyzer()
        self._sleep_analyzer = SleepAnalyzer()
        self._workout_analyzer = WorkoutAnalyzer()
        self._recommendation_engine = RuleBasedRecommendationEngine()
        self._weight_predictor = weight_predictor or WeightPredictorService()

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

        today_features = compute_daily_features(
            now.date(),
            meal_logs=meal_logs,
            sleep_logs=sleep_logs,
            workout_logs=workout_logs,
            weight_logs=weight_logs,
        )
        weight_prediction = self._weight_predictor.predict(today_features)
        if (
            weight_prediction.source == "ml"
            and weight_prediction.predicted_next_day_change_kg is not None
        ):
            # priority=100は既存のRule-based所見(最大でも100弱)より
            # 確実に高くなる値。Recommendation.priorityの定義(値が
            # 大きいほど優先度が高い)に沿って先頭に来るようにする。
            recommendations.append(
                Recommendation(
                    domain="weight",
                    message=(
                        "AI予測: 明日の体重は"
                        f"{weight_prediction.predicted_next_day_change_kg:+.2f}kg"
                        "程度の見込みです"
                    ),
                    priority=100,
                )
            )
            recommendations.sort(key=lambda r: r.priority, reverse=True)

        return RecommendationReport(health_score=health_score, recommendations=recommendations)

    def get_ml_progress(self, user_id: UUID) -> DataQualityReport:
        """体重予測MLパイプライン(ml/dataset.py)が要求するデータ量・
        欠損率の基準に対する、ユーザーの現在の進捗を返す。

        最初のログ記録日から今日までを対象期間とし、`check_data_quality`
        と同じ基準(MIN_DAYS=60日、欠損率30%未満)で判定する。ログが
        1件も無い場合は0日として扱う。
        """
        with self._uow_factory() as uow:
            meal_logs = uow.meal_logs.list_by_user(user_id)
            sleep_logs = uow.sleep_logs.list_by_user(user_id)
            workout_logs = uow.workout_logs.list_by_user(user_id)
            weight_logs = uow.weight_logs.list_by_user(user_id)

        candidate_dates = (
            [m.consumed_at.date() for m in meal_logs]
            + [s.wake_time.date() for s in sleep_logs]
            + [w.performed_at.date() for w in workout_logs]
            + [w.recorded_at.date() for w in weight_logs]
        )
        if not candidate_dates:
            return check_data_quality([])

        start_date = min(candidate_dates)
        end_date = datetime.now(UTC).date()
        num_days = (end_date - start_date).days + 1

        daily_features = [
            compute_daily_features(
                start_date + timedelta(days=offset),
                meal_logs=meal_logs,
                sleep_logs=sleep_logs,
                workout_logs=workout_logs,
                weight_logs=weight_logs,
            )
            for offset in range(num_days)
        ]
        return check_data_quality(daily_features)
