"""DailyJournalService。

「今日」ページのP(計画)/D(実績のうちTaskベースの部分)/DailyJournal
(P/C/A + 家計)をまとめて扱うService。requirements.md 4.4節・4.5節。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import date
from uuid import UUID, uuid4

from health_intelligence.domain.models import DailyJournal, DailyPlanItem, DailyTaskLog
from health_intelligence.repositories.unit_of_work import UnitOfWork


class DailyJournalService:
    """DailyJournal/DailyPlanItem/DailyTaskLogに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    # --- DailyJournal (P/C/A + 家計) ---

    def get_journal(self, user_id: UUID, journal_date: date) -> DailyJournal | None:
        with self._uow_factory() as uow:
            return uow.daily_journals.get_by_date(user_id, journal_date)

    def get_or_create_draft(self, user_id: UUID, journal_date: date) -> DailyJournal:
        """指定日のDailyJournalが無ければ、未保存のドラフトを返す。

        「今日」ページの各セクションはこのドラフト(または既存レコード)を
        `dataclasses.replace()`で部分更新してから`save_journal`に渡す想定。
        ドラフトの時点ではDBへ書き込まない。
        """
        existing = self.get_journal(user_id, journal_date)
        if existing is not None:
            return existing
        return DailyJournal(daily_journal_id=uuid4(), user_id=user_id, journal_date=journal_date)

    def save_journal(self, journal: DailyJournal) -> None:
        """指定日のDailyJournalをupsertする。"""
        with self._uow_factory() as uow:
            existing = uow.daily_journals.get_by_date(journal.user_id, journal.journal_date)
            if existing is None:
                uow.daily_journals.add(journal)
            else:
                uow.daily_journals.update(
                    replace(journal, daily_journal_id=existing.daily_journal_id)
                )
            uow.commit()

    # --- DailyPlanItem (P) ---

    def list_plan(self, user_id: UUID, journal_date: date) -> list[DailyPlanItem]:
        with self._uow_factory() as uow:
            return uow.daily_plan_items.list_by_date(user_id, journal_date)

    def save_plan(self, user_id: UUID, journal_date: date, task_ids: list[UUID]) -> None:
        """指定日のPをtask_idsの内容へまるごと置き換える。"""
        with self._uow_factory() as uow:
            uow.daily_plan_items.replace_for_date(user_id, journal_date, task_ids)
            uow.commit()

    # --- DailyTaskLog (D: 学習・PF開発・仕事の実績) ---

    def list_task_logs(self, user_id: UUID, journal_date: date) -> list[DailyTaskLog]:
        with self._uow_factory() as uow:
            return uow.daily_task_logs.list_by_date(user_id, journal_date)

    def save_task_log(self, daily_task_log: DailyTaskLog) -> None:
        """指定日・指定Taskの実績をupsertする。"""
        with self._uow_factory() as uow:
            existing = uow.daily_task_logs.get_by_task_and_date(
                daily_task_log.user_id, daily_task_log.task_id, daily_task_log.journal_date
            )
            if existing is None:
                uow.daily_task_logs.add(daily_task_log)
            else:
                uow.daily_task_logs.update(
                    replace(daily_task_log, daily_task_log_id=existing.daily_task_log_id)
                )
            uow.commit()
