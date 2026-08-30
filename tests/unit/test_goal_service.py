"""GoalService.compute_task_progressのテスト。"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from health_intelligence.domain.enums import GoalCategory, GoalStatus, TaskLogType
from health_intelligence.domain.models import DailyTaskLog, Goal, Task
from health_intelligence.services.goal_service import GoalService


def _make_service(make_fake_uow_factory, *, tasks=None, daily_task_logs=None, goals=None):
    from tests.conftest import (
        FakeDailyTaskLogRepository,
        FakeGoalRepository,
        FakeTaskRepository,
    )

    uow_factory = make_fake_uow_factory(
        goals=FakeGoalRepository(goals or []),
        tasks=FakeTaskRepository(tasks or []),
        daily_task_logs=FakeDailyTaskLogRepository(daily_task_logs or []),
    )
    return GoalService(uow_factory)


def test_compute_task_progress_sums_quantity_and_duration(make_fake_uow_factory) -> None:
    user_id = uuid4()
    goal_id = uuid4()
    task_id = uuid4()
    task = Task(
        task_id=task_id,
        user_id=user_id,
        goal_id=goal_id,
        category=GoalCategory.STUDY,
        title="Chapter3演習問題",
        log_type=TaskLogType.COUNT_AND_DURATION,
        unit="問",
        created_at=datetime.now(UTC),
    )
    logs = [
        DailyTaskLog(
            daily_task_log_id=uuid4(),
            user_id=user_id,
            journal_date=date(2026, 8, 28),
            task_id=task_id,
            quantity=150,
            duration_minutes=60,
        ),
        DailyTaskLog(
            daily_task_log_id=uuid4(),
            user_id=user_id,
            journal_date=date(2026, 8, 29),
            task_id=task_id,
            quantity=300,
            duration_minutes=90,
        ),
    ]
    service = _make_service(make_fake_uow_factory, tasks=[task], daily_task_logs=logs)

    progresses = service.compute_task_progress(user_id, goal_id)

    assert len(progresses) == 1
    assert progresses[0].task == task
    assert progresses[0].total_quantity == 450
    assert progresses[0].total_duration_minutes == 150
    assert progresses[0].log_count == 2


def test_compute_task_progress_excludes_plan_only_tasks(make_fake_uow_factory) -> None:
    user_id = uuid4()
    goal_id = uuid4()
    plan_only_task = Task(
        task_id=uuid4(),
        user_id=user_id,
        goal_id=goal_id,
        category=GoalCategory.DIET,
        title="21時以降食べない",
        log_type=TaskLogType.PLAN_ONLY,
        created_at=datetime.now(UTC),
    )
    service = _make_service(make_fake_uow_factory, tasks=[plan_only_task])

    progresses = service.compute_task_progress(user_id, goal_id)

    assert progresses == []


def test_change_status_updates_goal_status(make_fake_uow_factory) -> None:
    from tests.conftest import FakeGoalRepository

    user_id = uuid4()
    goal = Goal(
        goal_id=uuid4(),
        user_id=user_id,
        title="Python3エンジニア認定実践試験合格",
        category=GoalCategory.STUDY,
        status=GoalStatus.IN_PROGRESS,
        created_at=datetime.now(UTC),
    )
    fake_goal_repo = FakeGoalRepository([goal])
    uow_factory = make_fake_uow_factory(goals=fake_goal_repo)
    service = GoalService(uow_factory)

    service.change_status(user_id, goal.goal_id, GoalStatus.ACHIEVED)

    updated = fake_goal_repo.get_by_id(user_id, goal.goal_id)
    assert updated is not None
    assert updated.status == GoalStatus.ACHIEVED
