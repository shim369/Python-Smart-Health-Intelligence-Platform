"""SqlAlchemyによる`MealLogRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import MealLogORM
from health_intelligence.domain.enums import MealType
from health_intelligence.domain.models import MealLog


def _to_domain(orm: MealLogORM) -> MealLog:
    return MealLog(
        meal_log_id=orm.id,
        user_id=orm.user_id,
        consumed_at=orm.consumed_at,
        meal_type=MealType(orm.meal_type),
        calories=orm.calories,
        protein_g=orm.protein_g,
        fat_g=orm.fat_g,
        carbohydrate_g=orm.carbohydrate_g,
        memo=orm.memo,
    )


def _to_orm(meal_log: MealLog) -> MealLogORM:
    return MealLogORM(
        id=meal_log.meal_log_id,
        user_id=meal_log.user_id,
        consumed_at=meal_log.consumed_at,
        meal_type=meal_log.meal_type.value,
        calories=meal_log.calories,
        protein_g=meal_log.protein_g,
        fat_g=meal_log.fat_g,
        carbohydrate_g=meal_log.carbohydrate_g,
        memo=meal_log.memo,
    )


class SqlAlchemyMealLogRepository:
    """`repositories.protocols.MealLogRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, meal_log_id: UUID) -> MealLog | None:
        stmt = select(MealLogORM).where(
            MealLogORM.id == meal_log_id, MealLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(self, user_id: UUID) -> list[MealLog]:
        stmt = select(MealLogORM).where(MealLogORM.user_id == user_id)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, meal_log: MealLog) -> None:
        self._session.add(_to_orm(meal_log))

    def delete(self, user_id: UUID, meal_log_id: UUID) -> None:
        stmt = select(MealLogORM).where(
            MealLogORM.id == meal_log_id, MealLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
