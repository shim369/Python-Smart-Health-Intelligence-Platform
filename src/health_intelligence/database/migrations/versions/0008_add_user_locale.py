"""add users.locale

UI表示言語(日本語/英語)をユーザーごとに永続化するため、usersテーブルに
localeカラムを追加する。既存ユーザーは全員"ja"扱いとする。

Revision ID: 0008
Revises: 0007
Create Date: (日英切り替え機能追加に伴い追加)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("locale", sa.String(), nullable=False, server_default="ja"))


def downgrade() -> None:
    op.drop_column("users", "locale")
