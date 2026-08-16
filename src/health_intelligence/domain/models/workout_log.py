"""WorkoutLog Domain Model。

1回の運動セッション(WorkoutLog)は複数の種目(WorkoutExercise)からなり、
筋力トレーニングの種目はさらに複数セット(WorkoutSet)からなる、という
3階層構造で運動記録を表現する。

例:

```text
有酸素運動：25分
レッグプレス：10回(75kg) × 2
チェストプレス：10回(20kg) × 2
ラットプルダウン：10回(30kg) × 1, 10回(20kg) × 1
```

は以下のように対応する。

```text
WorkoutLog(performed_at=..., exercises=[
    WorkoutExercise(exercise_name="有酸素運動", category=CARDIO,
                     duration_minutes=25),
    WorkoutExercise(exercise_name="レッグプレス", category=STRENGTH,
                     sets=[WorkoutSet(10, 75), WorkoutSet(10, 75)]),
    WorkoutExercise(exercise_name="チェストプレス", category=STRENGTH,
                     sets=[WorkoutSet(10, 20), WorkoutSet(10, 20)]),
    WorkoutExercise(exercise_name="ラットプルダウン", category=STRENGTH,
                     sets=[WorkoutSet(10, 30), WorkoutSet(10, 20)]),
])
```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from health_intelligence.domain.enums import ExerciseCategory


@dataclass(frozen=True, kw_only=True, slots=True)
class WorkoutSet:
    """筋力トレーニングの1セット分の記録。

    セットごとに回数・重さが異なるケース(例: ラットプルダウンで
    1セット目30kg、2セット目20kg)をそのまま表現できる。
    """

    reps: int
    weight_kg: float | None = None
    """自重トレーニング等、重さが無い種目ではNoneを許容する。"""


@dataclass(frozen=True, kw_only=True, slots=True)
class WorkoutExercise:
    """1種目分の運動記録。

    有酸素運動(CARDIO)は`duration_minutes`を、筋力トレーニング
    (STRENGTH)は`sets`を用いる。両方を同時に埋める必要はない。
    """

    exercise_name: str
    """種目名。例: "有酸素運動", "レッグプレス", "ラットプルダウン"。"""
    category: ExerciseCategory
    duration_minutes: int | None = None
    """有酸素運動の実施時間(分)。CARDIO種目で使用する。"""
    sets: list[WorkoutSet] = field(default_factory=list)
    """筋力トレーニングのセット一覧。STRENGTH種目で使用する。"""


@dataclass(frozen=True, kw_only=True, slots=True)
class WorkoutLog:
    """1回の運動セッションを表すDomain Model。"""

    workout_log_id: UUID
    user_id: UUID
    performed_at: datetime
    exercises: list[WorkoutExercise]
    calories_burned: float | None = None
    """セッション全体の消費カロリー(ウェアラブル端末等から取得した場合)。"""
    memo: str | None = None
