"""add health_log five-axis condition fields

requirements.md 4.2節: HealthLogの体調を単一のcondition_score
から5軸(朝/夜の体調・メンタル・疲労・ストレス)へ拡張する。既存の
condition_score(総合スコア)は互換性のため残し、置き換えない。

Revision ID: 0005
Revises: 0004
Create Date: (Daily Journal機能追加に伴い追加)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_COLUMNS = (
    "morning_condition",
    "evening_condition",
    "mental_score",
    "fatigue_score",
    "stress_score",
)


def upgrade() -> None:
    for column_name in _NEW_COLUMNS:
        op.add_column("health_logs", sa.Column(column_name, sa.Integer(), nullable=True))


def downgrade() -> None:
    for column_name in reversed(_NEW_COLUMNS):
        op.drop_column("health_logs", column_name)
