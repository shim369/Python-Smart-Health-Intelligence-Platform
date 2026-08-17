"""initial schema

database/schema.py のORM Model一式に対応する初期テーブル群を作成する。
DATABASE_URL(Neon等)に接続できる環境がまだ無いため、
`alembic revision --autogenerate` の代わりに手動で作成した。
接続可能な環境が整ったら、このMigrationを適用した上で
`alembic revision --autogenerate -m "check drift"` を実行し、
schema.pyとの差分が無いことを確認することを推奨する。

Revision ID: 0001
Revises:
Create Date: (Day 1)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "health_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("condition_score", sa.Integer(), nullable=True),
        sa.Column(
            "symptoms",
            sa.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("memo", sa.Text(), nullable=True),
    )
    op.create_index("ix_health_logs_user_id", "health_logs", ["user_id"])

    op.create_table(
        "meal_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("consumed_at", sa.DateTime(), nullable=False),
        sa.Column("meal_type", sa.String(), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False),
        sa.Column("fat_g", sa.Float(), nullable=False),
        sa.Column("carbohydrate_g", sa.Float(), nullable=False),
        sa.Column("memo", sa.Text(), nullable=True),
    )
    op.create_index("ix_meal_logs_user_id", "meal_logs", ["user_id"])

    op.create_table(
        "workout_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("performed_at", sa.DateTime(), nullable=False),
        sa.Column("calories_burned", sa.Float(), nullable=True),
        sa.Column("memo", sa.Text(), nullable=True),
    )
    op.create_index("ix_workout_logs_user_id", "workout_logs", ["user_id"])

    op.create_table(
        "workout_exercises",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workout_log_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workout_logs.id"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("exercise_name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_workout_exercises_workout_log_id",
        "workout_exercises",
        ["workout_log_id"],
    )

    op.create_table(
        "workout_sets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workout_exercise_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workout_exercises.id"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
    )
    op.create_index(
        "ix_workout_sets_workout_exercise_id",
        "workout_sets",
        ["workout_exercise_id"],
    )

    op.create_table(
        "sleep_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("bedtime", sa.DateTime(), nullable=False),
        sa.Column("wake_time", sa.DateTime(), nullable=False),
        sa.Column("quality", sa.String(), nullable=True),
    )
    op.create_index("ix_sleep_logs_user_id", "sleep_logs", ["user_id"])

    op.create_table(
        "weight_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
    )
    op.create_index("ix_weight_logs_user_id", "weight_logs", ["user_id"])

    op.create_table(
        "ingredients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("calories_per_100g", sa.Float(), nullable=True),
        sa.Column("protein_per_100g", sa.Float(), nullable=True),
        sa.Column("fat_per_100g", sa.Float(), nullable=True),
        sa.Column("carbohydrate_per_100g", sa.Float(), nullable=True),
    )

    op.create_table(
        "recipes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_recipes_user_id", "recipes", ["user_id"])

    op.create_table(
        "recipe_ingredients",
        sa.Column(
            "recipe_id",
            UUID(as_uuid=True),
            sa.ForeignKey("recipes.id"),
            primary_key=True,
        ),
        sa.Column(
            "ingredient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ingredients.id"),
            primary_key=True,
        ),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("recipe_ingredients")
    op.drop_table("recipes")
    op.drop_table("ingredients")
    op.drop_table("weight_logs")
    op.drop_table("sleep_logs")
    op.drop_table("workout_sets")
    op.drop_table("workout_exercises")
    op.drop_table("workout_logs")
    op.drop_table("meal_logs")
    op.drop_table("health_logs")
    op.drop_table("users")
