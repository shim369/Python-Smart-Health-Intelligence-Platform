"""DailyJournal Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class DailyJournal:
    """「今日」ページのP/C/A項目と家計の入口を持つDomain Model
    (daily-journal-design.md 8章)。

    学習・PF開発・仕事はGoal/Task方式(Task/DailyPlanItem/DailyTaskLog)に
    切り出しているため、ここではそれ以外のP/C/A項目のみを持つ。
    1ユーザー・1日につき1レコード。
    """

    daily_journal_id: UUID
    user_id: UUID
    journal_date: date
    diet_policy_note: str | None = None
    """[P] 食事方針の補足メモ。"""
    wake_target_time: time | None = None
    """[P] 起床目標時刻。"""
    sleep_target_time: time | None = None
    """[P] 就寝目標時刻。"""
    shopping_memo: str | None = None
    """[D] 買い物メモ。レシピの材料をワンタップで追記できる(design.md 6章)。"""
    food_expense_yen: int | None = None
    """[D] その日の食費合計(円)。"""
    work_hours: float | None = None
    """[D] その日の総勤務時間(時間)。Task単位の時間集計とは別の数値。"""
    reflection_memo: str | None = None
    """[C] 振り返り。"""
    improvement_point: str | None = None
    """[A] 明日変えること(1つ)。"""
    cooking_shopping_note: str | None = None
    """[A] 料理・買い物メモ。"""
    study_prep_note: str | None = None
    """[A] 学習準備メモ。"""
