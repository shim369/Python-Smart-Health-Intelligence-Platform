"""Task Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from health_intelligence.domain.enums import GoalCategory, TaskLogType


@dataclass(frozen=True, kw_only=True, slots=True)
class Task:
    """Goal配下、または単発の関連タスクを表すDomain Model
    (daily-journal-design.md 3章)。

    `goal_id`はNullable(空 = 長期目標に属さない単発タスク。
    「今日」ページでの経路Bの即席追加を想定。design.md 3.5節参照)。

    `log_type`によって「今日」ページD(実績)での記録方法が変わる。
    COUNT_AND_DURATIONは`DailyTaskLog`に数量・時間・メモを記録し、
    PLAN_ONLYは選ぶだけで実績は既存のMealLog/WorkoutLog/SleepLogが担う。
    """

    task_id: UUID
    user_id: UUID
    goal_id: UUID | None = None
    category: GoalCategory
    title: str
    log_type: TaskLogType
    unit: str | None = None
    """数量の単位(例: "問")。log_type=COUNT_AND_DURATIONのみ使用。"""
    is_archived: bool = False
    created_at: datetime
