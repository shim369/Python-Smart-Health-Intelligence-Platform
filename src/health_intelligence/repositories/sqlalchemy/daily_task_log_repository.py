"""SqlAlchemyによる`DailyTaskLogRepository`実装。"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import DailyTaskLogORM
from health_intelligence.domain.models import DailyTaskLog
from health_intelligence.repositories.errors import RecordNotFoundError


def _to_domain(orm: DailyTaskLogORM) -> DailyTaskLog:
    return DailyTaskLog(
        daily_task_log_id=orm.id,
        user_id=orm.user_id,
        journal_date=orm.journal_date,
        task_id=orm.task_id,
        quantity=orm.quantity,
        duration_minutes=orm.duration_minutes,
        memo=orm.memo,
    )


def _to_orm(daily_task_log: DailyTaskLog) -> DailyTaskLogORM:
    return DailyTaskLogORM(
        id=daily_task_log.daily_task_log_id,
        user_id=daily_task_log.user_id,
        journal_date=daily_task_log.journal_date,
        task_id=daily_task_log.task_id,
        quantity=daily_task_log.quantity,
        duration_minutes=daily_task_log.duration_minutes,
        memo=daily_task_log.memo,
    )


class SqlAlchemyDailyTaskLogRepository:
    """`repositories.protocols.DailyTaskLogRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_task_and_date(
        self, user_id: UUID, task_id: UUID, journal_date: date
    ) -> DailyTaskLog | None:
        stmt = select(DailyTaskLogORM).where(
            DailyTaskLogORM.user_id == user_id,
            DailyTaskLogORM.task_id == task_id,
            DailyTaskLogORM.journal_date == journal_date,
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_date(self, user_id: UUID, journal_date: date) -> list[DailyTaskLog]:
        stmt = select(DailyTaskLogORM).where(
            DailyTaskLogORM.user_id == user_id, DailyTaskLogORM.journal_date == journal_date
        )
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def list_by_date_range(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[DailyTaskLog]:
        stmt = select(DailyTaskLogORM).where(
            DailyTaskLogORM.user_id == user_id,
            DailyTaskLogORM.journal_date.between(start_date, end_date),
        )
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def list_by_task(self, user_id: UUID, task_id: UUID) -> list[DailyTaskLog]:
        stmt = select(DailyTaskLogORM).where(
            DailyTaskLogORM.user_id == user_id, DailyTaskLogORM.task_id == task_id
        )
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, daily_task_log: DailyTaskLog) -> None:
        self._session.add(_to_orm(daily_task_log))

    def update(self, daily_task_log: DailyTaskLog) -> None:
        stmt = select(DailyTaskLogORM).where(
            DailyTaskLogORM.id == daily_task_log.daily_task_log_id,
            DailyTaskLogORM.user_id == daily_task_log.user_id,
        )
        orm = self._session.scalars(stmt).first()
        if orm is None:
            raise RecordNotFoundError(str(daily_task_log.daily_task_log_id))
        orm.journal_date = daily_task_log.journal_date
        orm.task_id = daily_task_log.task_id
        orm.quantity = daily_task_log.quantity
        orm.duration_minutes = daily_task_log.duration_minutes
        orm.memo = daily_task_log.memo

    def delete(self, user_id: UUID, daily_task_log_id: UUID) -> None:
        stmt = select(DailyTaskLogORM).where(
            DailyTaskLogORM.id == daily_task_log_id, DailyTaskLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
