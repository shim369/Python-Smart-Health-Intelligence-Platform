"""SqlAlchemyによる`DailyJournalRepository`実装。"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import DailyJournalORM
from health_intelligence.domain.models import DailyJournal
from health_intelligence.repositories.errors import RecordNotFoundError


def _to_domain(orm: DailyJournalORM) -> DailyJournal:
    return DailyJournal(
        daily_journal_id=orm.id,
        user_id=orm.user_id,
        journal_date=orm.journal_date,
        diet_policy_note=orm.diet_policy_note,
        wake_target_time=orm.wake_target_time,
        sleep_target_time=orm.sleep_target_time,
        shopping_memo=orm.shopping_memo,
        food_expense_yen=orm.food_expense_yen,
        reflection_memo=orm.reflection_memo,
        improvement_point=orm.improvement_point,
        cooking_shopping_note=orm.cooking_shopping_note,
        study_prep_note=orm.study_prep_note,
    )


def _to_orm(daily_journal: DailyJournal) -> DailyJournalORM:
    return DailyJournalORM(
        id=daily_journal.daily_journal_id,
        user_id=daily_journal.user_id,
        journal_date=daily_journal.journal_date,
        diet_policy_note=daily_journal.diet_policy_note,
        wake_target_time=daily_journal.wake_target_time,
        sleep_target_time=daily_journal.sleep_target_time,
        shopping_memo=daily_journal.shopping_memo,
        food_expense_yen=daily_journal.food_expense_yen,
        reflection_memo=daily_journal.reflection_memo,
        improvement_point=daily_journal.improvement_point,
        cooking_shopping_note=daily_journal.cooking_shopping_note,
        study_prep_note=daily_journal.study_prep_note,
    )


class SqlAlchemyDailyJournalRepository:
    """`repositories.protocols.DailyJournalRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_date(self, user_id: UUID, journal_date: date) -> DailyJournal | None:
        stmt = select(DailyJournalORM).where(
            DailyJournalORM.user_id == user_id, DailyJournalORM.journal_date == journal_date
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def add(self, daily_journal: DailyJournal) -> None:
        self._session.add(_to_orm(daily_journal))

    def update(self, daily_journal: DailyJournal) -> None:
        stmt = select(DailyJournalORM).where(
            DailyJournalORM.id == daily_journal.daily_journal_id,
            DailyJournalORM.user_id == daily_journal.user_id,
        )
        orm = self._session.scalars(stmt).first()
        if orm is None:
            raise RecordNotFoundError(str(daily_journal.daily_journal_id))
        orm.journal_date = daily_journal.journal_date
        orm.diet_policy_note = daily_journal.diet_policy_note
        orm.wake_target_time = daily_journal.wake_target_time
        orm.sleep_target_time = daily_journal.sleep_target_time
        orm.shopping_memo = daily_journal.shopping_memo
        orm.food_expense_yen = daily_journal.food_expense_yen
        orm.reflection_memo = daily_journal.reflection_memo
        orm.improvement_point = daily_journal.improvement_point
        orm.cooking_shopping_note = daily_journal.cooking_shopping_note
        orm.study_prep_note = daily_journal.study_prep_note
