"""GoalService。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from health_intelligence.domain.enums import GoalStatus, TaskLogType
from health_intelligence.domain.models import Goal, Task
from health_intelligence.repositories.unit_of_work import UnitOfWork


@dataclass(frozen=True, kw_only=True, slots=True)
class TaskProgress:
    """`compute_task_progress`が返す、Task単位の累計実績
    (requirements.md 4.4節「累計450問」等の進捗表示に対応)。
    """

    task: Task
    total_quantity: float
    total_duration_minutes: int
    log_count: int


class GoalService:
    """Goal/Taskに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def create_goal(self, goal: Goal) -> None:
        with self._uow_factory() as uow:
            uow.goals.add(goal)
            uow.commit()

    def list_goals(self, user_id: UUID) -> list[Goal]:
        with self._uow_factory() as uow:
            return uow.goals.list_by_user(user_id)

    def get_goal(self, user_id: UUID, goal_id: UUID) -> Goal | None:
        with self._uow_factory() as uow:
            return uow.goals.get_by_id(user_id, goal_id)

    def update_goal(self, goal: Goal) -> None:
        with self._uow_factory() as uow:
            uow.goals.update(goal)
            uow.commit()

    def change_status(self, user_id: UUID, goal_id: UUID, status: GoalStatus) -> None:
        with self._uow_factory() as uow:
            goal = uow.goals.get_by_id(user_id, goal_id)
            if goal is None:
                return
            uow.goals.update(
                Goal(
                    goal_id=goal.goal_id,
                    user_id=goal.user_id,
                    title=goal.title,
                    category=goal.category,
                    deadline=goal.deadline,
                    status=status,
                    created_at=goal.created_at,
                )
            )
            uow.commit()

    def compute_task_progress(self, user_id: UUID, goal_id: UUID) -> list[TaskProgress]:
        """Goal配下のTask(log_type=COUNT_AND_DURATIONのみ)について、
        DailyTaskLogを集計した累計実績を返す。
        """
        with self._uow_factory() as uow:
            tasks = [
                task
                for task in uow.tasks.list_by_user(user_id, goal_id=goal_id)
                if task.log_type == TaskLogType.COUNT_AND_DURATION
            ]
            progresses = []
            for task in tasks:
                logs = uow.daily_task_logs.list_by_task(user_id, task.task_id)
                progresses.append(
                    TaskProgress(
                        task=task,
                        total_quantity=sum(log.quantity or 0 for log in logs),
                        total_duration_minutes=sum(log.duration_minutes or 0 for log in logs),
                        log_count=len(logs),
                    )
                )
            return progresses
