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

from components.workout_form import (  # noqa: E402
    build_workout_log,
    entries_to_rows,
    format_exercise_line,
    rows_to_entries,
)

from health_intelligence.domain.enums import ExerciseCategory  # noqa: E402
from health_intelligence.domain.models import WorkoutExercise, WorkoutSet  # noqa: E402


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


def test_rows_to_entries_groups_sets_and_ignores_empty_rows() -> None:
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
            "reps": 8,
            "weight_kg": 80,
        },
        {
            "exercise_name": "",
            "category": "",
            "duration_minutes": None,
            "reps": None,
            "weight_kg": None,
        },
    ]

    entries = rows_to_entries(rows)

    assert entries == [
        {
            "exercise_name": "有酸素運動",
            "category": "cardio",
            "duration_minutes": 25,
            "sets": [],
        },
        {
            "exercise_name": "レッグプレス",
            "category": "strength",
            "duration_minutes": None,
            "sets": [
                {"reps": 10, "weight_kg": 75},
                {"reps": 8, "weight_kg": 80},
            ],
        },
    ]


def test_entries_to_rows_is_inverse_of_rows_to_entries() -> None:
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
            "reps": 8,
            "weight_kg": 80,
        },
    ]

    entries = rows_to_entries(rows)

    assert entries_to_rows(entries) == rows


def test_entries_to_rows_keeps_exercise_with_no_sets_as_placeholder_row() -> None:
    entries = [
        {
            "exercise_name": "スクワット",
            "category": "strength",
            "duration_minutes": None,
            "sets": [],
        }
    ]

    rows = entries_to_rows(entries)

    assert rows == [
        {
            "exercise_name": "スクワット",
            "category": "strength",
            "duration_minutes": None,
            "reps": None,
            "weight_kg": None,
        }
    ]


def test_format_exercise_line_cardio() -> None:
    exercise = WorkoutExercise(
        exercise_name="有酸素運動", category=ExerciseCategory.CARDIO, duration_minutes=30
    )

    assert format_exercise_line(exercise) == "有酸素運動：30分"


def test_format_exercise_line_cardio_without_duration() -> None:
    exercise = WorkoutExercise(exercise_name="有酸素運動", category=ExerciseCategory.CARDIO)

    assert format_exercise_line(exercise) == "有酸素運動：-"


def test_format_exercise_line_strength_bodyweight_groups_identical_sets() -> None:
    exercise = WorkoutExercise(
        exercise_name="スクワット",
        category=ExerciseCategory.STRENGTH,
        sets=[WorkoutSet(reps=30, weight_kg=None)],
    )

    assert format_exercise_line(exercise) == "スクワット：30回 × 1"


def test_format_exercise_line_strength_weighted_groups_identical_sets() -> None:
    exercise = WorkoutExercise(
        exercise_name="レッグプレス",
        category=ExerciseCategory.STRENGTH,
        sets=[
            WorkoutSet(reps=10, weight_kg=75),
            WorkoutSet(reps=10, weight_kg=75),
        ],
    )

    assert format_exercise_line(exercise) == "レッグプレス：10回(75kg) × 2"


def test_format_exercise_line_strength_splits_differing_sets_into_groups() -> None:
    exercise = WorkoutExercise(
        exercise_name="ラットプルダウン",
        category=ExerciseCategory.STRENGTH,
        sets=[
            WorkoutSet(reps=10, weight_kg=30),
            WorkoutSet(reps=10, weight_kg=20),
        ],
    )

    assert format_exercise_line(exercise) == "ラットプルダウン：10回(30kg) × 1, 10回(20kg) × 1"


def test_format_exercise_line_strength_no_sets() -> None:
    exercise = WorkoutExercise(exercise_name="スクワット", category=ExerciseCategory.STRENGTH)

    assert format_exercise_line(exercise) == "スクワット：-"
