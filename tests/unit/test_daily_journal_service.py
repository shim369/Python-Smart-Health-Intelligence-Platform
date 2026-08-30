"""DailyJournalServiceのテスト。"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from health_intelligence.domain.models import DailyJournal, DailyTaskLog
from health_intelligence.services.daily_journal_service import DailyJournalService


def _make_service(
    make_fake_uow_factory,
    *,
    daily_journals=None,
    daily_task_logs=None,
    daily_plan_items=None,
):
    from tests.conftest import (
        FakeDailyJournalRepository,
        FakeDailyPlanItemRepository,
        FakeDailyTaskLogRepository,
    )

    uow_factory = make_fake_uow_factory(
        daily_journals=FakeDailyJournalRepository(daily_journals or []),
        daily_task_logs=FakeDailyTaskLogRepository(daily_task_logs or []),
        daily_plan_items=FakeDailyPlanItemRepository(daily_plan_items or []),
    )
    return service_for(uow_factory)


def service_for(uow_factory) -> DailyJournalService:
    return DailyJournalService(uow_factory)


def test_get_or_create_draft_returns_unsaved_draft_when_missing(make_fake_uow_factory) -> None:
    user_id = uuid4()
    journal_date = date(2026, 8, 30)
    service = _make_service(make_fake_uow_factory)

    draft = service.get_or_create_draft(user_id, journal_date)

    assert draft.user_id == user_id
    assert draft.journal_date == journal_date
    assert service.get_journal(user_id, journal_date) is None


def test_get_or_create_draft_returns_existing_journal(make_fake_uow_factory) -> None:
    from tests.conftest import FakeDailyJournalRepository

    user_id = uuid4()
    journal_date = date(2026, 8, 30)
    existing = DailyJournal(
        daily_journal_id=uuid4(),
        user_id=user_id,
        journal_date=journal_date,
        reflection_memo="既存の振り返り",
    )
    uow_factory = make_fake_uow_factory(daily_journals=FakeDailyJournalRepository([existing]))
    service = service_for(uow_factory)

    draft = service.get_or_create_draft(user_id, journal_date)

    assert draft == existing


def test_save_journal_does_not_overwrite_other_sections(make_fake_uow_factory) -> None:
    """あるセクション保存後、他セクションの既存値が消えないこと(部分保存の整合性)。"""
    from dataclasses import replace

    from tests.conftest import FakeDailyJournalRepository

    user_id = uuid4()
    journal_date = date(2026, 8, 30)
    existing = DailyJournal(
        daily_journal_id=uuid4(),
        user_id=user_id,
        journal_date=journal_date,
        reflection_memo="Cセクションの内容",
    )
    uow_factory = make_fake_uow_factory(daily_journals=FakeDailyJournalRepository([existing]))
    service = service_for(uow_factory)

    draft = service.get_or_create_draft(user_id, journal_date)
    service.save_journal(replace(draft, improvement_point="Aセクションの内容"))

    saved = service.get_journal(user_id, journal_date)
    assert saved is not None
    assert saved.reflection_memo == "Cセクションの内容"
    assert saved.improvement_point == "Aセクションの内容"


def test_save_plan_replaces_previous_selection(make_fake_uow_factory) -> None:
    user_id = uuid4()
    journal_date = date(2026, 8, 30)
    task_a, task_b, task_c = uuid4(), uuid4(), uuid4()
    service = _make_service(make_fake_uow_factory)

    service.save_plan(user_id, journal_date, [task_a, task_b])
    service.save_plan(user_id, journal_date, [task_c])

    plan = service.list_plan(user_id, journal_date)
    assert {item.task_id for item in plan} == {task_c}


def test_save_task_log_inserts_when_absent(make_fake_uow_factory) -> None:
    user_id = uuid4()
    task_id = uuid4()
    journal_date = date(2026, 8, 30)
    service = _make_service(make_fake_uow_factory)

    service.save_task_log(
        DailyTaskLog(
            daily_task_log_id=uuid4(),
            user_id=user_id,
            journal_date=journal_date,
            task_id=task_id,
            quantity=10,
        )
    )

    logs = service.list_task_logs(user_id, journal_date)
    assert len(logs) == 1
    assert logs[0].quantity == 10


def test_save_task_log_updates_existing_entry_for_same_task_and_date(make_fake_uow_factory) -> None:
    user_id = uuid4()
    task_id = uuid4()
    journal_date = date(2026, 8, 30)
    service = _make_service(make_fake_uow_factory)

    service.save_task_log(
        DailyTaskLog(
            daily_task_log_id=uuid4(),
            user_id=user_id,
            journal_date=journal_date,
            task_id=task_id,
            quantity=10,
        )
    )
    service.save_task_log(
        DailyTaskLog(
            daily_task_log_id=uuid4(),
            user_id=user_id,
            journal_date=journal_date,
            task_id=task_id,
            quantity=25,
        )
    )

    logs = service.list_task_logs(user_id, journal_date)
    assert len(logs) == 1
    assert logs[0].quantity == 25
