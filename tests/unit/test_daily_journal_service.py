"""DailyJournalServiceのテスト。"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from uuid import uuid4

from health_intelligence.domain.models import DailyJournal, DailyTaskLog
from health_intelligence.services.daily_journal_service import DailyJournalService


def _make_service(
    make_fake_uow_factory,
    *,
    fake_daily_journal_repo,
    fake_daily_task_log_repo,
    fake_daily_plan_item_repo,
) -> DailyJournalService:
    uow_factory = make_fake_uow_factory(
        daily_journals=fake_daily_journal_repo,
        daily_task_logs=fake_daily_task_log_repo,
        daily_plan_items=fake_daily_plan_item_repo,
    )
    return DailyJournalService(uow_factory)


def test_get_or_create_draft_returns_unsaved_draft_when_missing(
    make_fake_uow_factory,
    fake_daily_journal_repo,
    fake_daily_task_log_repo,
    fake_daily_plan_item_repo,
) -> None:
    user_id = uuid4()
    journal_date = date(2026, 8, 30)
    service = _make_service(
        make_fake_uow_factory,
        fake_daily_journal_repo=fake_daily_journal_repo,
        fake_daily_task_log_repo=fake_daily_task_log_repo,
        fake_daily_plan_item_repo=fake_daily_plan_item_repo,
    )

    draft = service.get_or_create_draft(user_id, journal_date)

    assert draft.user_id == user_id
    assert draft.journal_date == journal_date
    assert service.get_journal(user_id, journal_date) is None


def test_get_or_create_draft_returns_existing_journal(
    make_fake_uow_factory, fake_daily_journal_repo
) -> None:
    user_id = uuid4()
    journal_date = date(2026, 8, 30)
    existing = DailyJournal(
        daily_journal_id=uuid4(),
        user_id=user_id,
        journal_date=journal_date,
        reflection_memo="既存の振り返り",
    )
    fake_daily_journal_repo.add(existing)
    uow_factory = make_fake_uow_factory(daily_journals=fake_daily_journal_repo)
    service = DailyJournalService(uow_factory)

    draft = service.get_or_create_draft(user_id, journal_date)

    assert draft == existing


def test_save_journal_does_not_overwrite_other_sections(
    make_fake_uow_factory, fake_daily_journal_repo
) -> None:
    """あるセクション保存後、他セクションの既存値が消えないこと(部分保存の整合性)。"""
    user_id = uuid4()
    journal_date = date(2026, 8, 30)
    existing = DailyJournal(
        daily_journal_id=uuid4(),
        user_id=user_id,
        journal_date=journal_date,
        reflection_memo="Cセクションの内容",
    )
    fake_daily_journal_repo.add(existing)
    uow_factory = make_fake_uow_factory(daily_journals=fake_daily_journal_repo)
    service = DailyJournalService(uow_factory)

    draft = service.get_or_create_draft(user_id, journal_date)
    service.save_journal(replace(draft, improvement_point="Aセクションの内容"))

    saved = service.get_journal(user_id, journal_date)
    assert saved is not None
    assert saved.reflection_memo == "Cセクションの内容"
    assert saved.improvement_point == "Aセクションの内容"


def test_save_plan_replaces_previous_selection(
    make_fake_uow_factory,
    fake_daily_journal_repo,
    fake_daily_task_log_repo,
    fake_daily_plan_item_repo,
) -> None:
    user_id = uuid4()
    journal_date = date(2026, 8, 30)
    task_a, task_b, task_c = uuid4(), uuid4(), uuid4()
    service = _make_service(
        make_fake_uow_factory,
        fake_daily_journal_repo=fake_daily_journal_repo,
        fake_daily_task_log_repo=fake_daily_task_log_repo,
        fake_daily_plan_item_repo=fake_daily_plan_item_repo,
    )

    service.save_plan(user_id, journal_date, [task_a, task_b])
    service.save_plan(user_id, journal_date, [task_c])

    plan = service.list_plan(user_id, journal_date)
    assert {item.task_id for item in plan} == {task_c}


def test_save_task_log_inserts_when_absent(
    make_fake_uow_factory,
    fake_daily_journal_repo,
    fake_daily_task_log_repo,
    fake_daily_plan_item_repo,
) -> None:
    user_id = uuid4()
    task_id = uuid4()
    journal_date = date(2026, 8, 30)
    service = _make_service(
        make_fake_uow_factory,
        fake_daily_journal_repo=fake_daily_journal_repo,
        fake_daily_task_log_repo=fake_daily_task_log_repo,
        fake_daily_plan_item_repo=fake_daily_plan_item_repo,
    )

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


def test_list_task_logs_in_range_returns_only_logs_within_range(
    make_fake_uow_factory,
    fake_daily_journal_repo,
    fake_daily_task_log_repo,
    fake_daily_plan_item_repo,
) -> None:
    user_id = uuid4()
    task_id = uuid4()
    service = _make_service(
        make_fake_uow_factory,
        fake_daily_journal_repo=fake_daily_journal_repo,
        fake_daily_task_log_repo=fake_daily_task_log_repo,
        fake_daily_plan_item_repo=fake_daily_plan_item_repo,
    )
    for d in (date(2026, 8, 28), date(2026, 8, 30), date(2026, 9, 2)):
        service.save_task_log(
            DailyTaskLog(
                daily_task_log_id=uuid4(),
                user_id=user_id,
                journal_date=d,
                task_id=task_id,
                quantity=1,
            )
        )

    logs = service.list_task_logs_in_range(user_id, date(2026, 8, 29), date(2026, 9, 1))

    assert [log.journal_date for log in logs] == [date(2026, 8, 30)]


def test_list_journals_in_range_returns_only_journals_within_range(
    make_fake_uow_factory, fake_daily_journal_repo
) -> None:
    user_id = uuid4()
    for d in (date(2026, 8, 28), date(2026, 8, 30), date(2026, 9, 2)):
        fake_daily_journal_repo.add(
            DailyJournal(daily_journal_id=uuid4(), user_id=user_id, journal_date=d)
        )
    uow_factory = make_fake_uow_factory(daily_journals=fake_daily_journal_repo)
    service = DailyJournalService(uow_factory)

    journals = service.list_journals_in_range(user_id, date(2026, 8, 29), date(2026, 9, 1))

    assert [j.journal_date for j in journals] == [date(2026, 8, 30)]


def test_save_task_log_updates_existing_entry_for_same_task_and_date(
    make_fake_uow_factory,
    fake_daily_journal_repo,
    fake_daily_task_log_repo,
    fake_daily_plan_item_repo,
) -> None:
    user_id = uuid4()
    task_id = uuid4()
    journal_date = date(2026, 8, 30)
    service = _make_service(
        make_fake_uow_factory,
        fake_daily_journal_repo=fake_daily_journal_repo,
        fake_daily_task_log_repo=fake_daily_task_log_repo,
        fake_daily_plan_item_repo=fake_daily_plan_item_repo,
    )

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
