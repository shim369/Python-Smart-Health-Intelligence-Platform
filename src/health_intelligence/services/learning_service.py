"""LearningService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.domain.models import LearningLog
from health_intelligence.repositories.unit_of_work import UnitOfWork


class LearningService:
    """LearningLogに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def record_learning_log(self, learning_log: LearningLog) -> None:
        with self._uow_factory() as uow:
            uow.learning_logs.add(learning_log)
            uow.commit()

    def record_learning_logs(self, learning_logs: list[LearningLog]) -> None:
        """複数件を1トランザクションでまとめて記録する(CSV一括インポート用)。

        1件ずつ`record_learning_log`を呼ぶと件数分のDB往復・commitが発生し、
        リモートDBでは件数に比例して著しく遅くなるため。
        """
        with self._uow_factory() as uow:
            for learning_log in learning_logs:
                uow.learning_logs.add(learning_log)
            uow.commit()

    def list_learning_logs(self, user_id: UUID) -> list[LearningLog]:
        with self._uow_factory() as uow:
            return uow.learning_logs.list_by_user(user_id)

    def get_learning_log(self, user_id: UUID, learning_log_id: UUID) -> LearningLog | None:
        with self._uow_factory() as uow:
            return uow.learning_logs.get_by_id(user_id, learning_log_id)

    def update_learning_log(self, learning_log: LearningLog) -> None:
        with self._uow_factory() as uow:
            uow.learning_logs.update(learning_log)
            uow.commit()

    def delete_learning_log(self, user_id: UUID, learning_log_id: UUID) -> None:
        with self._uow_factory() as uow:
            uow.learning_logs.delete(user_id, learning_log_id)
            uow.commit()
