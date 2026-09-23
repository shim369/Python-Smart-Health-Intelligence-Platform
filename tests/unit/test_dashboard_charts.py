"""dashboard_charts.pyの純粋関数のテスト。"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.dashboard_charts import (  # noqa: E402
    cardio_minutes_by_exercise,
    group_average_by_date,
    group_sum_by_date,
    last_n_days,
    strength_max_weight_by_exercise,
)

from health_intelligence.domain.enums import ExerciseCategory  # noqa: E402
from health_intelligence.domain.models import (  # noqa: E402
    WorkoutExercise,
    WorkoutLog,
    WorkoutSet,
)


@dataclass
class _Item:
    day: date
    value: float | None


def test_last_n_days_returns_ascending_range_including_reference() -> None:
    result = last_n_days(date(2026, 8, 30), 7)

    assert result == [
        date(2026, 8, 24),
        date(2026, 8, 25),
        date(2026, 8, 26),
        date(2026, 8, 27),
        date(2026, 8, 28),
        date(2026, 8, 29),
        date(2026, 8, 30),
    ]


def test_group_sum_by_date_sums_matching_dates_and_ignores_others() -> None:
    dates = last_n_days(date(2026, 8, 30), 3)
    items = [
        _Item(date(2026, 8, 29), 10),
        _Item(date(2026, 8, 29), 5),
        _Item(date(2026, 8, 30), 3),
        _Item(date(2026, 8, 1), 999),  # 範囲外なので無視される
    ]

    result = group_sum_by_date(items, lambda i: i.day, lambda i: i.value, dates)

    assert result == [0.0, 15.0, 3.0]


def test_group_sum_by_date_returns_zero_for_empty_days() -> None:
    dates = last_n_days(date(2026, 8, 30), 3)

    result = group_sum_by_date([], lambda i: i.day, lambda i: i.value, dates)

    assert result == [0.0, 0.0, 0.0]


def test_group_average_by_date_averages_and_skips_none_values() -> None:
    dates = last_n_days(date(2026, 8, 30), 2)
    items = [
        _Item(date(2026, 8, 30), 4),
        _Item(date(2026, 8, 30), 2),
        _Item(date(2026, 8, 30), None),
    ]

    result = group_average_by_date(items, lambda i: i.day, lambda i: i.value, dates)

    assert result == [None, 3.0]


_D1, _D2, _D3 = date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)


def _strength(name: str, *sets: tuple[int, float | None]) -> WorkoutExercise:
    return WorkoutExercise(
        exercise_name=name,
        category=ExerciseCategory.STRENGTH,
        sets=[WorkoutSet(reps=reps, weight_kg=weight) for reps, weight in sets],
    )


def _cardio(name: str, minutes: int) -> WorkoutExercise:
    return WorkoutExercise(
        exercise_name=name, category=ExerciseCategory.CARDIO, duration_minutes=minutes
    )


def _workout(day: date, *exercises: WorkoutExercise) -> WorkoutLog:
    return WorkoutLog(
        workout_log_id=uuid4(),
        user_id=uuid4(),
        performed_at=datetime(day.year, day.month, day.day, tzinfo=UTC),
        exercises=list(exercises),
    )


def _day_of(w: WorkoutLog) -> date:
    return w.performed_at.date()


def test_strength_max_weight_takes_daily_max_and_skips_bodyweight_sets() -> None:
    logs = [
        _workout(_D1, _strength("スクワット", (10, 60.0), (8, 70.0)), _strength("懸垂", (8, None))),
        _workout(_D3, _strength("スクワット", (5, 80.0))),
        _workout(_D3, _cardio("ランニング", 30)),
    ]

    result = strength_max_weight_by_exercise(logs, _day_of, [_D1, _D2, _D3])

    assert result == {"スクワット": [70.0, None, 80.0]}


def test_strength_max_weight_keeps_top_n_by_recorded_days() -> None:
    logs = [
        _workout(_D1, _strength("A", (1, 10.0)), _strength("B", (1, 10.0))),
        _workout(_D2, _strength("B", (1, 10.0)), _strength("C", (1, 10.0))),
        _workout(_D3, _strength("B", (1, 10.0)), _strength("C", (1, 10.0))),
    ]

    result = strength_max_weight_by_exercise(logs, _day_of, [_D1, _D2, _D3], top_n=2)

    assert list(result) == ["B", "C"]


def test_cardio_minutes_by_exercise_orders_by_total_minutes() -> None:
    logs = [
        _workout(_D1, _cardio("散歩", 20), _cardio("ランニング", 30)),
        _workout(_D2, _cardio("ランニング", 40), _strength("スクワット", (10, 60.0))),
        _workout(date(2026, 5, 1), _cardio("サイクリング", 90)),
    ]

    result = cardio_minutes_by_exercise(logs, _day_of, [_D1, _D2])

    assert result == {"ランニング": [30.0, 40.0], "散歩": [20.0, 0.0]}
