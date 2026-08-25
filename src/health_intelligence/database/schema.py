"""SQLAlchemy ORM Model定義。

architecture.md Section 14 Domain / ORM Separation:
Domain ModelとORM Modelは分離する。ここではテーブル構造・型・制約
(ForeignKey/Index等)を表現し、Domain固有のビジネスルールは持たない。
Domain Modelへの変換は`repositories/sqlalchemy/`内のmapper関数で行う。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
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

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), primary_key=True
    )
    password_hash: Mapped[str]


class HealthLogORM(Base):
    __tablename__ = "health_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    condition_score: Mapped[int | None]
    symptoms: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    memo: Mapped[str | None] = mapped_column(Text)


class MealLogORM(Base):
    __tablename__ = "meal_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
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
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
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
    workout_log_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_logs.id"), index=True
    )
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
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    bedtime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    wake_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quality: Mapped[str | None]


class WeightLogORM(Base):
    __tablename__ = "weight_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
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
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    title: Mapped[str]
    instructions: Mapped[str] = mapped_column(Text)
    source: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RecipeIngredientORM(Base):
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id"), primary_key=True
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id"), primary_key=True
    )
    amount: Mapped[float]
    unit: Mapped[str]
