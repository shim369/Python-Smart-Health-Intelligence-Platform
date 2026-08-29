"""SqlAlchemyによる`WorkoutLogRepository`実装。

WorkoutLog(セッション) → WorkoutExercise(種目) → WorkoutSet(セット)
という3階層のDomain Modelを、対応する3テーブルのORM Modelとの間で
相互変換する。
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from health_intelligence.database.schema import (
    WorkoutExerciseORM,
    WorkoutLogORM,
    WorkoutSetORM,
)
from health_intelligence.domain.enums import ExerciseCategory
from health_intelligence.domain.models import WorkoutExercise, WorkoutLog, WorkoutSet
from health_intelligence.repositories.errors import RecordNotFoundError

_EXERCISES_WITH_SETS = selectinload(WorkoutLogORM.exercises).selectinload(WorkoutExerciseORM.sets)
"""exercises・setsを個別クエリの遅延ロードに任せず一括で事前読み込みする。
デフォルト(lazy="select")のままだと、一覧取得時に記録件数×種目数分の
N+1クエリが発生し、CSV一括インポート後などレコード数が多い場合に
著しく遅くなる。"""


def _to_domain(orm: WorkoutLogORM) -> WorkoutLog:
    return WorkoutLog(
        workout_log_id=orm.id,
        user_id=orm.user_id,
        performed_at=orm.performed_at,
        calories_burned=orm.calories_burned,
        memo=orm.memo,
        exercises=[
            WorkoutExercise(
                exercise_name=exercise_orm.exercise_name,
                category=ExerciseCategory(exercise_orm.category),
                duration_minutes=exercise_orm.duration_minutes,
                sets=[
                    WorkoutSet(reps=set_orm.reps, weight_kg=set_orm.weight_kg)
                    for set_orm in exercise_orm.sets
                ],
            )
            for exercise_orm in orm.exercises
        ],
    )


def _build_exercise_orms(
    exercises: list[WorkoutExercise],
) -> list[WorkoutExerciseORM]:
    """WorkoutExerciseのリストから、対応するORM(子のWorkoutSetORM含む)
    のリストを組み立てる。`add`(新規作成)と`update`(既存差し替え)の
    両方から利用する共通ロジック。"""
    return [
        WorkoutExerciseORM(
            id=uuid4(),
            order_index=exercise_index,
            exercise_name=exercise.exercise_name,
            category=exercise.category.value,
            duration_minutes=exercise.duration_minutes,
            sets=[
                WorkoutSetORM(
                    id=uuid4(),
                    order_index=set_index,
                    reps=workout_set.reps,
                    weight_kg=workout_set.weight_kg,
                )
                for set_index, workout_set in enumerate(exercise.sets)
            ],
        )
        for exercise_index, exercise in enumerate(exercises)
    ]


def _to_orm(workout_log: WorkoutLog) -> WorkoutLogORM:
    return WorkoutLogORM(
        id=workout_log.workout_log_id,
        user_id=workout_log.user_id,
        performed_at=workout_log.performed_at,
        calories_burned=workout_log.calories_burned,
        memo=workout_log.memo,
        exercises=_build_exercise_orms(workout_log.exercises),
    )


class SqlAlchemyWorkoutLogRepository:
    """`repositories.protocols.WorkoutLogRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, workout_log_id: UUID) -> WorkoutLog | None:
        stmt = (
            select(WorkoutLogORM)
            .where(WorkoutLogORM.id == workout_log_id, WorkoutLogORM.user_id == user_id)
            .options(_EXERCISES_WITH_SETS)
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(self, user_id: UUID) -> list[WorkoutLog]:
        stmt = (
            select(WorkoutLogORM)
            .where(WorkoutLogORM.user_id == user_id)
            .options(_EXERCISES_WITH_SETS)
        )
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, workout_log: WorkoutLog) -> None:
        # exercises/setsはcascade="all, delete-orphan"設定により、
        # WorkoutLogORMをaddするだけで子オブジェクトも合わせて永続化される。
        self._session.add(_to_orm(workout_log))

    def update(self, workout_log: WorkoutLog) -> None:
        """既存のWorkoutLogを更新する。

        `exercises`を新しいORMリストへまるごと差し替える。
        `cascade="all, delete-orphan"`(database/schema.py参照)により、
        除外されたWorkoutExerciseORM/WorkoutSetORMは自動的に削除され、
        新しいものが追加される。個々の種目・セットを1件ずつ差分更新
        するより単純で、種目の追加・削除・並び替えも自然に扱える。
        """
        stmt = select(WorkoutLogORM).where(
            WorkoutLogORM.id == workout_log.workout_log_id,
            WorkoutLogORM.user_id == workout_log.user_id,
        )
        orm = self._session.scalars(stmt).first()
        if orm is None:
            raise RecordNotFoundError(str(workout_log.workout_log_id))
        orm.performed_at = workout_log.performed_at
        orm.calories_burned = workout_log.calories_burned
        orm.memo = workout_log.memo
        orm.exercises = _build_exercise_orms(workout_log.exercises)

    def delete(self, user_id: UUID, workout_log_id: UUID) -> None:
        stmt = select(WorkoutLogORM).where(
            WorkoutLogORM.id == workout_log_id, WorkoutLogORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
