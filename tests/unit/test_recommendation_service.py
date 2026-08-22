"""RecommendationServiceのテスト。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from health_intelligence.domain.enums import MealType, SleepQuality
from health_intelligence.domain.models import MealLog, SleepLog, WeightLog
from health_intelligence.services.recommendation_service import RecommendationService


def _make_service(
    make_fake_uow_factory,
    fake_list_repository_factory,
    *,
    meal_logs=(),
    sleep_logs=(),
    workout_logs=(),
    weight_logs=(),
) -> RecommendationService:
    uow_factory = make_fake_uow_factory(
        meal_logs=fake_list_repository_factory(list(meal_logs)),
        sleep_logs=fake_list_repository_factory(list(sleep_logs)),
        workout_logs=fake_list_repository_factory(list(workout_logs)),
        weight_logs=fake_list_repository_factory(list(weight_logs)),
    )
    return RecommendationService(uow_factory)


def test_workout_deficiency_is_top_priority_when_others_are_healthy(
    make_fake_uow_factory, fake_list_repository_factory
) -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    meal_logs, sleep_logs, weight_logs = [], [], []

    for i in range(7):
        d = now - timedelta(days=i)
        meal_logs.append(
            MealLog(
                meal_log_id=uuid4(),
                user_id=user_id,
                consumed_at=d,
                meal_type=MealType.DINNER,
                calories=700,
                protein_g=30,
                fat_g=20,
                carbohydrate_g=90,
            )
        )
        sleep_logs.append(
            SleepLog(
                sleep_log_id=uuid4(),
                user_id=user_id,
                bedtime=d.replace(hour=23),
                wake_time=(d + timedelta(days=1)).replace(hour=6),
                quality=SleepQuality.GOOD,
            )
        )
        weight_logs.append(
            WeightLog(
                weight_log_id=uuid4(),
                user_id=user_id,
                recorded_at=d,
                weight_kg=70.0,
            )
        )

    service = _make_service(
        make_fake_uow_factory,
        fake_list_repository_factory,
        meal_logs=meal_logs,
        sleep_logs=sleep_logs,
        weight_logs=weight_logs,
    )

    report = service.get_recommendations(user_id)

    assert report.recommendations
    assert report.recommendations[0].domain == "workout"


def test_empty_logs_return_neutral_scores(
    make_fake_uow_factory, fake_list_repository_factory
) -> None:
    service = _make_service(make_fake_uow_factory, fake_list_repository_factory)

    report = service.get_recommendations(uuid4())

    assert report.health_score.overall_score == pytest.approx(50.0)
