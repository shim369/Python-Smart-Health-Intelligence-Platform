"""SqlAlchemyによる`HealthLogRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import HealthLogORM
from health_intelligence.domain.models import HealthLog


def _to_domain(orm: HealthLogORM) -> HealthLog:
    return HealthLog(
        health_log_id=orm.id,
        user_id=orm.user_id,
        recorded_at=orm.recorded_at,
        condition_score=orm.condition_score,
        symptoms=list(orm.symptoms),
        memo=orm.memo,
    )


def _to_orm(health_log: HealthLog) -> HealthLogORM:
    return HealthLogORM(
        id=health_log.health_log_id,
        user_id=health_log.user_id,
        recorded_at=health_log.recorded_at,
        condition_score=health_log.condition_score,
        symptoms=list(health_log.symptoms),
        memo=health_log.memo,
    )


class SqlAlchemyHealthLogRepository:
    """`repositories.protocols.HealthLogRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, health_log_id: UUID) -> HealthLog | None:
        stmt = select(HealthLogORM).where(
            HealthLogORM.id == health_log_id, HealthLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(self, user_id: UUID) -> list[HealthLog]:
        stmt = select(HealthLogORM).where(HealthLogORM.user_id == user_id)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, health_log: HealthLog) -> None:
        self._session.add(_to_orm(health_log))

    def delete(self, user_id: UUID, health_log_id: UUID) -> None:
        stmt = select(HealthLogORM).where(
            HealthLogORM.id == health_log_id, HealthLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
