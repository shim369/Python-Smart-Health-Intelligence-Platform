"""DailyTaskLog Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class DailyTaskLog:
    """「今日」ページD(実績)で記録した、log_type=COUNT_AND_DURATIONの
    Taskの実績を表すDomain Model(daily-journal-design.md 3.4節)。

    1ユーザー・1日・1Taskにつき1レコード。GoalService.compute_task_progress
    が同一Taskの複数日分を集計し、長期目標の進捗を算出する。
    """

    daily_task_log_id: UUID
    user_id: UUID
    journal_date: date
    task_id: UUID
    quantity: float | None = None
    duration_minutes: int | None = None
    """15分刻み(15/30/45/60/90/120以上)を想定。値そのものは分単位の整数。"""
    memo: str | None = None
