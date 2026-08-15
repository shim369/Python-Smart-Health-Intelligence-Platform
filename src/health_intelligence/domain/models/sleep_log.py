"""SleepLog Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from health_intelligence.domain.enums import SleepQuality


@dataclass(frozen=True, kw_only=True, slots=True)
class SleepLog:
    """睡眠記録を表すDomain Model。

    睡眠時間は保存せず、就寝・起床時刻から都度算出する
    (保存された時間と算出結果がずれるリスクを避けるため)。
    """

    sleep_log_id: UUID
    user_id: UUID
    bedtime: datetime
    wake_time: datetime
    quality: SleepQuality | None = None

    @property
    def duration_minutes(self) -> int:
        """就寝〜起床時刻から睡眠時間(分)を算出する。"""
        delta = self.wake_time - self.bedtime
        return int(delta.total_seconds() // 60)
