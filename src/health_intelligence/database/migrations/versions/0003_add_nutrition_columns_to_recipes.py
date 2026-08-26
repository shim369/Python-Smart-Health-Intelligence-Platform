"""add nutrition columns to recipes

recipesテーブルにtotal_calories/protein_g/fat_g/carbohydrate_g
(いずれもnullable)を追加する。既存レシピはNoneのままとなる
(AI生成時のみ栄養情報を推定して埋める仕様のため)。

Revision ID: 0003
Revises: 0002
Create Date: (レシピ表示改善に伴い追加)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = ["total_calories", "protein_g", "fat_g", "carbohydrate_g"]


def upgrade() -> None:
    for column in _COLUMNS:
        op.add_column("recipes", sa.Column(column, sa.Float(), nullable=True))


def downgrade() -> None:
    for column in _COLUMNS:
        op.drop_column("recipes", column)
