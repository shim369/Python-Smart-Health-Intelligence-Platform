"""pytest共通フィクスチャ。

実DB・実AI APIを使わずにService/Authenticator層のロジックを検証する
ための、最小限のFake Repository/UnitOfWorkを提供する。
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TypeVar
from uuid import UUID, uuid4

import pytest
from dotenv import load_dotenv

from health_intelligence.domain.models import (
    DailyJournal,
    DailyPlanItem,
    DailyTaskLog,
    Goal,
    Task,
    User,
)

load_dotenv()

# `.env.test`が存在する場合、DATABASE_URL等をテスト専用DBへ上書きする
# (override=True)。tests/integration/test_user_isolation.py や
# tests/unit/test_migrations.pyはDATABASE_URLへ実際にデータを書き込み・
# 全テーブルをdrop/再作成するため、日常使っているDB(.envのDATABASE_URL)
# を巻き込まないための分離。`.env.test`が無い環境(CI等)では何も
# 起きず、従来通り.envのDATABASE_URLがそのまま使われる。
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=_PROJECT_ROOT / ".env.test", override=True)

T = TypeVar("T")


class FakeUserRepository:
    """`UserRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self) -> None:
        self._by_email: dict[str, User] = {}
        self._by_id: dict[UUID, User] = {}

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email)

    def add(self, user: User) -> None:
        self._by_email[user.email] = user
        self._by_id[user.user_id] = user


class FakeUserCredentialRepository:
    """`UserCredentialRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self) -> None:
        self._hashes: dict[UUID, str] = {}

    def get_password_hash(self, user_id: UUID) -> str | None:
        return self._hashes.get(user_id)

    def set_password_hash(self, user_id: UUID, password_hash: str) -> None:
        self._hashes[user_id] = password_hash


class FakeListRepository[T]:
    """`list_by_user`のみを提供する汎用Fake Repository。

    RecommendationServiceのテスト等、`list_by_user`しか使わない
    Repositoryを毎回書くのを避けるための共通実装。
    """

    def __init__(self, items: list[T]) -> None:
        self._items = items

    def list_by_user(self, user_id: UUID) -> list[T]:
        return self._items


class FakeGoalRepository:
    """`GoalRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self, goals: list[Goal] | None = None) -> None:
        self._goals: dict[UUID, Goal] = {g.goal_id: g for g in (goals or [])}

    def get_by_id(self, user_id: UUID, goal_id: UUID) -> Goal | None:
        goal = self._goals.get(goal_id)
        return goal if goal is not None and goal.user_id == user_id else None

    def list_by_user(self, user_id: UUID) -> list[Goal]:
        return [g for g in self._goals.values() if g.user_id == user_id]

    def add(self, goal: Goal) -> None:
        self._goals[goal.goal_id] = goal

    def update(self, goal: Goal) -> None:
        self._goals[goal.goal_id] = goal

    def delete(self, user_id: UUID, goal_id: UUID) -> None:
        self._goals.pop(goal_id, None)


class FakeTaskRepository:
    """`TaskRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self, tasks: list[Task] | None = None) -> None:
        self._tasks: dict[UUID, Task] = {t.task_id: t for t in (tasks or [])}

    def get_by_id(self, user_id: UUID, task_id: UUID) -> Task | None:
        task = self._tasks.get(task_id)
        return task if task is not None and task.user_id == user_id else None

    def list_by_user(
        self, user_id: UUID, *, goal_id: UUID | None = None, include_archived: bool = True
    ) -> list[Task]:
        tasks = [t for t in self._tasks.values() if t.user_id == user_id]
        if goal_id is not None:
            tasks = [t for t in tasks if t.goal_id == goal_id]
        if not include_archived:
            tasks = [t for t in tasks if not t.is_archived]
        return tasks

    def add(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    def update(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    def delete(self, user_id: UUID, task_id: UUID) -> None:
        self._tasks.pop(task_id, None)


class FakeDailyPlanItemRepository:
    """`DailyPlanItemRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self, items: list[DailyPlanItem] | None = None) -> None:
        self._items: list[DailyPlanItem] = list(items or [])

    def list_by_date(self, user_id: UUID, journal_date: date) -> list[DailyPlanItem]:
        return [i for i in self._items if i.user_id == user_id and i.journal_date == journal_date]

    def replace_for_date(self, user_id: UUID, journal_date: date, task_ids: list[UUID]) -> None:
        self._items = [
            i for i in self._items if not (i.user_id == user_id and i.journal_date == journal_date)
        ]
        self._items.extend(
            DailyPlanItem(
                daily_plan_item_id=uuid4(), user_id=user_id, journal_date=journal_date, task_id=tid
            )
            for tid in task_ids
        )


class FakeDailyTaskLogRepository:
    """`DailyTaskLogRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self, logs: list[DailyTaskLog] | None = None) -> None:
        self._logs: dict[UUID, DailyTaskLog] = {log.daily_task_log_id: log for log in (logs or [])}

    def get_by_task_and_date(
        self, user_id: UUID, task_id: UUID, journal_date: date
    ) -> DailyTaskLog | None:
        for log in self._logs.values():
            if (
                log.user_id == user_id
                and log.task_id == task_id
                and log.journal_date == journal_date
            ):
                return log
        return None

    def list_by_date(self, user_id: UUID, journal_date: date) -> list[DailyTaskLog]:
        return [
            log
            for log in self._logs.values()
            if log.user_id == user_id and log.journal_date == journal_date
        ]

    def list_by_task(self, user_id: UUID, task_id: UUID) -> list[DailyTaskLog]:
        return [
            log for log in self._logs.values() if log.user_id == user_id and log.task_id == task_id
        ]

    def add(self, daily_task_log: DailyTaskLog) -> None:
        self._logs[daily_task_log.daily_task_log_id] = daily_task_log

    def update(self, daily_task_log: DailyTaskLog) -> None:
        self._logs[daily_task_log.daily_task_log_id] = daily_task_log

    def delete(self, user_id: UUID, daily_task_log_id: UUID) -> None:
        self._logs.pop(daily_task_log_id, None)


class FakeDailyJournalRepository:
    """`DailyJournalRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self, journals: list[DailyJournal] | None = None) -> None:
        self._journals: dict[UUID, DailyJournal] = {j.daily_journal_id: j for j in (journals or [])}

    def get_by_date(self, user_id: UUID, journal_date: date) -> DailyJournal | None:
        for journal in self._journals.values():
            if journal.user_id == user_id and journal.journal_date == journal_date:
                return journal
        return None

    def add(self, daily_journal: DailyJournal) -> None:
        self._journals[daily_journal.daily_journal_id] = daily_journal

    def update(self, daily_journal: DailyJournal) -> None:
        self._journals[daily_journal.daily_journal_id] = daily_journal


class FakeUnitOfWork:
    """テストで使うRepositoryだけを動的に持たせるUnitOfWork。

    UnitOfWork Protocolはstructural typing(Protocol)のため、実行時に
    使わない属性が存在しなくても、そのテストが触れない限り問題ない。
    """

    def __init__(self, **repositories: object) -> None:
        for name, repo in repositories.items():
            setattr(self, name, repo)

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


@pytest.fixture
def fake_user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def fake_credential_repo() -> FakeUserCredentialRepository:
    return FakeUserCredentialRepository()


@pytest.fixture
def fake_goal_repo() -> FakeGoalRepository:
    return FakeGoalRepository()


@pytest.fixture
def fake_task_repo() -> FakeTaskRepository:
    return FakeTaskRepository()


@pytest.fixture
def fake_daily_plan_item_repo() -> FakeDailyPlanItemRepository:
    return FakeDailyPlanItemRepository()


@pytest.fixture
def fake_daily_task_log_repo() -> FakeDailyTaskLogRepository:
    return FakeDailyTaskLogRepository()


@pytest.fixture
def fake_daily_journal_repo() -> FakeDailyJournalRepository:
    return FakeDailyJournalRepository()


@pytest.fixture
def make_fake_uow_factory():
    """任意のRepositoryキーワード引数からFakeUnitOfWork factoryを組み立てる。

    使用例: `make_fake_uow_factory(users=fake_user_repo, ...)`
    """

    def _factory(**repositories: object):
        return lambda: FakeUnitOfWork(**repositories)

    return _factory


@pytest.fixture
def fake_list_repository_factory():
    """`FakeListRepository`のコンストラクタをそのまま返すフィクスチャ。"""
    return FakeListRepository
