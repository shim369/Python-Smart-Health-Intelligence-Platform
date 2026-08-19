"""NutritionAnalyzer。

一般的なPFCバランスの目安(厚生労働省「日本人の食事摂取基準」の
エネルギー産生栄養素バランスに近い値)を参考に、目安レンジから
どれだけ外れているかを評価する。医学的な個別最適化は行わない
(architecture.md Section 12.3 Health Scoreの位置づけ参照)。
"""

from __future__ import annotations

from health_intelligence.analysis.types import AnalysisResult, clamp_score
from health_intelligence.features.nutrition_features import NutritionFeatures

_PROTEIN_RATIO_RANGE = (0.13, 0.20)
_FAT_RATIO_RANGE = (0.20, 0.30)
_CARBOHYDRATE_RATIO_RANGE = (0.50, 0.65)
_PENALTY_PER_RATIO_POINT = 300.0


def _range_penalty(value: float, low: float, high: float) -> float:
    if value < low:
        return low - value
    if value > high:
        return value - high
    return 0.0


class NutritionAnalyzer:
    """PFCバランスの目安レンジからの乖離を評価する。"""

    def analyze(self, features: NutritionFeatures) -> AnalysisResult:
        if features.total_calories == 0:
            return AnalysisResult(
                score=50.0,
                findings=["食事記録が不足しているため評価できません"],
            )

        penalty = (
            _range_penalty(features.protein_ratio, *_PROTEIN_RATIO_RANGE)
            + _range_penalty(features.fat_ratio, *_FAT_RATIO_RANGE)
            + _range_penalty(features.carbohydrate_ratio, *_CARBOHYDRATE_RATIO_RANGE)
        )
        score = clamp_score(100.0 - penalty * _PENALTY_PER_RATIO_POINT)

        findings = []
        if features.protein_ratio < _PROTEIN_RATIO_RANGE[0]:
            findings.append("タンパク質の摂取割合が目安より低めです")
        if features.fat_ratio > _FAT_RATIO_RANGE[1]:
            findings.append("脂質の摂取割合が目安より高めです")
        if not findings:
            findings.append("PFCバランスは目安の範囲内です")

        return AnalysisResult(score=score, findings=findings)
