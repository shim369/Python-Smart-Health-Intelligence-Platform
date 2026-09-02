"""drop user_credentials

認証方式をEmail/PasswordからGoogle OAuth(OIDC)へ移行するため、パスワード
ハッシュを保持していたuser_credentialsテーブルを削除する
(docs/auth-migration-design.md 4.8)。

Revision ID: 0009
Revises: 0008
Create Date: (Google OAuth移行に伴い追加)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("user_credentials")


def downgrade() -> None:
    op.create_table(
        "user_credentials",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("password_hash", sa.String(), nullable=False),
    )
