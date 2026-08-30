"""drop daily_journals.work_hours

WORKカテゴリの「その日の総勤務時間」は家計タブから不要と判断されたため、
0006で追加したwork_hoursカラムを削除する。

Revision ID: 0007
Revises: 0006
Create Date: (家計タブ見直しに伴い追加)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("daily_journals", "work_hours")


def downgrade() -> None:
    op.add_column("daily_journals", sa.Column("work_hours", sa.Float(), nullable=True))
