"""WorkoutAnalyzer。"""

from __future__ import annotations

from health_intelligence.analysis.types import AnalysisResult, clamp_score
from health_intelligence.features.workout_features import WorkoutFeatures

_RECOMMENDED_WEEKLY_SESSIONS = 3
_PENALTY_PER_MISSING_SESSION = 15.0


class WorkoutAnalyzer:
    """週あたりの運動セッション数から評価する。

    強度(ボリューム)は現時点ではスコアに反映せず、所見(findings)の
    参考情報にとどめる。強度の評価基準はPhase 5以降で見直す。
    """

    def analyze(self, features: WorkoutFeatures) -> AnalysisResult:
        if features.session_count == 0:
            return AnalysisResult(
                score=50.0,
                findings=["運動記録が不足しているため評価できません"],
            )

        missing_sessions = max(
            0,
            _RECOMMENDED_WEEKLY_SESSIONS - features.session_count,
        )

        score = clamp_score(100.0 - missing_sessions * _PENALTY_PER_MISSING_SESSION)

        if missing_sessions > 0:
            findings = [
                f"週あたりの運動回数が目安({_RECOMMENDED_WEEKLY_SESSIONS}回)"
                f"より{missing_sessions}回少ないです"
            ]
        else:
            findings = ["運動頻度は目安を満たしています"]

        if features.total_strength_volume_kg > 0:
            findings.append(
                f"筋力トレーニングの総ボリューム: {features.total_strength_volume_kg:.0f}kg"
            )

        return AnalysisResult(score=score, findings=findings)
