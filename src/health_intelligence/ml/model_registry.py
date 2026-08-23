"""ML採用判断の永続化。

`ml/run_weight_pipeline.py`(Phase 8)で評価した結果を元に、対象領域で
MLを使うかどうかの判断をファイルへ保存する。Recommendation Engine
(Phase 8B)はここに保存された判断を読み取り、Rule-based/ML/Fallbackを
切り替える(architecture.md Section 11.6 ML Fallback)。

現状はJSONファイルへの単純な保存のみを行う。学習済みモデル自体
(LightGBM)の永続化・ロードの仕組みは、実データでの本評価が行われる
Phase 9以降で本格的に整備する想定(現時点ではPipelineの再実行を
前提とした簡易実装)。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

_ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "ml_artifacts"
"""src/health_intelligence/ml/model_registry.py から3階層上 = プロジェクトルート
直下の`ml_artifacts/`。"""


@dataclass(frozen=True, slots=True)
class MLAdoptionDecision:
    """1領域分のML採用判断のスナップショット。"""

    domain: str
    adopted: bool
    improvement_rate: float
    reason: str


def save_decision(decision: MLAdoptionDecision) -> None:
    """判断を`ml_artifacts/{domain}_model_decision.json`へ保存する。"""
    _ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = _ARTIFACT_DIR / f"{decision.domain}_model_decision.json"
    path.write_text(
        json.dumps(asdict(decision), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_decision(domain: str) -> MLAdoptionDecision | None:
    """保存された判断を読み取る。存在しない場合はNoneを返す。"""
    path = _ARTIFACT_DIR / f"{domain}_model_decision.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return MLAdoptionDecision(**data)
