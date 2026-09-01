"""DailyPlanItem Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class DailyPlanItem:
    """「今日」ページP(計画)で選択したTaskを表すDomain Model
    (requirements.md 4.4節)。

    1ユーザー・1日・1Taskにつき1レコード。1日分のPは
    `DailyPlanItemRepository.replace_for_date`でまとめて置き換える。
    """

    daily_plan_item_id: UUID
    user_id: UUID
    journal_date: date
    task_id: UUID
