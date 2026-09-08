"""実データからのDailyFeatures構築(Weight領域)。

requirements.md 9.3.1の判定・`ml/run_weight_pipeline.py`でのML初回学習に
用いる実データを、DBから直接組み立てる。運用スクリプト専用の想定で、
Service層のProtocol/UnitOfWorkを経由せず`database.connection.session_scope`
を直接使う(tests/unit/test_migrations.pyと同様、通常のRepository経由の
アプリケーションコードとは異なる例外)。

このアプリはGoogle OAuthの`allowed_emails`により実質シングルユーザー
運用を前提としているため、複数ユーザーが存在する場合は
`weight_logs`が最も多いユーザー(＝主利用者とみなす)のデータのみを
対象とする。
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import UserORM
from health_intelligence.features.daily_features import (
    DailyFeatures,
    compute_daily_features,
)
from health_intelligence.ml.dataset import MIN_DAYS
from health_intelligence.repositories.sqlalchemy.meal_log_repository import (
    SqlAlchemyMealLogRepository,
)
from health_intelligence.repositories.sqlalchemy.sleep_log_repository import (
    SqlAlchemySleepLogRepository,
)
from health_intelligence.repositories.sqlalchemy.weight_log_repository import (
    SqlAlchemyWeightLogRepository,
)
from health_intelligence.repositories.sqlalchemy.workout_log_repository import (
    SqlAlchemyWorkoutLogRepository,
)


def load_real_daily_features(session: Session) -> list[DailyFeatures]:
    """DBに蓄積された実データからWeight領域用のDailyFeaturesを組み立てる。

    最初のログ記録日から最後のログ記録日までの暦日ごとに1件生成する
    (ログが存在しない日もその日の`DailyFeatures`として含め、欠損として
    扱う。dataset.check_data_qualityの欠損率計算に対応するため)。
    対象ユーザーが1人もいない、またはログが1件も無い場合は空リストを返す。
    """
    user_ids = session.scalars(select(UserORM.id)).all()
    if not user_ids:
        return []

    meal_repo = SqlAlchemyMealLogRepository(session)
    sleep_repo = SqlAlchemySleepLogRepository(session)
    workout_repo = SqlAlchemyWorkoutLogRepository(session)
    weight_repo = SqlAlchemyWeightLogRepository(session)

    target_user_id = max(user_ids, key=lambda uid: len(weight_repo.list_by_user(uid)))

    meal_logs = meal_repo.list_by_user(target_user_id)
    sleep_logs = sleep_repo.list_by_user(target_user_id)
    workout_logs = workout_repo.list_by_user(target_user_id)
    weight_logs = weight_repo.list_by_user(target_user_id)

    all_dates: set[date] = set()
    all_dates.update(m.consumed_at.date() for m in meal_logs)
    all_dates.update(s.wake_time.date() for s in sleep_logs)
    all_dates.update(w.performed_at.date() for w in workout_logs)
    all_dates.update(w.recorded_at.date() for w in weight_logs)
    if not all_dates:
        return []

    start, end = min(all_dates), max(all_dates)
    span_days = (end - start).days + 1
    return [
        compute_daily_features(
            start + timedelta(days=i),
            meal_logs=meal_logs,
            sleep_logs=sleep_logs,
            workout_logs=workout_logs,
            weight_logs=weight_logs,
        )
        for i in range(span_days)
    ]


def estimate_readiness_date(daily_features: list[DailyFeatures]) -> date | None:
    """MIN_DAYS(60暦日)到達の見込み日を概算する。

    先頭ログの記録日 + (MIN_DAYS - 1)日を返す。ログが1件も無い場合は
    起点が無く見込みを算出できないため`None`を返す。
    """
    if not daily_features:
        return None
    return daily_features[0].target_date + timedelta(days=MIN_DAYS - 1)
