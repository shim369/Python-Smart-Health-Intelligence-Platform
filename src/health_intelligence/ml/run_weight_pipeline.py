"""Weight変化予測モデルのPipeline実行スクリプト。

実データがまだ不足している開発初期段階では、ダミーデータで配線を
確認する(requirements.md 9.3.1)。実データが60日分以上蓄積された後は、
`generate_dummy_daily_features`の代わりにRepository経由で実データの
`DailyFeatures`を組み立てて渡すよう差し替える。

実行方法: `uv run python -m health_intelligence.ml.run_weight_pipeline`
"""

from __future__ import annotations

from health_intelligence.logging_config import configure_logging
from health_intelligence.ml.dataset import (
    build_weight_change_dataset,
    check_data_quality,
)
from health_intelligence.ml.dummy_data import generate_dummy_daily_features
from health_intelligence.ml.evaluation import evaluate
from health_intelligence.ml.mlflow_tracking import log_weight_model_evaluation
from health_intelligence.ml.model_registry import MLAdoptionDecision, save_decision
from health_intelligence.ml.train import train_and_predict


def main() -> None:
    configure_logging()
    daily_features = generate_dummy_daily_features(num_days=90)

    quality = check_data_quality(daily_features)
    print(f"データ品質: {quality.reason}")
    if not quality.is_sufficient:
        print("→ 見送り(Rule-based Fallbackを継続)")
        return

    samples = build_weight_change_dataset(daily_features)
    print(f"サンプル数: {len(samples)}")

    result = evaluate(samples, train_and_predict)
    print(f"Baseline MAE: {result.mean_baseline_mae:.4f} kg")
    print(f"Model MAE:    {result.mean_model_val_mae:.4f} kg")
    print(f"改善率: {result.improvement_rate:.1%}")
    print(f"過学習乖離: {result.overfit_gap:.1%}")
    print(f"判定: {'ML採用' if result.ml_adopted else '見送り(Rule-based Fallback)'}")
    print(f"理由: {result.reason}")

    log_weight_model_evaluation(result)
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


if __name__ == "__main__":
    main()
