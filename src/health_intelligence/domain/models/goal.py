"""Goal Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from health_intelligence.domain.enums import GoalCategory, GoalStatus


@dataclass(frozen=True, kw_only=True, slots=True)
class Goal:
    """長期目標を表すDomain Model(requirements.md 4.4節)。

    配下のTaskを「今日」ページのP(計画)で選択したり、D(実績)の
    DailyTaskLogを集計して進捗を可視化する起点になる。
    """

    goal_id: UUID
    user_id: UUID
    title: str
    category: GoalCategory
    deadline: date | None = None
    status: GoalStatus = GoalStatus.IN_PROGRESS
    created_at: datetime
