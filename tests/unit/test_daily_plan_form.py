"""daily_plan_form.pyの純粋関数のテスト。"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.daily_plan_form import resolve_initial_plan_task_ids  # noqa: E402


def test_uses_todays_plan_when_already_saved() -> None:
    today_ids = {uuid4()}
    yesterday_ids = {uuid4()}

    resolved, copied_from_yesterday = resolve_initial_plan_task_ids(today_ids, yesterday_ids)

    assert resolved == today_ids
    assert copied_from_yesterday is False


def test_copies_yesterdays_plan_when_today_is_empty() -> None:
    yesterday_ids = {uuid4(), uuid4()}

    resolved, copied_from_yesterday = resolve_initial_plan_task_ids(set(), yesterday_ids)

    assert resolved == yesterday_ids
    assert copied_from_yesterday is True


def test_returns_empty_when_both_empty() -> None:
    resolved, copied_from_yesterday = resolve_initial_plan_task_ids(set(), set())

    assert resolved == set()
    assert copied_from_yesterday is True
