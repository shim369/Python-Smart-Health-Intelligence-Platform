"""Recommendation Layer。

Rule-based Recommendation Engineを提供する。MLによる推薦
(採用/限定採用/見送りの判断を含む)はPhase 8/8Bで統合する
(architecture.md Section 11.5 ML Recommendation Strategy)。
"""

from health_intelligence.recommendation.rule_based import RuleBasedRecommendationEngine
from health_intelligence.recommendation.types import (
    Recommendation,
    RecommendationReport,
)

__all__ = ["Recommendation", "RecommendationReport", "RuleBasedRecommendationEngine"]
