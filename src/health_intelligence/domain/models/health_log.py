"""HealthLog Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class HealthLog:
    """ユーザーの健康状態に関する基本的な記録を表すDomain Model。

    MealLog / WorkoutLog / SleepLog / WeightLogでカバーしない、
    体調・症状・気分など汎用的な健康記録の受け皿として扱う。

    フィールド構成は初期案(requirements.md 4.2で未確定とした項目の
    暫定案)であり、実装しながら見直す前提とする。
    """

    health_log_id: UUID
    user_id: UUID
    recorded_at: datetime
    condition_score: int | None = None
    """自己申告の体調スコア。1(不調)〜5(良好)を想定。"""
    symptoms: list[str] = field(default_factory=list)
    """自由記述の症状タグ(例: "頭痛", "倦怠感")。"""
    memo: str | None = None
