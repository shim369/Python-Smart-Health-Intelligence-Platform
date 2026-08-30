"""GoalService.compute_task_progressのテスト。"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from health_intelligence.domain.enums import GoalCategory, GoalStatus, TaskLogType
from health_intelligence.domain.models import DailyTaskLog, Goal, Task
from health_intelligence.services.goal_service import GoalService


def test_compute_task_progress_sums_quantity_and_duration(
    make_fake_uow_factory, fake_goal_repo, fake_task_repo, fake_daily_task_log_repo
) -> None:
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
    fake_task_repo.add(task)
    fake_daily_task_log_repo.add(
        DailyTaskLog(
            daily_task_log_id=uuid4(),
            user_id=user_id,
            journal_date=date(2026, 8, 28),
            task_id=task_id,
            quantity=150,
            duration_minutes=60,
        )
    )
    fake_daily_task_log_repo.add(
        DailyTaskLog(
            daily_task_log_id=uuid4(),
            user_id=user_id,
            journal_date=date(2026, 8, 29),
            task_id=task_id,
            quantity=300,
            duration_minutes=90,
        )
    )
    uow_factory = make_fake_uow_factory(
        goals=fake_goal_repo, tasks=fake_task_repo, daily_task_logs=fake_daily_task_log_repo
    )
    service = GoalService(uow_factory)

    progresses = service.compute_task_progress(user_id, goal_id)

    assert len(progresses) == 1
    assert progresses[0].task == task
    assert progresses[0].total_quantity == 450
    assert progresses[0].total_duration_minutes == 150
    assert progresses[0].log_count == 2


def test_compute_task_progress_excludes_plan_only_tasks(
    make_fake_uow_factory, fake_goal_repo, fake_task_repo, fake_daily_task_log_repo
) -> None:
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
    fake_task_repo.add(plan_only_task)
    uow_factory = make_fake_uow_factory(
        goals=fake_goal_repo, tasks=fake_task_repo, daily_task_logs=fake_daily_task_log_repo
    )
    service = GoalService(uow_factory)

    progresses = service.compute_task_progress(user_id, goal_id)

    assert progresses == []


def test_change_status_updates_goal_status(make_fake_uow_factory, fake_goal_repo) -> None:
    user_id = uuid4()
    goal = Goal(
        goal_id=uuid4(),
        user_id=user_id,
        title="Python3エンジニア認定実践試験合格",
        category=GoalCategory.STUDY,
        status=GoalStatus.IN_PROGRESS,
        created_at=datetime.now(UTC),
    )
    fake_goal_repo.add(goal)
    uow_factory = make_fake_uow_factory(goals=fake_goal_repo)
    service = GoalService(uow_factory)

    service.change_status(user_id, goal.goal_id, GoalStatus.ACHIEVED)

    updated = fake_goal_repo.get_by_id(user_id, goal.goal_id)
    assert updated is not None
    assert updated.status == GoalStatus.ACHIEVED
