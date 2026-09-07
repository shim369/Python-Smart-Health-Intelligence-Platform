"""user_idによるデータ分離を検証するIntegration Test。

実際のPostgreSQL(Neon等)への接続を必要とする。schema.pyが
PostgreSQL固有の型(`postgresql.UUID` / `postgresql.ARRAY`)を
使っているため、SQLiteのような軽量DBでは代替できない。

ローカルで実行する場合は、テスト用DBを指すDATABASE_URLを設定し、
`alembic upgrade head`でスキーマを適用してから実行すること。
DATABASE_URLが未設定の場合は自動的にスキップする。

CI(GitHub Actions)では.github/workflows/ci.ymlにPostgresサービス
コンテナとDATABASE_URLを設定済みで、`alembic upgrade head`を
実行した後にこのテストも自動実行される。
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    DATABASE_URL is None,
    reason="DATABASE_URL が未設定のためIntegration Testをスキップ",
)


@pytest.fixture
def uow_factory():
    from health_intelligence.repositories.sqlalchemy import build_uow_factory

    return build_uow_factory()


def test_user_cannot_see_other_users_meal_logs(uow_factory) -> None:
    from health_intelligence.domain.enums import MealType
    from health_intelligence.domain.models import MealLog, User

    user_a_id, user_b_id = uuid4(), uuid4()

    with uow_factory() as uow:
        uow.users.add(
            User(
                user_id=user_a_id,
                email=f"{user_a_id}@example.com",
                display_name="User A",
                created_at=datetime.now(UTC),
            )
        )
        uow.users.add(
            User(
                user_id=user_b_id,
                email=f"{user_b_id}@example.com",
                display_name="User B",
                created_at=datetime.now(UTC),
            )
        )
        uow.meal_logs.add(
            MealLog(
                meal_log_id=uuid4(),
                user_id=user_a_id,
                consumed_at=datetime.now(UTC),
                meal_type=MealType.LUNCH,
                calories=500,
                protein_g=20,
                fat_g=10,
                carbohydrate_g=60,
            )
        )
        uow.commit()

    with uow_factory() as uow:
        user_a_logs = uow.meal_logs.list_by_user(user_a_id)
        user_b_logs = uow.meal_logs.list_by_user(user_b_id)

    assert len(user_a_logs) == 1
    assert len(user_b_logs) == 0


def _create_two_users(uow) -> tuple[UUID, UUID]:
    from health_intelligence.domain.models import User

    user_a_id, user_b_id = uuid4(), uuid4()
    for user_id in (user_a_id, user_b_id):
        uow.users.add(
            User(
                user_id=user_id,
                email=f"{user_id}@example.com",
                display_name=str(user_id),
                created_at=datetime.now(UTC),
            )
        )
    return user_a_id, user_b_id


def test_user_cannot_see_other_users_goals(uow_factory) -> None:
    from health_intelligence.domain.enums import GoalCategory
    from health_intelligence.domain.models import Goal

    with uow_factory() as uow:
        user_a_id, user_b_id = _create_two_users(uow)
        uow.goals.add(
            Goal(
                goal_id=uuid4(),
                user_id=user_a_id,
                title="Python3エンジニア認定実践試験合格",
                category=GoalCategory.STUDY,
                created_at=datetime.now(UTC),
            )
        )
        uow.commit()

    with uow_factory() as uow:
        assert len(uow.goals.list_by_user(user_a_id)) == 1
        assert len(uow.goals.list_by_user(user_b_id)) == 0


def test_user_cannot_see_other_users_tasks(uow_factory) -> None:
    from health_intelligence.domain.enums import GoalCategory, TaskLogType
    from health_intelligence.domain.models import Task

    with uow_factory() as uow:
        user_a_id, user_b_id = _create_two_users(uow)
        uow.tasks.add(
            Task(
                task_id=uuid4(),
                user_id=user_a_id,
                category=GoalCategory.STUDY,
                title="Chapter3演習問題",
                log_type=TaskLogType.COUNT_AND_DURATION,
                unit="問",
                created_at=datetime.now(UTC),
            )
        )
        uow.commit()

    with uow_factory() as uow:
        assert len(uow.tasks.list_by_user(user_a_id)) == 1
        assert len(uow.tasks.list_by_user(user_b_id)) == 0


def test_user_cannot_see_other_users_daily_plan_items(uow_factory) -> None:
    from health_intelligence.domain.enums import GoalCategory, TaskLogType
    from health_intelligence.domain.models import Task

    journal_date = datetime.now(UTC).date()

    with uow_factory() as uow:
        user_a_id, user_b_id = _create_two_users(uow)
        uow.commit()

    # TaskORM/DailyPlanItemORMには明示的なORM relationshipが無く、
    # SQLAlchemyのflushはmapper間の依存関係(insert順序)を保証しない。
    # 同一トランザクションでTaskとその外部キー参照先を両方addすると、
    # 挿入順が入れ替わりForeignKeyViolationになりうるため、Task作成は
    # 別トランザクションでcommitしてから参照する(実際のアプリでも
    # Task作成とDailyPlanItem作成は別のService呼び出しであり、この方が
    # 実運用の順序にも近い)。
    task_id = uuid4()
    with uow_factory() as uow:
        uow.tasks.add(
            Task(
                task_id=task_id,
                user_id=user_a_id,
                category=GoalCategory.STUDY,
                title="AWS動画教材",
                log_type=TaskLogType.COUNT_AND_DURATION,
                created_at=datetime.now(UTC),
            )
        )
        uow.commit()

    with uow_factory() as uow:
        uow.daily_plan_items.replace_for_date(user_a_id, journal_date, [task_id])
        uow.commit()

    with uow_factory() as uow:
        assert len(uow.daily_plan_items.list_by_date(user_a_id, journal_date)) == 1
        assert len(uow.daily_plan_items.list_by_date(user_b_id, journal_date)) == 0


def test_user_cannot_see_other_users_daily_task_logs(uow_factory) -> None:
    from health_intelligence.domain.enums import GoalCategory, TaskLogType
    from health_intelligence.domain.models import DailyTaskLog, Task

    journal_date = datetime.now(UTC).date()

    with uow_factory() as uow:
        user_a_id, user_b_id = _create_two_users(uow)
        uow.commit()

    # test_user_cannot_see_other_users_daily_plan_itemsと同じ理由で、
    # Task作成は別トランザクションでcommitしてから参照する。
    task_id = uuid4()
    with uow_factory() as uow:
        uow.tasks.add(
            Task(
                task_id=task_id,
                user_id=user_a_id,
                category=GoalCategory.STUDY,
                title="Chapter3演習問題",
                log_type=TaskLogType.COUNT_AND_DURATION,
                unit="問",
                created_at=datetime.now(UTC),
            )
        )
        uow.commit()

    with uow_factory() as uow:
        uow.daily_task_logs.add(
            DailyTaskLog(
                daily_task_log_id=uuid4(),
                user_id=user_a_id,
                journal_date=journal_date,
                task_id=task_id,
                quantity=50,
            )
        )
        uow.commit()

    with uow_factory() as uow:
        assert len(uow.daily_task_logs.list_by_date(user_a_id, journal_date)) == 1
        assert len(uow.daily_task_logs.list_by_date(user_b_id, journal_date)) == 0


def test_user_cannot_see_other_users_daily_journal(uow_factory) -> None:
    from health_intelligence.domain.models import DailyJournal

    journal_date = datetime.now(UTC).date()

    with uow_factory() as uow:
        user_a_id, user_b_id = _create_two_users(uow)
        uow.daily_journals.add(
            DailyJournal(
                daily_journal_id=uuid4(),
                user_id=user_a_id,
                journal_date=journal_date,
                reflection_memo="今日の振り返り",
            )
        )
        uow.commit()

    with uow_factory() as uow:
        assert uow.daily_journals.get_by_date(user_a_id, journal_date) is not None
        assert uow.daily_journals.get_by_date(user_b_id, journal_date) is None
