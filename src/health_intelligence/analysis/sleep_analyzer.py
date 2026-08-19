"""SleepAnalyzer。"""

from __future__ import annotations

from health_intelligence.analysis.types import AnalysisResult, clamp_score
from health_intelligence.features.sleep_features import SleepFeatures

_RECOMMENDED_MINUTES_RANGE = (360, 540)
"""推奨睡眠時間の目安レンジ(6〜9時間)。"""
_PENALTY_PER_MINUTE_OUTSIDE_RANGE = 0.3
_PENALTY_PER_INSUFFICIENT_DAY = 5.0


class SleepAnalyzer:
    """平均睡眠時間と睡眠不足日数から評価する。"""

    def analyze(self, features: SleepFeatures) -> AnalysisResult:
        if features.average_duration_minutes is None:
            return AnalysisResult(
                score=50.0,
                findings=["睡眠記録が不足しているため評価できません"],
            )

        low, high = _RECOMMENDED_MINUTES_RANGE
        avg = features.average_duration_minutes
        if avg < low:
            duration_penalty = (low - avg) * _PENALTY_PER_MINUTE_OUTSIDE_RANGE
        elif avg > high:
            duration_penalty = (avg - high) * _PENALTY_PER_MINUTE_OUTSIDE_RANGE
        else:
            duration_penalty = 0.0

        insufficient_penalty = (
            features.insufficient_sleep_days * _PENALTY_PER_INSUFFICIENT_DAY
        )
        score = clamp_score(100.0 - duration_penalty - insufficient_penalty)

        findings = []
        if duration_penalty > 0:
            findings.append(f"平均睡眠時間が目安から外れています({avg:.0f}分)")
        if features.insufficient_sleep_days > 0:
            findings.append(
                f"睡眠不足の日が{features.insufficient_sleep_days}日あります"
            )
        if not findings:
            findings.append("睡眠は良好な状態です")

        return AnalysisResult(score=score, findings=findings)
