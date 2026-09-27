"""compute_daily_featuresの日付境界(JST)のテスト。"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from health_intelligence.domain.enums import MealType
from health_intelligence.domain.models import MealLog
from health_intelligence.features import compute_daily_features
from health_intelligence.local_time import local_date_of


def _calories_on(target_date: date, meal: MealLog) -> float | None:
    return compute_daily_features(
        target_date, meal_logs=[meal], sleep_logs=[], workout_logs=[], weight_logs=[]
    ).calories


def test_morning_log_counts_toward_jst_date() -> None:
    """UTCでは前日でも、JSTで当日の朝の記録は当日の集計に含まれる。"""
    # 2026-06-01 23:30 UTC = 2026-06-02 08:30 JST
    breakfast = MealLog(
        meal_log_id=uuid4(),
        user_id=uuid4(),
        consumed_at=datetime(2026, 6, 1, 23, 30, tzinfo=UTC),
        meal_type=MealType.BREAKFAST,
        calories=500.0,
        protein_g=20.0,
        fat_g=10.0,
        carbohydrate_g=60.0,
    )

    assert _calories_on(date(2026, 6, 2), breakfast) == 500.0
    assert _calories_on(date(2026, 6, 1), breakfast) is None


def test_local_date_of_converts_utc_to_jst_date() -> None:
    assert local_date_of(datetime(2026, 6, 1, 14, 59, tzinfo=UTC)) == date(2026, 6, 1)
    assert local_date_of(datetime(2026, 6, 1, 15, 0, tzinfo=UTC)) == date(2026, 6, 2)
