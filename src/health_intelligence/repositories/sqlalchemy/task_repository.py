"""SqlAlchemyによる`TaskRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import TaskORM
from health_intelligence.domain.enums import GoalCategory, TaskLogType
from health_intelligence.domain.models import Task
from health_intelligence.repositories.errors import RecordNotFoundError


def _to_domain(orm: TaskORM) -> Task:
    return Task(
        task_id=orm.id,
        user_id=orm.user_id,
        goal_id=orm.goal_id,
        category=GoalCategory(orm.category),
        title=orm.title,
        log_type=TaskLogType(orm.log_type),
        unit=orm.unit,
        is_archived=orm.is_archived,
        created_at=orm.created_at,
    )


def _to_orm(task: Task) -> TaskORM:
    return TaskORM(
        id=task.task_id,
        user_id=task.user_id,
        goal_id=task.goal_id,
        category=task.category.value,
        title=task.title,
        log_type=task.log_type.value,
        unit=task.unit,
        is_archived=task.is_archived,
        created_at=task.created_at,
    )


class SqlAlchemyTaskRepository:
    """`repositories.protocols.TaskRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, task_id: UUID) -> Task | None:
        stmt = select(TaskORM).where(TaskORM.id == task_id, TaskORM.user_id == user_id)
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(
        self, user_id: UUID, *, goal_id: UUID | None = None, include_archived: bool = True
    ) -> list[Task]:
        stmt = select(TaskORM).where(TaskORM.user_id == user_id)
        if goal_id is not None:
            stmt = stmt.where(TaskORM.goal_id == goal_id)
        if not include_archived:
            stmt = stmt.where(TaskORM.is_archived.is_(False))
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, task: Task) -> None:
        self._session.add(_to_orm(task))

    def update(self, task: Task) -> None:
        stmt = select(TaskORM).where(TaskORM.id == task.task_id, TaskORM.user_id == task.user_id)
        orm = self._session.scalars(stmt).first()
        if orm is None:
            raise RecordNotFoundError(str(task.task_id))
        orm.goal_id = task.goal_id
        orm.category = task.category.value
        orm.title = task.title
        orm.log_type = task.log_type.value
        orm.unit = task.unit
        orm.is_archived = task.is_archived
        orm.created_at = task.created_at

    def delete(self, user_id: UUID, task_id: UUID) -> None:
        stmt = select(TaskORM).where(TaskORM.id == task_id, TaskORM.user_id == user_id)
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
