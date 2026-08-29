"""運動記録フォームのデータ変換ロジック。

Streamlitの`st.data_editor`から得られる行データ(dict)を、WorkoutLog
Domain Model(セッション/種目/セットの3階層構造)へ変換する。UIから
独立した純粋関数として実装し、Streamlit無しでテストできるようにする。

想定する行の形式(各行がdict):
    {"exercise_name": str, "category": "cardio" | "strength",
     "duration_minutes": int | None, "reps": int | None,
     "weight_kg": float | None}

同じ (exercise_name, category) の行は1つのWorkoutExerciseへまとめ、
strength種目の各行は1セットとして扱う。例えば

    レッグプレス, strength, -, 10, 75
    レッグプレス, strength, -, 10, 75

は「レッグプレス」1種目・2セットのWorkoutExerciseになる。
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from health_intelligence.domain.enums import ExerciseCategory
from health_intelligence.domain.models import WorkoutExercise, WorkoutLog, WorkoutSet


def build_workout_log(
    rows: list[dict[str, object]],
    *,
    user_id: UUID,
    performed_at: datetime,
    memo: str | None = None,
    workout_log_id: UUID | None = None,
) -> WorkoutLog:
    """data_editorの行データからWorkoutLogを組み立てる。

    exercise_nameまたはcategoryが空の行は無視する。
    `workout_log_id`を指定すると、新規発行せずそのIDを使う
    (既存レコードの編集・更新時に同一IDを維持するため)。
    """
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    order: list[tuple[str, str]] = []

    for row in rows:
        name = str(row.get("exercise_name") or "").strip()
        category_value = str(row.get("category") or "").strip()
        if not name or not category_value:
            continue

        key = (name, category_value)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(row)

    exercises: list[WorkoutExercise] = []
    for name, category_value in order:
        category = ExerciseCategory(category_value)
        group_rows = grouped[(name, category_value)]

        if category == ExerciseCategory.CARDIO:
            total_duration = sum(
                int(r["duration_minutes"])  # type: ignore[arg-type]
                for r in group_rows
                if r.get("duration_minutes") not in (None, "")
            )
            exercises.append(
                WorkoutExercise(
                    exercise_name=name,
                    category=category,
                    duration_minutes=total_duration or None,
                )
            )
        else:
            sets = [
                WorkoutSet(
                    reps=int(r["reps"]),  # type: ignore[arg-type]
                    weight_kg=(
                        float(r["weight_kg"])  # type: ignore[arg-type]
                        if r.get("weight_kg") not in (None, "")
                        else None
                    ),
                )
                for r in group_rows
                if r.get("reps") not in (None, "")
            ]
            exercises.append(WorkoutExercise(exercise_name=name, category=category, sets=sets))

    return WorkoutLog(
        workout_log_id=workout_log_id or uuid4(),
        user_id=user_id,
        performed_at=performed_at,
        exercises=exercises,
        memo=memo,
    )


def rows_to_entries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """フラット行データ(1行=1セット、cardioは1行)を、種目カードUI用の
    ネスト構造(種目ごとにsetsをまとめた辞書のリスト)へ変換する。

    `build_workout_log`のグルーピング((exercise_name, category)単位)と
    対称。既存記録の編集フォームや「前回と同じ」復元時に、種目ごとの
    カードとして表示するために使う。
    """
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    order: list[tuple[str, str]] = []

    for row in rows:
        name = str(row.get("exercise_name") or "").strip()
        category = str(row.get("category") or "").strip()
        if not name or not category:
            continue

        key = (name, category)
        if key not in grouped:
            grouped[key] = {
                "exercise_name": name,
                "category": category,
                "duration_minutes": None,
                "sets": [],
            }
            order.append(key)

        entry = grouped[key]
        if category == "cardio":
            duration = row.get("duration_minutes")
            if duration not in (None, ""):
                current = entry["duration_minutes"]
                entry["duration_minutes"] = (
                    int(current) if current is not None else 0  # type: ignore[arg-type]
                ) + int(duration)  # type: ignore[arg-type]
        elif row.get("reps") not in (None, ""):
            entry["sets"].append(  # type: ignore[union-attr]
                {"reps": row["reps"], "weight_kg": row.get("weight_kg")}
            )

    return [grouped[key] for key in order]


def entries_to_rows(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    """種目カードUI用のネスト構造を、`build_workout_log`が受け付ける
    フラット行データへ変換する(`rows_to_entries`の逆変換)。
    """
    rows: list[dict[str, object]] = []
    for entry in entries:
        name = str(entry.get("exercise_name") or "").strip()
        category = str(entry.get("category") or "").strip()

        if category == "cardio":
            rows.append(
                {
                    "exercise_name": name,
                    "category": category,
                    "duration_minutes": entry.get("duration_minutes"),
                    "reps": None,
                    "weight_kg": None,
                }
            )
            continue

        sets = entry.get("sets") or []
        if not sets:
            rows.append(
                {
                    "exercise_name": name,
                    "category": category,
                    "duration_minutes": None,
                    "reps": None,
                    "weight_kg": None,
                }
            )
        for workout_set in sets:  # type: ignore[union-attr]
            rows.append(
                {
                    "exercise_name": name,
                    "category": category,
                    "duration_minutes": None,
                    "reps": workout_set.get("reps"),
                    "weight_kg": workout_set.get("weight_kg"),
                }
            )
    return rows


def workout_log_to_rows(workout_log: WorkoutLog) -> list[dict[str, object]]:
    """WorkoutLogをdata_editorの行データ(dictのリスト)へ逆変換する。

    `build_workout_log`の逆方向。既存の運動記録を編集フォームへ
    再現するために使う。1つのWorkoutExercise(strength、複数セット)は
    セット数だけ行に展開する(build_workout_logのグルーピングと対称)。
    """
    rows: list[dict[str, object]] = []
    for exercise in workout_log.exercises:
        if exercise.category == ExerciseCategory.CARDIO:
            rows.append(
                {
                    "exercise_name": exercise.exercise_name,
                    "category": exercise.category.value,
                    "duration_minutes": exercise.duration_minutes,
                    "reps": None,
                    "weight_kg": None,
                }
            )
        else:
            if not exercise.sets:
                rows.append(
                    {
                        "exercise_name": exercise.exercise_name,
                        "category": exercise.category.value,
                        "duration_minutes": None,
                        "reps": None,
                        "weight_kg": None,
                    }
                )
            for workout_set in exercise.sets:
                rows.append(
                    {
                        "exercise_name": exercise.exercise_name,
                        "category": exercise.category.value,
                        "duration_minutes": None,
                        "reps": workout_set.reps,
                        "weight_kg": workout_set.weight_kg,
                    }
                )
    return rows


def _format_weight(weight_kg: float) -> str:
    """75.0のような余分な小数を削り、72.5のような値はそのまま残す。"""
    return f"{weight_kg:g}"


def format_exercise_line(exercise: WorkoutExercise) -> str:
    """WorkoutExerciseを「種目名：値」の1行テキストへ整形する。

    過去の記録一覧で、種目名だけでなく回数・重量・セット数を確認できる
    ようにするための表示用関数(手記(kiroku等)でよく使われる
    「スクワット：30回 × 2」のような記法に合わせる)。

    有酸素運動は「名前：N分」。筋力トレーニングは、連続する同じ
    (reps, weight_kg)のセットをまとめて「N回(Wkg) × M」とし、セットの
    途中でreps・weightが変わる場合はカンマ区切りで複数グループを並べる
    (例: "10回(30kg) × 1, 10回(20kg) × 1")。
    """
    if exercise.category == ExerciseCategory.CARDIO:
        duration = exercise.duration_minutes
        value = f"{duration}分" if duration is not None else "-"
        return f"{exercise.exercise_name}：{value}"

    if not exercise.sets:
        return f"{exercise.exercise_name}：-"

    groups: list[tuple[int, float | None, int]] = []
    for workout_set in exercise.sets:
        if groups and groups[-1][0] == workout_set.reps and groups[-1][1] == workout_set.weight_kg:
            last_reps, last_weight, last_count = groups[-1]
            groups[-1] = (last_reps, last_weight, last_count + 1)
        else:
            groups.append((workout_set.reps, workout_set.weight_kg, 1))

    parts = []
    for reps, weight, count in groups:
        weight_text = f"({_format_weight(weight)}kg)" if weight is not None else ""
        parts.append(f"{reps}回{weight_text} × {count}")
    return f"{exercise.exercise_name}：{', '.join(parts)}"
