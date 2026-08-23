"""Weight領域のML/Rule-based Fallbackを管理するPredictor。

requirements.md 9.4 Fallback: 以下のいずれかに該当する場合、
Rule-based(この場合は「予測を行わない」)へFallbackする。

- ML採用判断がまだ保存されていない(Pipeline未実行)
- 保存された判断が「見送り」
- 学習済みモデルがロードされていない
- 当日の入力データが欠損している
- 推論時にエラーが発生した

architecture.md Section 11.6 ML Fallbackに対応する。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from health_intelligence.features.daily_features import DailyFeatures
from health_intelligence.ml.model_registry import load_decision

ModelPredictFn = Callable[[list[list[float]]], list[float]]
"""特徴量行列を受け取り予測値のリストを返す関数(学習済みモデルの推論)。"""


@dataclass(frozen=True, slots=True)
class WeightPrediction:
    """Weight領域の予測結果。"""

    predicted_next_day_change_kg: float | None
    source: str
    """`"ml"` または `"rule_based_fallback"`。"""
    fallback_reason: str | None = None


class WeightPredictorService:
    """ML採用判断を読み取り、必要に応じてRule-basedへFallbackする。"""

    def __init__(self, *, model_predict_fn: ModelPredictFn | None = None) -> None:
        """`model_predict_fn`が`None`の場合は常にFallbackする
        (学習済みモデルがまだロードされていない実行環境向け)。
        """
        self._model_predict_fn = model_predict_fn

    def predict(self, today: DailyFeatures) -> WeightPrediction:
        decision = load_decision("weight")

        if decision is None:
            return WeightPrediction(
                predicted_next_day_change_kg=None,
                source="rule_based_fallback",
                fallback_reason="ML採用判断が保存されていません(Pipeline未実行)",
            )

        if not decision.adopted:
            return WeightPrediction(
                predicted_next_day_change_kg=None,
                source="rule_based_fallback",
                fallback_reason=f"見送り判定のため: {decision.reason}",
            )

        if self._model_predict_fn is None:
            return WeightPrediction(
                predicted_next_day_change_kg=None,
                source="rule_based_fallback",
                fallback_reason="学習済みモデルがロードされていません",
            )

        if (
            today.calories is None
            or today.protein_g is None
            or today.fat_g is None
            or today.carbohydrate_g is None
            or today.sleep_duration_minutes is None
            or today.weight_kg is None
        ):
            return WeightPrediction(
                predicted_next_day_change_kg=None,
                source="rule_based_fallback",
                fallback_reason="当日の入力データが不足しています",
            )

        try:
            x = [
                [
                    today.calories,
                    today.protein_g,
                    today.fat_g,
                    today.carbohydrate_g,
                    float(today.sleep_duration_minutes),
                    # workout_duration_minutesがNoneなのは「運動していない日」を
                    # 意味し、データ欠損ではないため0として扱う。
                    float(today.workout_duration_minutes or 0),
                    today.weight_kg,
                ]
            ]
            prediction = self._model_predict_fn(x)[0]
        except Exception as e:  # noqa: BLE001 推論失敗時は必ずFallbackする
            return WeightPrediction(
                predicted_next_day_change_kg=None,
                source="rule_based_fallback",
                fallback_reason=f"推論エラーのため見送り: {e}",
            )

        return WeightPrediction(predicted_next_day_change_kg=prediction, source="ml")
