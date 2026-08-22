"""`app/components/workout_form.build_workout_log`のテスト。

app/はsrc/health_intelligenceとは別のトップレベルディレクトリのため、
importできるようsys.pathへ明示的に追加する。
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.workout_form import build_workout_log  # noqa: E402


def test_build_workout_log_groups_same_exercise_into_sets() -> None:
    rows = [
        {
            "exercise_name": "有酸素運動",
            "category": "cardio",
            "duration_minutes": 25,
            "reps": None,
            "weight_kg": None,
        },
        {
            "exercise_name": "レッグプレス",
            "category": "strength",
            "duration_minutes": None,
            "reps": 10,
            "weight_kg": 75,
        },
        {
            "exercise_name": "レッグプレス",
            "category": "strength",
            "duration_minutes": None,
            "reps": 10,
            "weight_kg": 75,
        },
        {
            "exercise_name": "ラットプルダウン",
            "category": "strength",
            "duration_minutes": None,
            "reps": 10,
            "weight_kg": 30,
        },
        {
            "exercise_name": "ラットプルダウン",
            "category": "strength",
            "duration_minutes": None,
            "reps": 10,
            "weight_kg": 20,
        },
    ]

    log = build_workout_log(
        rows,
        user_id=uuid4(),
        performed_at=datetime.now(UTC),
    )

    assert len(log.exercises) == 3
    lat = next(e for e in log.exercises if e.exercise_name == "ラットプルダウン")
    assert [s.weight_kg for s in lat.sets] == [30, 20]


def test_empty_rows_are_ignored() -> None:
    rows = [
        {
            "exercise_name": "",
            "category": "",
            "duration_minutes": None,
            "reps": None,
            "weight_kg": None,
        }
    ]

    log = build_workout_log(
        rows,
        user_id=uuid4(),
        performed_at=datetime.now(UTC),
    )

    assert log.exercises == []
