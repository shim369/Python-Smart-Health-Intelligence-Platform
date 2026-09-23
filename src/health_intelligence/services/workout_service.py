"""WorkoutService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.domain.models import WorkoutLog
from health_intelligence.repositories.unit_of_work import UnitOfWork


class WorkoutService:
    """WorkoutLogに関するユースケースを担当するService。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def record_workout_log(self, workout_log: WorkoutLog) -> None:
        with self._uow_factory() as uow:
            uow.workout_logs.add(workout_log)
            uow.commit()

    def record_workout_logs(self, workout_logs: list[WorkoutLog]) -> None:
        """複数件を1トランザクションでまとめて記録する(CSV一括インポート用)。

        1件ずつ`record_workout_log`を呼ぶと件数分のDB往復・commitが発生し、
        リモートDBでは件数に比例して著しく遅くなるため。
        """
        with self._uow_factory() as uow:
            for workout_log in workout_logs:
                uow.workout_logs.add(workout_log)
            uow.commit()

    def list_workout_logs(self, user_id: UUID) -> list[WorkoutLog]:
        with self._uow_factory() as uow:
            return uow.workout_logs.list_by_user(user_id)

    def get_workout_log(self, user_id: UUID, workout_log_id: UUID) -> WorkoutLog | None:
        with self._uow_factory() as uow:
            return uow.workout_logs.get_by_id(user_id, workout_log_id)

    def update_workout_log(self, workout_log: WorkoutLog) -> None:
        with self._uow_factory() as uow:
            uow.workout_logs.update(workout_log)
            uow.commit()

    def delete_workout_log(self, user_id: UUID, workout_log_id: UUID) -> None:
        with self._uow_factory() as uow:
            uow.workout_logs.delete(user_id, workout_log_id)
            uow.commit()
