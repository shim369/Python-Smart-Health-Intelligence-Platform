"""add goal/task/daily_plan_item/daily_task_log/daily_journal tables

daily-journal-design.md 3章・8章: 学習・PF開発・仕事・食事方針・運動目標・
睡眠目標・キャリア・生活全般をGoal(長期目標)/Task(関連タスク)の選択式で
記録するための新規ドメインと、P/C/A + 家計の入口を持つDailyJournalを
追加する。

作成順はFK依存のため goals -> tasks -> daily_plan_items ->
daily_task_logs -> daily_journals。

Revision ID: 0006
Revises: 0005
Create Date: (Daily Journal機能追加に伴い追加)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="in_progress"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])

    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "goal_id",
            UUID(as_uuid=True),
            sa.ForeignKey("goals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("log_type", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.create_index("ix_tasks_goal_id", "tasks", ["goal_id"])

    op.create_table(
        "daily_plan_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("journal_date", sa.Date(), nullable=False),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id"), nullable=False),
    )
    op.create_index("ix_daily_plan_items_user_id", "daily_plan_items", ["user_id"])
    op.create_index("ix_daily_plan_items_journal_date", "daily_plan_items", ["journal_date"])
    op.create_index("ix_daily_plan_items_task_id", "daily_plan_items", ["task_id"])
    op.create_unique_constraint(
        "uq_daily_plan_items_user_date_task",
        "daily_plan_items",
        ["user_id", "journal_date", "task_id"],
    )

    op.create_table(
        "daily_task_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("journal_date", sa.Date(), nullable=False),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("memo", sa.Text(), nullable=True),
    )
    op.create_index("ix_daily_task_logs_user_id", "daily_task_logs", ["user_id"])
    op.create_index("ix_daily_task_logs_journal_date", "daily_task_logs", ["journal_date"])
    op.create_index("ix_daily_task_logs_task_id", "daily_task_logs", ["task_id"])
    op.create_unique_constraint(
        "uq_daily_task_logs_user_date_task",
        "daily_task_logs",
        ["user_id", "journal_date", "task_id"],
    )

    op.create_table(
        "daily_journals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("journal_date", sa.Date(), nullable=False),
        sa.Column("diet_policy_note", sa.Text(), nullable=True),
        sa.Column("wake_target_time", sa.Time(), nullable=True),
        sa.Column("sleep_target_time", sa.Time(), nullable=True),
        sa.Column("shopping_memo", sa.Text(), nullable=True),
        sa.Column("food_expense_yen", sa.Integer(), nullable=True),
        sa.Column("work_hours", sa.Float(), nullable=True),
        sa.Column("reflection_memo", sa.Text(), nullable=True),
        sa.Column("improvement_point", sa.Text(), nullable=True),
        sa.Column("cooking_shopping_note", sa.Text(), nullable=True),
        sa.Column("study_prep_note", sa.Text(), nullable=True),
    )
    op.create_index("ix_daily_journals_user_id", "daily_journals", ["user_id"])
    op.create_unique_constraint(
        "uq_daily_journals_user_date", "daily_journals", ["user_id", "journal_date"]
    )


def downgrade() -> None:
    op.drop_table("daily_journals")

    op.drop_index("ix_daily_task_logs_task_id", table_name="daily_task_logs")
    op.drop_index("ix_daily_task_logs_journal_date", table_name="daily_task_logs")
    op.drop_index("ix_daily_task_logs_user_id", table_name="daily_task_logs")
    op.drop_table("daily_task_logs")

    op.drop_index("ix_daily_plan_items_task_id", table_name="daily_plan_items")
    op.drop_index("ix_daily_plan_items_journal_date", table_name="daily_plan_items")
    op.drop_index("ix_daily_plan_items_user_id", table_name="daily_plan_items")
    op.drop_table("daily_plan_items")

    op.drop_index("ix_tasks_goal_id", table_name="tasks")
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_table("goals")
