"""goal_task_labels.pyの純粋関数のテスト。"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.goal_task_labels import (  # noqa: E402
    format_duration_option,
    format_task_progress,
)

from health_intelligence.domain.enums import GoalCategory, TaskLogType  # noqa: E402
from health_intelligence.domain.models import Task  # noqa: E402
from health_intelligence.services.goal_service import TaskProgress  # noqa: E402


def _make_task(unit: str | None = "問") -> Task:
    return Task(
        task_id=uuid4(),
        user_id=uuid4(),
        category=GoalCategory.STUDY,
        title="Chapter3演習問題",
        log_type=TaskLogType.COUNT_AND_DURATION,
        unit=unit,
        created_at=datetime.now(UTC),
    )


def test_format_task_progress_with_quantity_only() -> None:
    progress = TaskProgress(
        task=_make_task(), total_quantity=450, total_duration_minutes=0, log_count=3
    )

    assert format_task_progress(progress) == "累計450問"


def test_format_task_progress_with_quantity_and_duration() -> None:
    progress = TaskProgress(
        task=_make_task(unit=None), total_quantity=0, total_duration_minutes=750, log_count=5
    )

    assert format_task_progress(progress) == "累計12時間30分"


def test_format_task_progress_with_no_records() -> None:
    progress = TaskProgress(
        task=_make_task(), total_quantity=0, total_duration_minutes=0, log_count=0
    )

    assert format_task_progress(progress) == "まだ記録がありません"


def test_format_duration_option_caps_at_120_as_or_more() -> None:
    assert format_duration_option(15) == "15分"
    assert format_duration_option(120) == "120分以上"
