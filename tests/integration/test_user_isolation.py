"""user_idによるデータ分離を検証するIntegration Test。

実際のPostgreSQL(Neon等)への接続を必要とする。schema.pyが
PostgreSQL固有の型(`postgresql.UUID` / `postgresql.ARRAY`)を
使っているため、SQLiteのような軽量DBでは代替できない。

ローカルで実行する場合は、テスト用DBを指すDATABASE_URLを設定し、
`alembic upgrade head`でスキーマを適用してから実行すること。
DATABASE_URLが未設定の場合は自動的にスキップする。

CI(GitHub Actions)で実行する場合は、ジョブにPostgresサービス
コンテナを追加することを想定している(Phase 9で設定予定)。
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    DATABASE_URL is None,
    reason="DATABASE_URL が未設定のためIntegration Testをスキップ",
)


@pytest.fixture
def uow_factory():
    from health_intelligence.repositories.sqlalchemy import build_uow_factory

    return build_uow_factory()


def test_user_cannot_see_other_users_meal_logs(uow_factory) -> None:
    from health_intelligence.domain.enums import MealType
    from health_intelligence.domain.models import MealLog, User

    user_a_id, user_b_id = uuid4(), uuid4()

    with uow_factory() as uow:
        uow.users.add(
            User(
                user_id=user_a_id,
                email=f"{user_a_id}@example.com",
                display_name="User A",
                created_at=datetime.now(UTC),
            )
        )
        uow.users.add(
            User(
                user_id=user_b_id,
                email=f"{user_b_id}@example.com",
                display_name="User B",
                created_at=datetime.now(UTC),
            )
        )
        uow.meal_logs.add(
            MealLog(
                meal_log_id=uuid4(),
                user_id=user_a_id,
                consumed_at=datetime.now(UTC),
                meal_type=MealType.LUNCH,
                calories=500,
                protein_g=20,
                fat_g=10,
                carbohydrate_g=60,
            )
        )
        uow.commit()

    with uow_factory() as uow:
        user_a_logs = uow.meal_logs.list_by_user(user_a_id)
        user_b_logs = uow.meal_logs.list_by_user(user_b_id)

    assert len(user_a_logs) == 1
    assert len(user_b_logs) == 0
