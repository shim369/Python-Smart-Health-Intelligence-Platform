"""ML採用判断のための評価オーケストレーション。

requirements.md 9.3.1の数値基準(改善率10%以上、過学習チェック20%
以内)に基づき、MLをRule-based Baselineと比較して採用可否を判定する。

具体的な学習アルゴリズム(LightGBM等)には依存しない
(`train_predict_fn`として注入する)。これにより、この評価ロジック
自体は外部ライブラリ無しでテストできる(ml/train.pyのみがlightgbmに
依存する)。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from health_intelligence.ml.baseline import MeanBaseline
from health_intelligence.ml.cross_validation import forward_chaining_splits
from health_intelligence.ml.dataset import WeightChangeSample
from health_intelligence.ml.features import samples_to_matrix
from health_intelligence.ml.metrics import mean_absolute_error

IMPROVEMENT_THRESHOLD = 0.10
"""requirements.md 9.3.1: Baseline比で相対10%以上の改善で採用。"""
OVERFIT_GAP_THRESHOLD = 0.20
"""requirements.md 9.3.1: train/validation誤差の差が相対20%以内。"""

TrainPredictFn = Callable[[list[list[float]], list[float], list[list[float]]], list[float]]
"""(X_train, y_train, X_predict) -> y_predict という学習+推論関数。"""


@dataclass(frozen=True, kw_only=True, slots=True)
class FoldResult:
    baseline_mae: float
    model_train_mae: float
    model_val_mae: float


@dataclass(frozen=True, kw_only=True, slots=True)
class MLEvaluationResult:
    """ML採用判断に必要な情報一式。"""

    fold_results: list[FoldResult]
    mean_baseline_mae: float
    mean_model_val_mae: float
    mean_model_train_mae: float
    improvement_rate: float
    """Baseline比の相対改善率。正の値が大きいほどMLが優れている。"""
    overfit_gap: float
    """(val_mae - train_mae) / val_mae。正の値が大きいほど過学習気味。"""
    is_overfitting: bool
    ml_adopted: bool
    reason: str


def evaluate(
    samples: list[WeightChangeSample],
    train_predict_fn: TrainPredictFn,
    *,
    n_splits: int = 5,
) -> MLEvaluationResult:
    """forward-chaining CVでBaselineとMLモデルを比較し、採用可否を判定する。"""
    x, y = samples_to_matrix(samples)
    splits = forward_chaining_splits(len(samples), n_splits=n_splits)

    fold_results: list[FoldResult] = []
    for train_idx, val_idx in splits:
        x_train = [x[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        x_val = [x[i] for i in val_idx]
        y_val = [y[i] for i in val_idx]

        baseline = MeanBaseline.fit([samples[i] for i in train_idx])
        baseline_pred = baseline.predict([samples[i] for i in val_idx])
        baseline_mae = mean_absolute_error(y_val, baseline_pred)

        val_pred = train_predict_fn(x_train, y_train, x_val)
        train_pred = train_predict_fn(x_train, y_train, x_train)

        fold_results.append(
            FoldResult(
                baseline_mae=baseline_mae,
                model_train_mae=mean_absolute_error(y_train, train_pred),
                model_val_mae=mean_absolute_error(y_val, val_pred),
            )
        )

    mean_baseline_mae = sum(f.baseline_mae for f in fold_results) / len(fold_results)
    mean_model_val_mae = sum(f.model_val_mae for f in fold_results) / len(fold_results)
    mean_model_train_mae = sum(f.model_train_mae for f in fold_results) / len(fold_results)

    improvement_rate = (
        (mean_baseline_mae - mean_model_val_mae) / mean_baseline_mae
        if mean_baseline_mae > 0
        else 0.0
    )

    overfit_gap = (
        (mean_model_val_mae - mean_model_train_mae) / mean_model_val_mae
        if mean_model_val_mae > 0
        else 0.0
    )
    is_overfitting = overfit_gap > OVERFIT_GAP_THRESHOLD

    if is_overfitting:
        ml_adopted = False
        reason = (
            f"過学習チェックに抵触(乖離{overfit_gap:.0%} > {OVERFIT_GAP_THRESHOLD:.0%})のため見送り"
        )
    elif improvement_rate >= IMPROVEMENT_THRESHOLD:
        ml_adopted = True
        reason = f"Baseline比で{improvement_rate:.1%}改善、採用基準を満たす"
    else:
        ml_adopted = False
        reason = (
            f"Baseline比の改善率{improvement_rate:.1%}が基準"
            f"({IMPROVEMENT_THRESHOLD:.0%})未満のため見送り"
        )

    return MLEvaluationResult(
        fold_results=fold_results,
        mean_baseline_mae=mean_baseline_mae,
        mean_model_val_mae=mean_model_val_mae,
        mean_model_train_mae=mean_model_train_mae,
        improvement_rate=improvement_rate,
        overfit_gap=overfit_gap,
        is_overfitting=is_overfitting,
        ml_adopted=ml_adopted,
        reason=reason,
    )
