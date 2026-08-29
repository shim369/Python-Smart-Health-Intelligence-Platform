"""SqlAlchemyによる`LearningLogRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import LearningLogORM
from health_intelligence.domain.enums import LearningCategory, LearningLocation
from health_intelligence.domain.models import LearningLog
from health_intelligence.repositories.errors import RecordNotFoundError


def _to_domain(orm: LearningLogORM) -> LearningLog:
    return LearningLog(
        learning_log_id=orm.id,
        user_id=orm.user_id,
        started_at=orm.started_at,
        category=LearningCategory(orm.category),
        location=LearningLocation(orm.location) if orm.location is not None else None,
        content=orm.content,
        breakdown=list(orm.breakdown),
        duration_minutes=orm.duration_minutes,
        keywords=list(orm.keywords),
        notes=list(orm.notes),
    )


def _to_orm(learning_log: LearningLog) -> LearningLogORM:
    return LearningLogORM(
        id=learning_log.learning_log_id,
        user_id=learning_log.user_id,
        started_at=learning_log.started_at,
        category=learning_log.category.value,
        location=(
            learning_log.location.value if learning_log.location is not None else None
        ),
        content=learning_log.content,
        breakdown=list(learning_log.breakdown),
        duration_minutes=learning_log.duration_minutes,
        keywords=list(learning_log.keywords),
        notes=list(learning_log.notes),
    )


class SqlAlchemyLearningLogRepository:
    """`repositories.protocols.LearningLogRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, learning_log_id: UUID) -> LearningLog | None:
        stmt = select(LearningLogORM).where(
            LearningLogORM.id == learning_log_id, LearningLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(self, user_id: UUID) -> list[LearningLog]:
        stmt = select(LearningLogORM).where(LearningLogORM.user_id == user_id)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, learning_log: LearningLog) -> None:
        self._session.add(_to_orm(learning_log))

    def update(self, learning_log: LearningLog) -> None:
        stmt = select(LearningLogORM).where(
            LearningLogORM.id == learning_log.learning_log_id,
            LearningLogORM.user_id == learning_log.user_id,
        )
        orm = self._session.scalars(stmt).first()
        if orm is None:
            raise RecordNotFoundError(str(learning_log.learning_log_id))
        orm.started_at = learning_log.started_at
        orm.category = learning_log.category.value
        orm.location = (
            learning_log.location.value if learning_log.location is not None else None
        )
        orm.content = learning_log.content
        orm.breakdown = list(learning_log.breakdown)
        orm.duration_minutes = learning_log.duration_minutes
        orm.keywords = list(learning_log.keywords)
        orm.notes = list(learning_log.notes)

    def delete(self, user_id: UUID, learning_log_id: UUID) -> None:
        stmt = select(LearningLogORM).where(
            LearningLogORM.id == learning_log_id, LearningLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
