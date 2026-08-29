"""ml/weight_predictor.pyのテスト。"""

from __future__ import annotations

from datetime import date

import pytest

from health_intelligence.features.daily_features import DailyFeatures
from health_intelligence.ml.model_registry import MLAdoptionDecision, save_decision
from health_intelligence.ml.weight_predictor import WeightPredictorService

_COMPLETE_DAY = DailyFeatures(
    target_date=date(2026, 1, 1),
    calories=2000,
    protein_g=90,
    fat_g=60,
    carbohydrate_g=250,
    sleep_duration_minutes=420,
    workout_duration_minutes=None,  # 運動していない日(データ欠損ではない)
    weight_kg=70.0,
)

_INCOMPLETE_DAY = DailyFeatures(
    target_date=date(2026, 1, 1),
    calories=None,
    protein_g=None,
    fat_g=None,
    carbohydrate_g=None,
    sleep_duration_minutes=None,
    workout_duration_minutes=None,
    weight_kg=None,
)


@pytest.fixture(autouse=True)
def _clean_artifact_dir(tmp_path, monkeypatch):
    """テスト間でml_artifacts/を汚染しないよう、一時ディレクトリに差し替える。"""
    import health_intelligence.ml.model_registry as model_registry

    monkeypatch.setattr(model_registry, "_ARTIFACT_DIR", tmp_path)


def test_no_decision_saved_falls_back() -> None:
    service = WeightPredictorService()

    result = service.predict(_COMPLETE_DAY)

    assert result.source == "rule_based_fallback"
    assert result.predicted_next_day_change_kg is None


def test_not_adopted_decision_falls_back() -> None:
    save_decision(
        MLAdoptionDecision(
            domain="weight", adopted=False, improvement_rate=0.02, reason="改善率不足"
        )
    )
    service = WeightPredictorService()

    result = service.predict(_COMPLETE_DAY)

    assert result.source == "rule_based_fallback"


def test_adopted_but_no_model_loaded_falls_back() -> None:
    save_decision(
        MLAdoptionDecision(domain="weight", adopted=True, improvement_rate=0.15, reason="採用")
    )
    service = WeightPredictorService()  # model_predict_fn未指定

    result = service.predict(_COMPLETE_DAY)

    assert result.source == "rule_based_fallback"


def test_missing_data_falls_back_even_with_model() -> None:
    save_decision(
        MLAdoptionDecision(domain="weight", adopted=True, improvement_rate=0.15, reason="採用")
    )
    service = WeightPredictorService(model_predict_fn=lambda x: [0.1])

    result = service.predict(_INCOMPLETE_DAY)

    assert result.source == "rule_based_fallback"
    assert "データ" in result.fallback_reason


def test_inference_error_falls_back() -> None:
    save_decision(
        MLAdoptionDecision(domain="weight", adopted=True, improvement_rate=0.15, reason="採用")
    )

    def broken_model(x: list[list[float]]) -> list[float]:
        raise RuntimeError("boom")

    service = WeightPredictorService(model_predict_fn=broken_model)

    result = service.predict(_COMPLETE_DAY)

    assert result.source == "rule_based_fallback"
    assert "推論エラー" in result.fallback_reason


def test_no_workout_that_day_does_not_trigger_fallback() -> None:
    """運動記録が無い日(workout_duration_minutes=None)は、データ欠損
    ではなく「運動していない日」として扱われ、Fallbackしないことを
    確認する(Day 8で見つけた不具合の回帰テスト)。"""
    save_decision(
        MLAdoptionDecision(domain="weight", adopted=True, improvement_rate=0.15, reason="採用")
    )
    service = WeightPredictorService(model_predict_fn=lambda x: [0.12])

    result = service.predict(_COMPLETE_DAY)

    assert result.source == "ml"
    assert result.predicted_next_day_change_kg == 0.12
