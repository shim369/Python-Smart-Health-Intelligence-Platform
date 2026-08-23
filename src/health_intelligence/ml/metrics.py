"""評価指標。

requirements.md 9.3.1: 回帰タスクの評価指標はMAE(平均絶対誤差)。
外れ値(記録ミス等)の影響を受けにくく、個人の健康データのような
荒いデータに向いているためRMSEではなくMAEを採用している
(architecture.md Section 11.5.1)。
"""

from __future__ import annotations


def mean_absolute_error(y_true: list[float], y_pred: list[float]) -> float:
    """MAE(平均絶対誤差)を計算する。"""
    if len(y_true) != len(y_pred):
        raise ValueError("y_trueとy_predの長さが一致しません")
    if not y_true:
        raise ValueError("空のデータでは計算できません")
    return sum(abs(t - p) for t, p in zip(y_true, y_pred, strict=True)) / len(y_true)
