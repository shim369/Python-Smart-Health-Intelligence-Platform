"""SQLAlchemy ORM Model定義。

architecture.md Section 14 Domain / ORM Separation:
Domain ModelとORM Modelは分離する。ここではテーブル構造・型・制約
(ForeignKey/Index等)を表現し、Domain固有のビジネスルールは持たない。
Domain Modelへの変換は`repositories/sqlalchemy/`内のmapper関数で行う。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserCredentialORM(Base):
    """Userのパスワードハッシュ。Userと1対1で、user_idを主キー兼外部キーとする。"""

    __tablename__ = "user_credentials"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    password_hash: Mapped[str]


class HealthLogORM(Base):
    __tablename__ = "health_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    condition_score: Mapped[int | None]
    morning_condition: Mapped[int | None]
    evening_condition: Mapped[int | None]
    mental_score: Mapped[int | None]
    fatigue_score: Mapped[int | None]
    stress_score: Mapped[int | None]
    symptoms: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    memo: Mapped[str | None] = mapped_column(Text)


class LearningLogORM(Base):
    __tablename__ = "learning_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    category: Mapped[str]
    location: Mapped[str | None]
    content: Mapped[str | None] = mapped_column(Text)
    breakdown: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    duration_minutes: Mapped[int | None]
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    notes: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)


class MealLogORM(Base):
    __tablename__ = "meal_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    consumed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    meal_type: Mapped[str]
    calories: Mapped[float]
    protein_g: Mapped[float]
    fat_g: Mapped[float]
    carbohydrate_g: Mapped[float]
    memo: Mapped[str | None] = mapped_column(Text)


class WorkoutLogORM(Base):
    """運動セッション。architecture.md/requirements.mdの3階層構造
    (セッション/種目/セット)に対応する。"""

    __tablename__ = "workout_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    calories_burned: Mapped[float | None]
    memo: Mapped[str | None] = mapped_column(Text)

    exercises: Mapped[list[WorkoutExerciseORM]] = relationship(
        back_populates="workout_log",
        cascade="all, delete-orphan",
        order_by="WorkoutExerciseORM.order_index",
    )


class WorkoutExerciseORM(Base):
    __tablename__ = "workout_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    workout_log_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workout_logs.id"), index=True)
    order_index: Mapped[int]
    exercise_name: Mapped[str]
    category: Mapped[str]
    duration_minutes: Mapped[int | None]

    workout_log: Mapped[WorkoutLogORM] = relationship(back_populates="exercises")
    sets: Mapped[list[WorkoutSetORM]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        order_by="WorkoutSetORM.order_index",
    )


class WorkoutSetORM(Base):
    __tablename__ = "workout_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    workout_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_exercises.id"), index=True
    )
    order_index: Mapped[int]
    reps: Mapped[int]
    weight_kg: Mapped[float | None]

    exercise: Mapped[WorkoutExerciseORM] = relationship(back_populates="sets")


class SleepLogORM(Base):
    __tablename__ = "sleep_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    bedtime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    wake_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quality: Mapped[str | None]


class WeightLogORM(Base):
    __tablename__ = "weight_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    weight_kg: Mapped[float]


class IngredientORM(Base):
    """食材マスタ。共通データのためuser_idを持たない。"""

    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str]
    calories_per_100g: Mapped[float | None]
    protein_per_100g: Mapped[float | None]
    fat_per_100g: Mapped[float | None]
    carbohydrate_per_100g: Mapped[float | None]


class RecipeORM(Base):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str]
    instructions: Mapped[str] = mapped_column(Text)
    source: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_calories: Mapped[float | None]
    protein_g: Mapped[float | None]
    fat_g: Mapped[float | None]
    carbohydrate_g: Mapped[float | None]

    ingredients: Mapped[list[RecipeIngredientORM]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
    )


class RecipeIngredientORM(Base):
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id"), primary_key=True)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingredients.id"), primary_key=True)
    amount: Mapped[float]
    unit: Mapped[str]

    recipe: Mapped[RecipeORM] = relationship(back_populates="ingredients")
    ingredient: Mapped[IngredientORM] = relationship()


class GoalORM(Base):
    """長期目標。daily-journal-design.md 3章参照。"""

    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str]
    category: Mapped[str]
    deadline: Mapped[date | None]
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TaskORM(Base):
    """Goal配下、または単発の関連タスク。daily-journal-design.md 3章参照。"""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("goals.id", ondelete="SET NULL"), index=True
    )
    category: Mapped[str]
    title: Mapped[str]
    log_type: Mapped[str]
    unit: Mapped[str | None]
    is_archived: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DailyPlanItemORM(Base):
    """「今日」ページP(計画)で選んだTask。daily-journal-design.md 3.4節参照。"""

    __tablename__ = "daily_plan_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "journal_date", "task_id", name="uq_daily_plan_items_user_date_task"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    journal_date: Mapped[date] = mapped_column(index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"), index=True)


class DailyTaskLogORM(Base):
    """「今日」ページD(実績)、log_type=COUNT_AND_DURATIONのTaskの実績。
    daily-journal-design.md 3.4節参照。"""

    __tablename__ = "daily_task_logs"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "journal_date", "task_id", name="uq_daily_task_logs_user_date_task"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    journal_date: Mapped[date] = mapped_column(index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    quantity: Mapped[float | None]
    duration_minutes: Mapped[int | None]
    memo: Mapped[str | None] = mapped_column(Text)


class DailyJournalORM(Base):
    """「今日」ページのP/C/A項目と家計の入口。daily-journal-design.md 8章参照。"""

    __tablename__ = "daily_journals"
    __table_args__ = (
        UniqueConstraint("user_id", "journal_date", name="uq_daily_journals_user_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    journal_date: Mapped[date]
    diet_policy_note: Mapped[str | None] = mapped_column(Text)
    wake_target_time: Mapped[time | None]
    sleep_target_time: Mapped[time | None]
    shopping_memo: Mapped[str | None] = mapped_column(Text)
    food_expense_yen: Mapped[int | None]
    work_hours: Mapped[float | None]
    reflection_memo: Mapped[str | None] = mapped_column(Text)
    improvement_point: Mapped[str | None] = mapped_column(Text)
    cooking_shopping_note: Mapped[str | None] = mapped_column(Text)
    study_prep_note: Mapped[str | None] = mapped_column(Text)
