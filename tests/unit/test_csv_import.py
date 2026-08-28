"""`app/components/csv_import`のテスト。

app/はsrc/health_intelligenceとは別のトップレベルディレクトリのため、
importできるようsys.pathへ明示的に追加する(test_workout_form.pyと
同じパターン)。
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.csv_import import (  # noqa: E402
    parse_health_rows,
    parse_meal_rows,
    parse_sleep_rows,
    parse_weight_rows,
    parse_workout_rows,
)


def test_parse_weight_rows_success() -> None:
    user_id = uuid4()
    rows = [
        {"date": "2026-06-01", "time": "07:00", "weight_kg": "65.5"},
        {"date": "2026-06-02", "time": "", "weight_kg": "65.2"},
    ]

    result = parse_weight_rows(rows, user_id=user_id)

    assert result.errors == []
    assert len(result.logs) == 2
    assert result.logs[0].weight_kg == 65.5
    assert result.logs[0].user_id == user_id


def test_parse_weight_rows_reports_errors_without_failing_other_rows() -> None:
    rows = [
        {"date": "not-a-date", "time": "07:00", "weight_kg": "65.5"},
        {"date": "2026-06-02", "time": "07:00", "weight_kg": "not-a-number"},
        {"date": "2026-06-03", "time": "07:00", "weight_kg": "65.0"},
    ]

    result = parse_weight_rows(rows, user_id=uuid4())

    assert len(result.logs) == 1
    assert len(result.errors) == 2
    assert result.errors[0].row_number == 2
    assert result.errors[1].row_number == 3


def test_parse_sleep_rows_success_and_duration() -> None:
    rows = [
        {
            "bedtime_date": "2026-06-01",
            "bedtime_time": "23:30",
            "wake_date": "2026-06-02",
            "wake_time": "07:00",
            "quality": "good",
        }
    ]

    result = parse_sleep_rows(rows, user_id=uuid4())

    assert result.errors == []
    assert len(result.logs) == 1
    assert result.logs[0].duration_minutes == 450


def test_parse_sleep_rows_rejects_wake_before_bedtime() -> None:
    rows = [
        {
            "bedtime_date": "2026-06-02",
            "bedtime_time": "07:00",
            "wake_date": "2026-06-01",
            "wake_time": "23:30",
            "quality": "",
        }
    ]

    result = parse_sleep_rows(rows, user_id=uuid4())

    assert result.logs == []
    assert len(result.errors) == 1


def test_parse_meal_rows_success() -> None:
    rows = [
        {
            "date": "2026-06-01",
            "time": "08:00",
            "meal_type": "breakfast",
            "calories": "450",
            "protein_g": "20",
            "fat_g": "15",
            "carbohydrate_g": "55",
            "memo": "納豆ご飯",
        }
    ]

    result = parse_meal_rows(rows, user_id=uuid4())

    assert result.errors == []
    log = result.logs[0]
    assert log.calories == 450
    assert log.memo == "納豆ご飯"


def test_parse_meal_rows_rejects_invalid_meal_type() -> None:
    rows = [
        {
            "date": "2026-06-01",
            "time": "08:00",
            "meal_type": "brunch",
            "calories": "450",
            "protein_g": "20",
            "fat_g": "15",
            "carbohydrate_g": "55",
            "memo": "",
        }
    ]

    result = parse_meal_rows(rows, user_id=uuid4())

    assert result.logs == []
    assert len(result.errors) == 1
    assert "meal_type" in result.errors[0].message


def test_parse_health_rows_splits_symptoms_by_semicolon() -> None:
    rows = [
        {
            "date": "2026-06-01",
            "time": "08:00",
            "condition_score": "3",
            "symptoms": "頭痛;倦怠感",
            "memo": "",
        }
    ]

    result = parse_health_rows(rows, user_id=uuid4())

    assert result.errors == []
    assert result.logs[0].symptoms == ["頭痛", "倦怠感"]
    assert result.logs[0].condition_score == 3


def test_parse_health_rows_rejects_out_of_range_score() -> None:
    rows = [
        {
            "date": "2026-06-01",
            "time": "08:00",
            "condition_score": "9",
            "symptoms": "",
            "memo": "",
        }
    ]

    result = parse_health_rows(rows, user_id=uuid4())

    assert result.logs == []
    assert len(result.errors) == 1


def test_parse_workout_rows_groups_same_session_into_one_log() -> None:
    rows = [
        {
            "date": "2026-06-01",
            "time": "19:00",
            "exercise_name": "レッグプレス",
            "category": "strength",
            "duration_minutes": "",
            "reps": "10",
            "weight_kg": "75",
        },
        {
            "date": "2026-06-01",
            "time": "19:00",
            "exercise_name": "レッグプレス",
            "category": "strength",
            "duration_minutes": "",
            "reps": "10",
            "weight_kg": "75",
        },
        {
            "date": "2026-06-01",
            "time": "19:00",
            "exercise_name": "有酸素運動",
            "category": "cardio",
            "duration_minutes": "25",
            "reps": "",
            "weight_kg": "",
        },
        {
            "date": "2026-06-02",
            "time": "19:00",
            "exercise_name": "ベンチプレス",
            "category": "strength",
            "duration_minutes": "",
            "reps": "8",
            "weight_kg": "60",
        },
    ]

    result = parse_workout_rows(rows, user_id=uuid4())

    assert result.errors == []
    assert len(result.logs) == 2
    first_session = result.logs[0]
    assert len(first_session.exercises) == 2
    leg_press = next(
        e for e in first_session.exercises if e.exercise_name == "レッグプレス"
    )
    assert len(leg_press.sets) == 2


def test_parse_workout_rows_rejects_invalid_category() -> None:
    rows = [
        {
            "date": "2026-06-01",
            "time": "19:00",
            "exercise_name": "レッグプレス",
            "category": "cardiostrength",
            "duration_minutes": "",
            "reps": "10",
            "weight_kg": "75",
        }
    ]

    result = parse_workout_rows(rows, user_id=uuid4())

    assert result.logs == []
    assert len(result.errors) == 1
