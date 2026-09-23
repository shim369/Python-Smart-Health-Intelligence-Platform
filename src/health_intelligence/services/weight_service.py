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

    def record_weight_logs(self, weight_logs: list[WeightLog]) -> None:
        """複数件を1トランザクションでまとめて記録する(CSV一括インポート用)。

        1件ずつ`record_weight_log`を呼ぶと件数分のDB往復・commitが発生し、
        リモートDBでは件数に比例して著しく遅くなるため。
        """
        with self._uow_factory() as uow:
            for weight_log in weight_logs:
                uow.weight_logs.add(weight_log)
            uow.commit()

    def list_weight_logs(self, user_id: UUID) -> list[WeightLog]:
        with self._uow_factory() as uow:
            return uow.weight_logs.list_by_user(user_id)

    def get_weight_log(self, user_id: UUID, weight_log_id: UUID) -> WeightLog | None:
        with self._uow_factory() as uow:
            return uow.weight_logs.get_by_id(user_id, weight_log_id)

    def update_weight_log(self, weight_log: WeightLog) -> None:
        with self._uow_factory() as uow:
            uow.weight_logs.update(weight_log)
            uow.commit()

    def delete_weight_log(self, user_id: UUID, weight_log_id: UUID) -> None:
        with self._uow_factory() as uow:
            uow.weight_logs.delete(user_id, weight_log_id)
            uow.commit()
