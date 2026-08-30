"""SqlAlchemyによる`GoalRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import GoalORM
from health_intelligence.domain.enums import GoalCategory, GoalStatus
from health_intelligence.domain.models import Goal
from health_intelligence.repositories.errors import RecordNotFoundError


def _to_domain(orm: GoalORM) -> Goal:
    return Goal(
        goal_id=orm.id,
        user_id=orm.user_id,
        title=orm.title,
        category=GoalCategory(orm.category),
        deadline=orm.deadline,
        status=GoalStatus(orm.status),
        created_at=orm.created_at,
    )


def _to_orm(goal: Goal) -> GoalORM:
    return GoalORM(
        id=goal.goal_id,
        user_id=goal.user_id,
        title=goal.title,
        category=goal.category.value,
        deadline=goal.deadline,
        status=goal.status.value,
        created_at=goal.created_at,
    )


class SqlAlchemyGoalRepository:
    """`repositories.protocols.GoalRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, goal_id: UUID) -> Goal | None:
        stmt = select(GoalORM).where(GoalORM.id == goal_id, GoalORM.user_id == user_id)
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(self, user_id: UUID) -> list[Goal]:
        stmt = select(GoalORM).where(GoalORM.user_id == user_id)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, goal: Goal) -> None:
        self._session.add(_to_orm(goal))

    def update(self, goal: Goal) -> None:
        stmt = select(GoalORM).where(GoalORM.id == goal.goal_id, GoalORM.user_id == goal.user_id)
        orm = self._session.scalars(stmt).first()
        if orm is None:
            raise RecordNotFoundError(str(goal.goal_id))
        orm.title = goal.title
        orm.category = goal.category.value
        orm.deadline = goal.deadline
        orm.status = goal.status.value
        orm.created_at = goal.created_at

    def delete(self, user_id: UUID, goal_id: UUID) -> None:
        stmt = select(GoalORM).where(GoalORM.id == goal_id, GoalORM.user_id == user_id)
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
