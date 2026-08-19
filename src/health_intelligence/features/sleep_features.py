"""睡眠特徴量。"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from health_intelligence.domain.models import SleepLog

_SUFFICIENT_SLEEP_MINUTES = 360
"""6時間。睡眠不足と判定する閾値の暫定値(Phase 5以降で見直す)。"""


@dataclass(frozen=True, kw_only=True, slots=True)
class SleepFeatures:
    average_duration_minutes: float | None
    insufficient_sleep_days: int
    """`_SUFFICIENT_SLEEP_MINUTES`未満だった日数。"""
    duration_stddev_minutes: float | None
    """睡眠時間の標準偏差(分)。記録が1件のみの場合は0.0とする。"""


def compute_sleep_features(sleep_logs: list[SleepLog]) -> SleepFeatures:
    if not sleep_logs:
        return SleepFeatures(
            average_duration_minutes=None,
            insufficient_sleep_days=0,
            duration_stddev_minutes=None,
        )

    durations = [s.duration_minutes for s in sleep_logs]
    average_duration_minutes = sum(durations) / len(durations)
    insufficient_sleep_days = sum(
        1 for d in durations if d < _SUFFICIENT_SLEEP_MINUTES
    )
    duration_stddev_minutes = (
        statistics.stdev(durations) if len(durations) >= 2 else 0.0
    )

    return SleepFeatures(
        average_duration_minutes=average_duration_minutes,
        insufficient_sleep_days=insufficient_sleep_days,
        duration_stddev_minutes=duration_stddev_minutes,
    )
