"""MealService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.domain.models import MealLog
from health_intelligence.repositories.unit_of_work import UnitOfWork


class MealService:
    """MealLogに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def record_meal_log(self, meal_log: MealLog) -> None:
        with self._uow_factory() as uow:
            uow.meal_logs.add(meal_log)
            uow.commit()

    def list_meal_logs(self, user_id: UUID) -> list[MealLog]:
        with self._uow_factory() as uow:
            return uow.meal_logs.list_by_user(user_id)

    def get_meal_log(self, user_id: UUID, meal_log_id: UUID) -> MealLog | None:
        with self._uow_factory() as uow:
            return uow.meal_logs.get_by_id(user_id, meal_log_id)

    def update_meal_log(self, meal_log: MealLog) -> None:
        with self._uow_factory() as uow:
            uow.meal_logs.update(meal_log)
            uow.commit()

    def delete_meal_log(self, user_id: UUID, meal_log_id: UUID) -> None:
        with self._uow_factory() as uow:
            uow.meal_logs.delete(user_id, meal_log_id)
            uow.commit()
