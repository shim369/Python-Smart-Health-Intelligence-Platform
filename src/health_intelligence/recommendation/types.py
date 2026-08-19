"""Recommendation関連の型。"""

from __future__ import annotations

from dataclasses import dataclass

from health_intelligence.analysis import HealthScore


@dataclass(frozen=True, kw_only=True, slots=True)
class Recommendation:
    """1件の改善提案。"""

    domain: str
    """"nutrition" / "weight" / "sleep" / "workout" のいずれか。"""
    message: str
    priority: int
    """値が大きいほど優先度が高い(対応するAnalyzerのスコアが低いほど
    大きくなる)。"""


@dataclass(frozen=True, kw_only=True, slots=True)
class RecommendationReport:
    """Health ScoreとRecommendation一覧をまとめたレポート。"""

    health_score: HealthScore
    recommendations: list[Recommendation]
