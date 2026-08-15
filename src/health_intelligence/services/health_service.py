"""HealthService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.domain.models import HealthLog
from health_intelligence.repositories.unit_of_work import UnitOfWork


class HealthService:
    """HealthLogに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def record_health_log(self, health_log: HealthLog) -> None:
        with self._uow_factory() as uow:
            uow.health_logs.add(health_log)
            uow.commit()

    def list_health_logs(self, user_id: UUID) -> list[HealthLog]:
        with self._uow_factory() as uow:
            return uow.health_logs.list_by_user(user_id)

    def delete_health_log(self, user_id: UUID, health_log_id: UUID) -> None:
        with self._uow_factory() as uow:
            uow.health_logs.delete(user_id, health_log_id)
            uow.commit()
