"""ML Pipeline Layer。

architecture.md Section 11.2/11.3: LightGBMベースのML Pipeline。
評価ロジック(evaluation.py)は学習アルゴリズムに依存しない設計とし、
LightGBM固有の処理はtrain.pyに閉じ込める。
"""

from health_intelligence.ml.baseline import MeanBaseline
from health_intelligence.ml.dataset import (
    DataQualityReport,
    WeightChangeSample,
    build_weight_change_dataset,
    check_data_quality,
)
from health_intelligence.ml.evaluation import (
    IMPROVEMENT_THRESHOLD,
    OVERFIT_GAP_THRESHOLD,
    FoldResult,
    MLEvaluationResult,
    evaluate,
)
from health_intelligence.ml.metrics import mean_absolute_error

__all__ = [
    "IMPROVEMENT_THRESHOLD",
    "OVERFIT_GAP_THRESHOLD",
    "DataQualityReport",
    "FoldResult",
    "MLEvaluationResult",
    "MeanBaseline",
    "WeightChangeSample",
    "build_weight_change_dataset",
    "check_data_quality",
    "evaluate",
    "mean_absolute_error",
]
