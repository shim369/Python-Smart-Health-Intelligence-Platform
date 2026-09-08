"""MLflow実験管理。

architecture.md Section 11.4: Parameters/Metrics/Model/Experiment/
Evaluation Resultsを記録し、実験の再現性・モデル比較・Baseline比較・
採用判断に利用する。PROJECT_ROOT基準のpathlibでTracking URIを統一する
(要件定義の「PROJECT_ROOT基準のpathlibによるTracking管理」に対応)。
"""

from __future__ import annotations

import os
from pathlib import Path

import mlflow

from health_intelligence.ml.evaluation import (
    IMPROVEMENT_THRESHOLD,
    OVERFIT_GAP_THRESHOLD,
    MLEvaluationResult,
)

os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
"""ファイルベースのTracking Store(`mlruns/`)はMLflowでメンテナンス
モード扱いとなり、既定では例外を送出するようになった。PROJECT_ROOT
基準のファイルStoreを使う設計(このモジュールのdocstring参照)は
意図的なものであるため、明示的に許可する。"""

PROJECT_ROOT = Path(__file__).resolve().parents[3]
"""src/health_intelligence/ml/mlflow_tracking.py から4階層上。"""
TRACKING_URI = f"file:{PROJECT_ROOT / 'mlruns'}"


def log_weight_model_evaluation(
    result: MLEvaluationResult, *, run_name: str = "weight_change_model"
) -> None:
    """`MLEvaluationResult`をMLflowへ記録する。"""
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment("weight_change_prediction")

    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("improvement_threshold", IMPROVEMENT_THRESHOLD)
        mlflow.log_param("overfit_gap_threshold", OVERFIT_GAP_THRESHOLD)
        mlflow.log_param("n_folds", len(result.fold_results))

        mlflow.log_metric("mean_baseline_mae", result.mean_baseline_mae)
        mlflow.log_metric("mean_model_val_mae", result.mean_model_val_mae)
        mlflow.log_metric("mean_model_train_mae", result.mean_model_train_mae)
        mlflow.log_metric("improvement_rate", result.improvement_rate)
        mlflow.log_metric("overfit_gap", result.overfit_gap)
        mlflow.log_metric("ml_adopted", int(result.ml_adopted))

        for i, fold in enumerate(result.fold_results):
            mlflow.log_metric(f"fold{i + 1}_baseline_mae", fold.baseline_mae)
            mlflow.log_metric(f"fold{i + 1}_model_val_mae", fold.model_val_mae)

        mlflow.set_tag("reason", result.reason)
