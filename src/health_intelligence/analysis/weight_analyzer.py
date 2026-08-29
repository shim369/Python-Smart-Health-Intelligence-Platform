"""WeightAnalyzer。

architecture.md Section 12.2: 体重の変化率を評価する。

目標体重(増量/減量/維持のいずれを目指すか)という概念はまだ
requirements.mdに存在しない。そのため現時点では「変化が急激すぎ
ないか」のみを評価する暫定ロジックとする。目標設定機能が追加され
次第(Phase 5以降)、目標との差分ベースの評価に切り替える想定。
"""

from __future__ import annotations

from health_intelligence.analysis.types import AnalysisResult, clamp_score
from health_intelligence.features.weight_features import WeightFeatures

_STABLE_WEEKLY_CHANGE_RATE = 0.01
"""週あたり1%以内の変化を「安定」とみなす閾値(暫定値)。"""
_PENALTY_PER_EXCESS_RATE = 1000.0
"""閾値超過分に対するスコア減点の係数。"""


class WeightAnalyzer:
    """体重の変化率から安定性を評価する。"""

    def analyze(self, features: WeightFeatures) -> AnalysisResult:
        if features.change_rate is None:
            return AnalysisResult(
                score=50.0,
                findings=["体重記録が不足しているため評価できません"],
            )

        excess = max(0.0, abs(features.change_rate) - _STABLE_WEEKLY_CHANGE_RATE)
        score = clamp_score(100.0 - excess * _PENALTY_PER_EXCESS_RATE)

        if excess > 0:
            direction = "増加" if features.change_rate > 0 else "減少"
            findings = [f"体重が急激に{direction}しています(変化率 {features.change_rate:+.1%})"]
        else:
            findings = ["体重は安定して推移しています"]

        return AnalysisResult(score=score, findings=findings)
