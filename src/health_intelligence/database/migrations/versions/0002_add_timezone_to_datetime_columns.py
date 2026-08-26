"""add timezone to datetime columns

0001_initial.pyでは全てのdatetime列がPostgreSQLの
`TIMESTAMP WITHOUT TIME ZONE`(タイムゾーン情報を持たない型)として
作成されていた。一方、Domain Model/アプリケーションコードは一貫して
`datetime.now(UTC)`(タイムゾーン付き=aware)を使っているため、
「aware(recent_since等)とnaive(DBから読み込んだ値)を比較できない」
というTypeErrorが実行時に発生していた。

このMigrationは、既存データを失わずに全datetime列を
`TIMESTAMP WITH TIME ZONE`(TIMESTAMPTZ)へ変換する。

`USING col AT TIME ZONE 'UTC'`は、「既存の(タイムゾーン情報を持たない)
値はUTCの時刻として書き込まれていた」という前提のもとで、その情報を
失わずにタイムゾーン付きの型へ変換する。アプリケーションコードは
書き込み時に常に`datetime.now(UTC)`を使っていたため、この前提は正しい。

Revision ID: 0002
Revises: 0001
Create Date: (Day 6以降の実機検証中に発見・追加)
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TIMEZONE_COLUMNS: list[tuple[str, str]] = [
    ("users", "created_at"),
    ("health_logs", "recorded_at"),
    ("meal_logs", "consumed_at"),
    ("workout_logs", "performed_at"),
    ("sleep_logs", "bedtime"),
    ("sleep_logs", "wake_time"),
    ("weight_logs", "recorded_at"),
    ("recipes", "created_at"),
]


def upgrade() -> None:
    for table, column in _TIMEZONE_COLUMNS:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} "
            f"TYPE TIMESTAMPTZ USING {column} AT TIME ZONE 'UTC'"
        )


def downgrade() -> None:
    for table, column in _TIMEZONE_COLUMNS:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} "
            f"TYPE TIMESTAMP USING {column} AT TIME ZONE 'UTC'"
        )
