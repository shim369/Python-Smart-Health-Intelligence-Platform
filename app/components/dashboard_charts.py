"""ダッシュボードの週間グラフ用、Streamlit非依存の集計関数。

各グラフは「過去7日間、日付ごとの合計/平均」という同じ形の集計を
繰り返し使うため、`group_sum_by_date`/`group_average_by_date`という
2つの汎用関数に集約する。運動(WorkoutLog)は種目・セットの入れ子構造を
持つため、専用の集計関数を別に用意する。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date, timedelta

from health_intelligence.domain.enums import ExerciseCategory
from health_intelligence.domain.models import WorkoutLog


def last_n_days(reference: date, n: int) -> list[date]:
    """`reference`を含む直近n日間を、古い→新しい順で返す。"""
    return [reference - timedelta(days=offset) for offset in range(n - 1, -1, -1)]


def group_sum_by_date[T](
    items: Iterable[T],
    date_of: Callable[[T], date],
    value_of: Callable[[T], float],
    dates: list[date],
) -> list[float]:
    """`items`を`date_of`で日付ごとにグルーピングし、`value_of`の合計を
    `dates`の並び順で返す。`dates`に含まれない日付のitemは無視する。
    """
    totals = dict.fromkeys(dates, 0.0)
    for item in items:
        d = date_of(item)
        if d in totals:
            totals[d] += value_of(item)
    return [totals[d] for d in dates]


def group_average_by_date[T](
    items: Iterable[T],
    date_of: Callable[[T], date],
    value_of: Callable[[T], float | None],
    dates: list[date],
) -> list[float | None]:
    """`group_sum_by_date`の平均版。値がNoneのitemは分母に含めない。
    その日の集計対象が1件もない場合はNoneを返す(0と区別するため)。
    """
    sums = dict.fromkeys(dates, 0.0)
    counts = dict.fromkeys(dates, 0)
    for item in items:
        d = date_of(item)
        if d not in sums:
            continue
        v = value_of(item)
        if v is not None:
            sums[d] += v
            counts[d] += 1
    return [sums[d] / counts[d] if counts[d] else None for d in dates]


def strength_max_weight_by_exercise(
    workout_logs: Iterable[WorkoutLog],
    date_of: Callable[[WorkoutLog], date],
    dates: list[date],
    *,
    top_n: int = 5,
) -> dict[str, list[float | None]]:
    """筋トレ種目ごとの、日別の最大重量(kg)を`dates`の並び順で返す。

    表示期間内に記録した日数が多い上位`top_n`種目のみを返す(種目が多いと
    線が重なって読めなくなるため)。重量の無いセット(懸垂等の自重種目)は
    対象外で、その日に記録が無い場合はNoneを返す。
    """
    date_set = set(dates)
    max_by_exercise: dict[str, dict[date, float]] = {}
    for log in workout_logs:
        d = date_of(log)
        if d not in date_set:
            continue
        for exercise in log.exercises:
            if exercise.category != ExerciseCategory.STRENGTH:
                continue
            weights = [s.weight_kg for s in exercise.sets if s.weight_kg is not None]
            if not weights:
                continue
            by_date = max_by_exercise.setdefault(exercise.exercise_name, {})
            by_date[d] = max(by_date.get(d, 0.0), *weights)

    top = sorted(max_by_exercise, key=lambda name: (-len(max_by_exercise[name]), name))[:top_n]
    return {name: [max_by_exercise[name].get(d) for d in dates] for name in top}


def strength_volume_by_date(
    workout_logs: Iterable[WorkoutLog],
    date_of: Callable[[WorkoutLog], date],
    dates: list[date],
) -> list[float]:
    """筋トレの総挙上量(重量×回数の全セット合計、kg)を日別に返す。

    重量の無いセット(自重種目)は重量を決められないため含めない。
    """
    totals = dict.fromkeys(dates, 0.0)
    for log in workout_logs:
        d = date_of(log)
        if d not in totals:
            continue
        for exercise in log.exercises:
            if exercise.category != ExerciseCategory.STRENGTH:
                continue
            totals[d] += sum(s.weight_kg * s.reps for s in exercise.sets if s.weight_kg is not None)
    return [totals[d] for d in dates]


def cardio_minutes_by_exercise(
    workout_logs: Iterable[WorkoutLog],
    date_of: Callable[[WorkoutLog], date],
    dates: list[date],
) -> dict[str, list[float]]:
    """有酸素種目ごとの日別運動時間(分)を返す(種目別の積み上げ棒グラフ用)。

    表示期間内に一度も記録の無い種目は含めない。種目の並びは期間内の
    合計時間が長い順(積み上げの下側・凡例の上側に主要な種目が来るように)。
    """
    date_set = set(dates)
    minutes: dict[str, dict[date, float]] = {}
    for log in workout_logs:
        d = date_of(log)
        if d not in date_set:
            continue
        for exercise in log.exercises:
            if exercise.category != ExerciseCategory.CARDIO:
                continue
            by_date = minutes.setdefault(exercise.exercise_name, {})
            by_date[d] = by_date.get(d, 0.0) + (exercise.duration_minutes or 0)

    order = sorted(minutes, key=lambda name: (-sum(minutes[name].values()), name))
    return {name: [minutes[name].get(d, 0.0) for d in dates] for name in order}
