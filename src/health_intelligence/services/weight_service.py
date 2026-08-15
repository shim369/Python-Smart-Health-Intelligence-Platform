"""WeightService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.domain.models import WeightLog
from health_intelligence.repositories.unit_of_work import UnitOfWork


class WeightService:
    """WeightLogに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def record_weight_log(self, weight_log: WeightLog) -> None:
        with self._uow_factory() as uow:
            uow.weight_logs.add(weight_log)
            uow.commit()

    def list_weight_logs(self, user_id: UUID) -> list[WeightLog]:
        with self._uow_factory() as uow:
            return uow.weight_logs.list_by_user(user_id)

    def delete_weight_log(self, user_id: UUID, weight_log_id: UUID) -> None:
        with self._uow_factory() as uow:
            uow.weight_logs.delete(user_id, weight_log_id)
            uow.commit()
