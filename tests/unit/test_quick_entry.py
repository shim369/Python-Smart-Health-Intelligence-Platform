"""`app/components/quick_entry`のテスト。

app/はsrc/health_intelligenceとは別のトップレベルディレクトリのため、
importできるようsys.pathへ明示的に追加する(test_workout_form.pyと
同じパターン)。
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.quick_entry import (  # noqa: E402
    exercise_template_to_entry,
    frequent_exercise_templates,
    frequent_learning_keywords,
    frequent_meal_templates,
    most_recent_learning_log,
    most_recent_meal,
)

from health_intelligence.domain.enums import (  # noqa: E402
    ExerciseCategory,
    LearningCategory,
    MealType,
)
from health_intelligence.domain.models import (  # noqa: E402
    LearningLog,
    MealLog,
    WorkoutExercise,
    WorkoutLog,
    WorkoutSet,
)

_USER_ID = uuid4()


def _meal(
    *, consumed_at: datetime, memo: str | None, calories: float = 100.0
) -> MealLog:
    return MealLog(
        meal_log_id=uuid4(),
        user_id=_USER_ID,
        consumed_at=consumed_at,
        meal_type=MealType.BREAKFAST,
        calories=calories,
        protein_g=10.0,
        fat_g=5.0,
        carbohydrate_g=15.0,
        memo=memo,
    )


def test_most_recent_meal_returns_latest_by_consumed_at() -> None:
    older = _meal(consumed_at=datetime(2026, 6, 1, tzinfo=UTC), memo="A")
    newer = _meal(consumed_at=datetime(2026, 6, 2, tzinfo=UTC), memo="B")

    assert most_recent_meal([older, newer]) is newer
    assert most_recent_meal([]) is None


def _learning(
    *,
    started_at: datetime,
    category: LearningCategory = LearningCategory.EXAM_STUDY,
    keywords: list[str] | None = None,
) -> LearningLog:
    return LearningLog(
        learning_log_id=uuid4(),
        user_id=_USER_ID,
        started_at=started_at,
        category=category,
        keywords=keywords or [],
    )


def test_most_recent_learning_log_returns_latest_by_started_at() -> None:
    older = _learning(started_at=datetime(2026, 6, 1, tzinfo=UTC))
    newer = _learning(started_at=datetime(2026, 6, 2, tzinfo=UTC))

    assert most_recent_learning_log([older, newer]) is newer
    assert most_recent_learning_log([]) is None


def test_frequent_learning_keywords_ranks_by_usage_across_logs() -> None:
    logs = [
        _learning(
            started_at=datetime(2026, 6, 1, tzinfo=UTC),
            keywords=["Python", "SQL"],
        ),
        _learning(
            started_at=datetime(2026, 6, 2, tzinfo=UTC),
            category=LearningCategory.PORTFOLIO_DEV,
            keywords=["Python", "Docker"],
        ),
        _learning(
            started_at=datetime(2026, 6, 3, tzinfo=UTC),
            category=LearningCategory.RESEARCH,
            keywords=["Python"],
        ),
    ]

    templates = frequent_learning_keywords(logs)

    assert templates[0].keyword == "Python"
    assert templates[0].usage_count == 3
    assert {t.keyword for t in templates} == {"Python", "SQL", "Docker"}


def test_frequent_learning_keywords_respects_limit_and_ignores_no_keywords() -> None:
    logs = [
        _learning(started_at=datetime(2026, 6, 1, tzinfo=UTC), keywords=[]),
        *[
            _learning(started_at=datetime(2026, 6, i, tzinfo=UTC), keywords=[f"kw{i}"])
            for i in range(2, 8)
        ],
    ]

    templates = frequent_learning_keywords(logs, limit=3)

    assert len(templates) == 3


def test_frequent_meal_templates_ranks_by_usage_and_ignores_empty_memo() -> None:
    logs = [
        _meal(consumed_at=datetime(2026, 6, 1, tzinfo=UTC), memo="納豆ご飯"),
        _meal(consumed_at=datetime(2026, 6, 2, tzinfo=UTC), memo="納豆ご飯"),
        _meal(consumed_at=datetime(2026, 6, 3, tzinfo=UTC), memo="納豆ご飯"),
        _meal(consumed_at=datetime(2026, 6, 4, tzinfo=UTC), memo="サラダ"),
        _meal(consumed_at=datetime(2026, 6, 5, tzinfo=UTC), memo=None),
        _meal(consumed_at=datetime(2026, 6, 6, tzinfo=UTC), memo=""),
    ]

    templates = frequent_meal_templates(logs)

    assert [t.memo for t in templates] == ["納豆ご飯", "サラダ"]
    assert templates[0].usage_count == 3
    assert templates[1].usage_count == 1


def test_frequent_meal_templates_uses_latest_nutrition_values() -> None:
    logs = [
        _meal(
            consumed_at=datetime(2026, 6, 1, tzinfo=UTC), memo="鶏胸肉", calories=200
        ),
        _meal(
            consumed_at=datetime(2026, 6, 3, tzinfo=UTC), memo="鶏胸肉", calories=250
        ),
        _meal(
            consumed_at=datetime(2026, 6, 2, tzinfo=UTC), memo="鶏胸肉", calories=999
        ),
    ]

    templates = frequent_meal_templates(logs)

    assert templates[0].calories == 250


def test_frequent_meal_templates_respects_limit() -> None:
    logs = [
        _meal(consumed_at=datetime(2026, 6, i, tzinfo=UTC), memo=f"meal{i}")
        for i in range(1, 8)
    ]

    templates = frequent_meal_templates(logs, limit=3)

    assert len(templates) == 3


def _workout(*, performed_at: datetime, exercises: list[WorkoutExercise]) -> WorkoutLog:
    return WorkoutLog(
        workout_log_id=uuid4(),
        user_id=_USER_ID,
        performed_at=performed_at,
        exercises=exercises,
    )


def test_frequent_exercise_templates_ranks_by_usage() -> None:
    logs = [
        _workout(
            performed_at=datetime(2026, 6, 1, tzinfo=UTC),
            exercises=[
                WorkoutExercise(
                    exercise_name="レッグプレス",
                    category=ExerciseCategory.STRENGTH,
                    sets=[WorkoutSet(reps=10, weight_kg=70)],
                )
            ],
        ),
        _workout(
            performed_at=datetime(2026, 6, 3, tzinfo=UTC),
            exercises=[
                WorkoutExercise(
                    exercise_name="レッグプレス",
                    category=ExerciseCategory.STRENGTH,
                    sets=[WorkoutSet(reps=8, weight_kg=75)],
                ),
                WorkoutExercise(
                    exercise_name="有酸素運動",
                    category=ExerciseCategory.CARDIO,
                    duration_minutes=20,
                ),
            ],
        ),
    ]

    templates = frequent_exercise_templates(logs)

    assert templates[0].exercise_name == "レッグプレス"
    assert templates[0].usage_count == 2
    assert templates[0].last_reps == 8
    assert templates[0].last_weight_kg == 75
    assert templates[1].exercise_name == "有酸素運動"
    assert templates[1].last_duration_minutes == 20


def test_frequent_exercise_templates_respects_limit() -> None:
    logs = [
        _workout(
            performed_at=datetime(2026, 6, 1, tzinfo=UTC),
            exercises=[
                WorkoutExercise(
                    exercise_name=f"種目{i}",
                    category=ExerciseCategory.STRENGTH,
                    sets=[WorkoutSet(reps=10, weight_kg=50)],
                )
                for i in range(10)
            ],
        )
    ]

    templates = frequent_exercise_templates(logs, limit=4)

    assert len(templates) == 4


def test_exercise_template_to_entry_converts_strength_template() -> None:
    logs = [
        _workout(
            performed_at=datetime(2026, 6, 1, tzinfo=UTC),
            exercises=[
                WorkoutExercise(
                    exercise_name="ベンチプレス",
                    category=ExerciseCategory.STRENGTH,
                    sets=[WorkoutSet(reps=8, weight_kg=60)],
                )
            ],
        )
    ]

    template = frequent_exercise_templates(logs)[0]
    entry = exercise_template_to_entry(template)

    assert entry == {
        "exercise_name": "ベンチプレス",
        "category": "strength",
        "duration_minutes": None,
        "sets": [{"reps": 8, "weight_kg": 60}],
    }


def test_exercise_template_to_entry_converts_cardio_template() -> None:
    logs = [
        _workout(
            performed_at=datetime(2026, 6, 1, tzinfo=UTC),
            exercises=[
                WorkoutExercise(
                    exercise_name="ランニング",
                    category=ExerciseCategory.CARDIO,
                    duration_minutes=30,
                )
            ],
        )
    ]

    template = frequent_exercise_templates(logs)[0]
    entry = exercise_template_to_entry(template)

    assert entry == {
        "exercise_name": "ランニング",
        "category": "cardio",
        "duration_minutes": 30,
        "sets": [],
    }
