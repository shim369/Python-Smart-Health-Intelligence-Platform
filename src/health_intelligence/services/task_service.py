"""TaskService。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from uuid import UUID

from health_intelligence.domain.models import Task
from health_intelligence.repositories.unit_of_work import UnitOfWork


class TaskService:
    """Taskに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def create_task(self, task: Task) -> None:
        with self._uow_factory() as uow:
            uow.tasks.add(task)
            uow.commit()

    def list_tasks(
        self, user_id: UUID, *, goal_id: UUID | None = None, include_archived: bool = True
    ) -> list[Task]:
        with self._uow_factory() as uow:
            return uow.tasks.list_by_user(
                user_id, goal_id=goal_id, include_archived=include_archived
            )

    def get_task(self, user_id: UUID, task_id: UUID) -> Task | None:
        with self._uow_factory() as uow:
            return uow.tasks.get_by_id(user_id, task_id)

    def update_task(self, task: Task) -> None:
        with self._uow_factory() as uow:
            uow.tasks.update(task)
            uow.commit()

    def archive_task(self, user_id: UUID, task_id: UUID) -> None:
        self._set_archived(user_id, task_id, is_archived=True)

    def unarchive_task(self, user_id: UUID, task_id: UUID) -> None:
        self._set_archived(user_id, task_id, is_archived=False)

    def _set_archived(self, user_id: UUID, task_id: UUID, *, is_archived: bool) -> None:
        with self._uow_factory() as uow:
            task = uow.tasks.get_by_id(user_id, task_id)
            if task is None:
                return
            uow.tasks.update(replace(task, is_archived=is_archived))
            uow.commit()
