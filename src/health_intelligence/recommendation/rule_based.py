"""Rule-based Recommendation Engine。

architecture.md Section 11.1/11.2、requirements.md 9.1:
初期Recommendation EngineをRule-based方式で実装する。ML評価時の
Baseline、ML利用不能時のFallbackとしても利用する
(Phase 8/8Bで統合予定)。

各Analyzer(analysis/)が既にAnalysisResult.findingsとして所見を
出力しているため、ここではそれをRecommendationとしてパッケージし、
スコアに応じた優先度を付与する。
"""

from __future__ import annotations

from health_intelligence.analysis import HealthScore
from health_intelligence.recommendation.types import Recommendation


class RuleBasedRecommendationEngine:
    """HealthScoreからRecommendation一覧を生成する。"""

    def generate(self, health_score: HealthScore) -> list[Recommendation]:
        analysis_by_domain = {
            "nutrition": health_score.nutrition,
            "weight": health_score.weight,
            "sleep": health_score.sleep,
            "workout": health_score.workout,
        }

        recommendations = [
            Recommendation(
                domain=domain,
                message=finding,
                priority=round(100 - result.score),
            )
            for domain, result in analysis_by_domain.items()
            for finding in result.findings
        ]

        # 優先度(スコアが低い=改善余地が大きい)の高い順に並べる。
        # スコアが良好な領域の所見(例:"PFCバランスは目安の範囲内です")は
        # 優先度が低くなるため自然と末尾に来る。
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        return recommendations
