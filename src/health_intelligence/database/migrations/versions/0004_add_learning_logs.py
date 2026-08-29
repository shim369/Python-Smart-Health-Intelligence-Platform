"""add learning_logs table

学習ログ(試験勉強・PF開発・調べ物・キャリア戦略設計)を記録する
learning_logsテーブルを追加する。health_logsと同様、breakdown/
keywords/notesはARRAY(Text)で保持する。

Revision ID: 0004
Revises: 0003
Create Date: (学習ログ機能追加に伴い追加)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "breakdown",
            sa.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "keywords",
            sa.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "notes",
            sa.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.create_index("ix_learning_logs_user_id", "learning_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_learning_logs_user_id", table_name="learning_logs")
    op.drop_table("learning_logs")
