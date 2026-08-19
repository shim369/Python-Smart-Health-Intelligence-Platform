"""Analysis結果を表す共通の型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, kw_only=True, slots=True)
class AnalysisResult:
    """1つのAnalyzerが出力する分析結果。

    scoreは0〜100のシステム独自スコアであり、医療的な指標ではない
    (architecture.md Section 12.3 Health Score Architecture参照)。
    """

    score: float
    """0(要改善)〜100(良好)。"""
    findings: list[str] = field(default_factory=list)
    """スコアの根拠となった所見。例: "睡眠不足の日が3日あります"。"""


def clamp_score(score: float) -> float:
    """スコアを0〜100の範囲に丸める共通ヘルパー。"""
    return max(0.0, min(100.0, score))
