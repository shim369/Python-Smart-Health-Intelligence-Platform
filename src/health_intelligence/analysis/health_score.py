"""Health Score。

architecture.md Section 12.3: Nutrition/Weight/Sleep/Workoutの各Score
を統合し、システム独自のHealth Scoreを算出する。医療診断・疾病予測を
目的としない(requirements.md 8章)。
"""

from __future__ import annotations

from dataclasses import dataclass

from health_intelligence.analysis.types import AnalysisResult

_DEFAULT_WEIGHTS = {
    "nutrition": 0.25,
    "weight": 0.25,
    "sleep": 0.25,
    "workout": 0.25,
}


@dataclass(frozen=True, kw_only=True, slots=True)
class HealthScore:
    """4領域のAnalysisResultを統合した総合スコア。"""

    overall_score: float
    nutrition: AnalysisResult
    weight: AnalysisResult
    sleep: AnalysisResult
    workout: AnalysisResult


def compute_health_score(
    *,
    nutrition: AnalysisResult,
    weight: AnalysisResult,
    sleep: AnalysisResult,
    workout: AnalysisResult,
    weights: dict[str, float] | None = None,
) -> HealthScore:
    """4領域のスコアを加重平均してHealth Scoreを算出する。

    デフォルトは均等配分(各25%)。ユーザーの目標(減量重視/睡眠改善
    重視等)に応じて重みを変えたい場合は`weights`を指定する
    (Phase 5以降で検討する拡張ポイント)。
    """
    w = weights or _DEFAULT_WEIGHTS
    overall_score = (
        nutrition.score * w["nutrition"]
        + weight.score * w["weight"]
        + sleep.score * w["sleep"]
        + workout.score * w["workout"]
    )
    return HealthScore(
        overall_score=overall_score,
        nutrition=nutrition,
        weight=weight,
        sleep=sleep,
        workout=workout,
    )
