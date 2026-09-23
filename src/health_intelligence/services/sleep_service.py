"""SleepService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.domain.models import SleepLog
from health_intelligence.repositories.unit_of_work import UnitOfWork


class SleepService:
    """SleepLogに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def record_sleep_log(self, sleep_log: SleepLog) -> None:
        with self._uow_factory() as uow:
            uow.sleep_logs.add(sleep_log)
            uow.commit()

    def record_sleep_logs(self, sleep_logs: list[SleepLog]) -> None:
        """複数件を1トランザクションでまとめて記録する(CSV一括インポート用)。

        1件ずつ`record_sleep_log`を呼ぶと件数分のDB往復・commitが発生し、
        リモートDBでは件数に比例して著しく遅くなるため。
        """
        with self._uow_factory() as uow:
            for sleep_log in sleep_logs:
                uow.sleep_logs.add(sleep_log)
            uow.commit()

    def list_sleep_logs(self, user_id: UUID) -> list[SleepLog]:
        with self._uow_factory() as uow:
            return uow.sleep_logs.list_by_user(user_id)

    def get_sleep_log(self, user_id: UUID, sleep_log_id: UUID) -> SleepLog | None:
        with self._uow_factory() as uow:
            return uow.sleep_logs.get_by_id(user_id, sleep_log_id)

    def update_sleep_log(self, sleep_log: SleepLog) -> None:
        with self._uow_factory() as uow:
            uow.sleep_logs.update(sleep_log)
            uow.commit()

    def delete_sleep_log(self, user_id: UUID, sleep_log_id: UUID) -> None:
        with self._uow_factory() as uow:
            uow.sleep_logs.delete(user_id, sleep_log_id)
            uow.commit()
