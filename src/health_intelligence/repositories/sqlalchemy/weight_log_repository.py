"""SqlAlchemyによる`WeightLogRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import WeightLogORM
from health_intelligence.domain.models import WeightLog


def _to_domain(orm: WeightLogORM) -> WeightLog:
    return WeightLog(
        weight_log_id=orm.id,
        user_id=orm.user_id,
        recorded_at=orm.recorded_at,
        weight_kg=orm.weight_kg,
    )


def _to_orm(weight_log: WeightLog) -> WeightLogORM:
    return WeightLogORM(
        id=weight_log.weight_log_id,
        user_id=weight_log.user_id,
        recorded_at=weight_log.recorded_at,
        weight_kg=weight_log.weight_kg,
    )


class SqlAlchemyWeightLogRepository:
    """`repositories.protocols.WeightLogRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, weight_log_id: UUID) -> WeightLog | None:
        stmt = select(WeightLogORM).where(
            WeightLogORM.id == weight_log_id, WeightLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(self, user_id: UUID) -> list[WeightLog]:
        stmt = select(WeightLogORM).where(WeightLogORM.user_id == user_id)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, weight_log: WeightLog) -> None:
        self._session.add(_to_orm(weight_log))

    def delete(self, user_id: UUID, weight_log_id: UUID) -> None:
        stmt = select(WeightLogORM).where(
            WeightLogORM.id == weight_log_id, WeightLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
