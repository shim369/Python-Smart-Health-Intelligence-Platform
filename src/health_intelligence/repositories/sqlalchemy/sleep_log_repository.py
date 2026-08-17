"""SqlAlchemyによる`SleepLogRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import SleepLogORM
from health_intelligence.domain.enums import SleepQuality
from health_intelligence.domain.models import SleepLog


def _to_domain(orm: SleepLogORM) -> SleepLog:
    return SleepLog(
        sleep_log_id=orm.id,
        user_id=orm.user_id,
        bedtime=orm.bedtime,
        wake_time=orm.wake_time,
        quality=SleepQuality(orm.quality) if orm.quality is not None else None,
    )


def _to_orm(sleep_log: SleepLog) -> SleepLogORM:
    return SleepLogORM(
        id=sleep_log.sleep_log_id,
        user_id=sleep_log.user_id,
        bedtime=sleep_log.bedtime,
        wake_time=sleep_log.wake_time,
        quality=sleep_log.quality.value if sleep_log.quality is not None else None,
    )


class SqlAlchemySleepLogRepository:
    """`repositories.protocols.SleepLogRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, sleep_log_id: UUID) -> SleepLog | None:
        stmt = select(SleepLogORM).where(
            SleepLogORM.id == sleep_log_id, SleepLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(self, user_id: UUID) -> list[SleepLog]:
        stmt = select(SleepLogORM).where(SleepLogORM.user_id == user_id)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, sleep_log: SleepLog) -> None:
        self._session.add(_to_orm(sleep_log))

    def delete(self, user_id: UUID, sleep_log_id: UUID) -> None:
        stmt = select(SleepLogORM).where(
            SleepLogORM.id == sleep_log_id, SleepLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
