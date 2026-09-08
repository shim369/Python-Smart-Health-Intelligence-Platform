"""Weight変化予測モデルのPipeline実行スクリプト。

まず実データの蓄積状況(requirements.md 9.3.1: 60日分以上・欠損率30%
未満)を確認する。基準を満たしていれば実データでPipelineを評価し、
その結果を`ml_artifacts/weight_model_decision.json`へ「ML採用判断」
として保存する(Recommendation Engineが参照する、製品判断に使える
唯一のソース)。

基準を満たしていない間は、ダミーデータでPipelineの配線確認のみを
行う。ダミーデータによる評価結果は採用判断として保存しない
(実データに基づかない判断がRecommendation Engineへ誤って
反映されるのを防ぐため)。あわせて60日到達の見込み日を算出して
表示する。

実行方法: `uv run python -m health_intelligence.ml.run_weight_pipeline`
"""

from __future__ import annotations

from health_intelligence.config import load_environment
from health_intelligence.database.connection import session_scope
from health_intelligence.features.daily_features import DailyFeatures
from health_intelligence.logging_config import configure_logging
from health_intelligence.ml.dataset import (
    build_weight_change_dataset,
    check_data_quality,
)
from health_intelligence.ml.dummy_data import generate_dummy_daily_features
from health_intelligence.ml.evaluation import MLEvaluationResult, evaluate
from health_intelligence.ml.mlflow_tracking import log_weight_model_evaluation
from health_intelligence.ml.model_registry import MLAdoptionDecision, save_decision
from health_intelligence.ml.real_data import estimate_readiness_date, load_real_daily_features
from health_intelligence.ml.train import train_and_predict


def _evaluate_pipeline(daily_features: list[DailyFeatures]) -> MLEvaluationResult | None:
    """データ品質を確認した上でPipelineを評価する。基準未満ならNoneを返す。"""
    quality = check_data_quality(daily_features)
    print(f"データ品質: {quality.reason}")
    if not quality.is_sufficient:
        print("→ 見送り(Rule-based Fallbackを継続)")
        return None

    samples = build_weight_change_dataset(daily_features)
    print(f"サンプル数: {len(samples)}")

    result = evaluate(samples, train_and_predict)
    print(f"Baseline MAE: {result.mean_baseline_mae:.4f} kg")
    print(f"Model MAE:    {result.mean_model_val_mae:.4f} kg")
    print(f"改善率: {result.improvement_rate:.1%}")
    print(f"過学習乖離: {result.overfit_gap:.1%}")
    print(f"判定: {'ML採用' if result.ml_adopted else '見送り(Rule-based Fallback)'}")
    print(f"理由: {result.reason}")
    return result


def main() -> None:
    load_environment()
    configure_logging()

    print("=== 実データ蓄積状況(Weight領域) ===")
    with session_scope() as session:
        real_daily_features = load_real_daily_features(session)

    real_quality = check_data_quality(real_daily_features)
    print(f"蓄積日数: {real_quality.total_days}日 / 欠損率: {real_quality.missing_rate:.1%}")
    print(f"理由: {real_quality.reason}")

    if real_quality.is_sufficient:
        print("→ 実データでML採用判断を実行します(初回判定)。")
        result = _evaluate_pipeline(real_daily_features)
        if result is None:
            return

        log_weight_model_evaluation(result, run_name="weight_change_model")
        print("MLflowへ記録しました。")

        save_decision(
            MLAdoptionDecision(
                domain="weight",
                adopted=result.ml_adopted,
                improvement_rate=result.improvement_rate,
                reason=result.reason,
            )
        )
        print("ML採用判断をml_artifacts/へ保存しました。")
        return

    readiness_date = estimate_readiness_date(real_daily_features)
    if readiness_date is not None:
        print(f"60日到達の見込み日: {readiness_date}")
    else:
        print(
            "ログが1件も存在しないため見込み日を算出できません。記録開始後に再度判定してください。"
        )
    print("→ 実データでの学習は見送り。ダミーデータでPipeline配線確認のみ継続します。")

    print("\n=== ダミーデータによる配線確認 ===")
    dummy_daily_features = generate_dummy_daily_features(num_days=90)
    result = _evaluate_pipeline(dummy_daily_features)
    if result is None:
        return

    # ダミーデータでの評価結果は実データに基づく判断ではないため、
    # Recommendation Engineが参照するML採用判断(save_decision)へは
    # 保存しない。Pipeline自体が最後まで動作することの確認に留める。
    log_weight_model_evaluation(result, run_name="weight_change_model_dummy_wiring_check")
    print("MLflowへ記録しました(配線確認用、採用判断へは反映しません)。")


if __name__ == "__main__":
    main()
