"""CSVインポートのデータ変換ロジック。

過去に手書き(Macのメモ・スプレッドシート等)で記録していたログを、
CSVとして書き出して取り込むための変換処理。`csv.DictReader`で得られる
行データ(dict)をDomain Modelへ変換する。Streamlitに依存しない純粋関数
として実装し、単体テストで検証できるようにする(workout_form.pyと同様
のパターン)。

日付・時刻は日本時間(JST)で入力する想定とし、`combine_jst_to_utc`で
保存用のUTCへ変換する(log_entry.pyの手入力フォームと同じ変換規則)。

行の検証エラーは例外を送出せず`ImportResult.errors`に集約する。
1件の不正な行が原因でファイル全体のインポートが失敗しないようにする
ため(過去データはExcelの手打ちミス等を含みがちで、全件やり直しに
なるのを避けたい)。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type
from datetime import time as time_type
from uuid import UUID, uuid4

from components.formatting import combine_jst_to_utc
from components.workout_form import build_workout_log

from health_intelligence.domain.enums import (
    ExerciseCategory,
    LearningCategory,
    LearningLocation,
    MealType,
    SleepQuality,
)
from health_intelligence.domain.models import (
    HealthLog,
    LearningLog,
    MealLog,
    SleepLog,
    WeightLog,
    WorkoutLog,
)


@dataclass(frozen=True, slots=True)
class ImportRowError:
    """CSVの1行分の検証エラー。

    `row_number`はCSVファイル上の行番号(ヘッダー行を1行目として数える、
    つまり1件目のデータ行は2)。エディタでファイルを開いたときの行数と
    一致させ、ユーザーが該当行を見つけやすくするため。
    """

    row_number: int
    message: str


@dataclass(frozen=True, slots=True)
class ImportResult[T]:
    """CSVインポートの解析結果。

    不正な行があってもファイル全体を失敗させず、有効な行(`logs`)と
    無効な行(`errors`)を両方保持する。呼び出し側は`errors`をプレビュー
    表示し、`logs`のみを実際に保存するかどうかをユーザーに委ねる。
    """

    logs: list[T]
    errors: list[ImportRowError]


def _parse_date(value: str, *, field: str) -> date_type:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field}が空です")
    try:
        return date_type.fromisoformat(text)
    except ValueError as e:
        raise ValueError(f"{field}の形式が不正です(YYYY-MM-DD): {value!r}") from e


def _parse_time(value: str, *, field: str, default: time_type | None = None) -> time_type:
    text = (value or "").strip()
    if not text:
        if default is not None:
            return default
        raise ValueError(f"{field}が空です")
    try:
        return time_type.fromisoformat(text)
    except ValueError as e:
        raise ValueError(f"{field}の形式が不正です(HH:MM): {value!r}") from e


def _parse_float(value: str, *, field: str) -> float:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field}が空です")
    try:
        return float(text)
    except ValueError as e:
        raise ValueError(f"{field}が数値ではありません: {value!r}") from e


def _parse_optional_int(value: str | None) -> int | None:
    text = (value or "").strip()
    return int(text) if text else None


def parse_weight_rows(rows: list[dict[str, str]], *, user_id: UUID) -> ImportResult[WeightLog]:
    """体重ログCSVを解析する。

    列: date(YYYY-MM-DD, 必須), time(HH:MM, 任意・省略時00:00), weight_kg(必須)
    """
    logs: list[WeightLog] = []
    errors: list[ImportRowError] = []

    for row_number, row in enumerate(rows, start=2):
        try:
            recorded_date = _parse_date(row.get("date", ""), field="date")
            recorded_time = _parse_time(row.get("time", ""), field="time", default=time_type(0, 0))
            weight_kg = _parse_float(row.get("weight_kg", ""), field="weight_kg")
        except ValueError as e:
            errors.append(ImportRowError(row_number=row_number, message=str(e)))
            continue

        logs.append(
            WeightLog(
                weight_log_id=uuid4(),
                user_id=user_id,
                recorded_at=combine_jst_to_utc(recorded_date, recorded_time),
                weight_kg=weight_kg,
            )
        )

    return ImportResult(logs=logs, errors=errors)


def parse_sleep_rows(rows: list[dict[str, str]], *, user_id: UUID) -> ImportResult[SleepLog]:
    """睡眠ログCSVを解析する。

    列: bedtime_date, bedtime_time, wake_date, wake_time(いずれも必須),
    quality(任意: poor/fair/good/excellent)
    """
    logs: list[SleepLog] = []
    errors: list[ImportRowError] = []

    for row_number, row in enumerate(rows, start=2):
        try:
            bedtime_date = _parse_date(row.get("bedtime_date", ""), field="bedtime_date")
            bedtime_time = _parse_time(row.get("bedtime_time", ""), field="bedtime_time")
            wake_date = _parse_date(row.get("wake_date", ""), field="wake_date")
            wake_time_value = _parse_time(row.get("wake_time", ""), field="wake_time")

            quality_text = (row.get("quality") or "").strip()
            quality = SleepQuality(quality_text) if quality_text else None

            bedtime = combine_jst_to_utc(bedtime_date, bedtime_time)
            wake_time = combine_jst_to_utc(wake_date, wake_time_value)
            if wake_time <= bedtime:
                raise ValueError("wake_timeはbedtimeより後である必要があります")
        except ValueError as e:
            errors.append(ImportRowError(row_number=row_number, message=str(e)))
            continue

        logs.append(
            SleepLog(
                sleep_log_id=uuid4(),
                user_id=user_id,
                bedtime=bedtime,
                wake_time=wake_time,
                quality=quality,
            )
        )

    return ImportResult(logs=logs, errors=errors)


def parse_meal_rows(rows: list[dict[str, str]], *, user_id: UUID) -> ImportResult[MealLog]:
    """食事ログCSVを解析する。

    列: date, time, meal_type(breakfast/lunch/dinner/snack), calories,
    protein_g, fat_g, carbohydrate_g(いずれも必須), memo(任意)

    AIによるカロリー・PFC推定は行わない(スプシ側で既に把握している
    数値をそのまま取り込む想定のため)。
    """
    logs: list[MealLog] = []
    errors: list[ImportRowError] = []

    for row_number, row in enumerate(rows, start=2):
        try:
            consumed_date = _parse_date(row.get("date", ""), field="date")
            consumed_time = _parse_time(row.get("time", ""), field="time")

            meal_type_text = (row.get("meal_type") or "").strip()
            if not meal_type_text:
                raise ValueError("meal_typeが空です")
            try:
                meal_type = MealType(meal_type_text)
            except ValueError as e:
                valid = ", ".join(m.value for m in MealType)
                raise ValueError(
                    f"meal_typeが不正です({valid}のいずれか): {meal_type_text!r}"
                ) from e

            calories = _parse_float(row.get("calories", ""), field="calories")
            protein_g = _parse_float(row.get("protein_g", ""), field="protein_g")
            fat_g = _parse_float(row.get("fat_g", ""), field="fat_g")
            carbohydrate_g = _parse_float(row.get("carbohydrate_g", ""), field="carbohydrate_g")
        except ValueError as e:
            errors.append(ImportRowError(row_number=row_number, message=str(e)))
            continue

        memo = (row.get("memo") or "").strip() or None

        logs.append(
            MealLog(
                meal_log_id=uuid4(),
                user_id=user_id,
                consumed_at=combine_jst_to_utc(consumed_date, consumed_time),
                meal_type=meal_type,
                calories=calories,
                protein_g=protein_g,
                fat_g=fat_g,
                carbohydrate_g=carbohydrate_g,
                memo=memo,
            )
        )

    return ImportResult(logs=logs, errors=errors)


def parse_health_rows(rows: list[dict[str, str]], *, user_id: UUID) -> ImportResult[HealthLog]:
    """体調ログCSVを解析する。

    列: date, time(必須), condition_score(任意: 1〜5),
    symptoms(任意、複数はセミコロン区切り。CSVの区切り文字と衝突する
    カンマではなくセミコロンを使う), memo(任意)
    """
    logs: list[HealthLog] = []
    errors: list[ImportRowError] = []

    for row_number, row in enumerate(rows, start=2):
        try:
            recorded_date = _parse_date(row.get("date", ""), field="date")
            recorded_time = _parse_time(row.get("time", ""), field="time")
            condition_score = _parse_optional_int(row.get("condition_score"))
            if condition_score is not None and not (1 <= condition_score <= 5):
                raise ValueError(f"condition_scoreは1〜5である必要があります: {condition_score}")
        except ValueError as e:
            errors.append(ImportRowError(row_number=row_number, message=str(e)))
            continue

        symptoms_text = (row.get("symptoms") or "").strip()
        symptoms = [s.strip() for s in symptoms_text.split(";") if s.strip()]
        memo = (row.get("memo") or "").strip() or None

        logs.append(
            HealthLog(
                health_log_id=uuid4(),
                user_id=user_id,
                recorded_at=combine_jst_to_utc(recorded_date, recorded_time),
                condition_score=condition_score,
                symptoms=symptoms,
                memo=memo,
            )
        )

    return ImportResult(logs=logs, errors=errors)


def parse_workout_rows(rows: list[dict[str, str]], *, user_id: UUID) -> ImportResult[WorkoutLog]:
    """運動ログCSVを解析する。

    列: date, time(セッションを識別する組。必須), exercise_name,
    category(cardio/strength、必須), duration_minutes(cardio用、任意),
    reps, weight_kg(strength用、任意)

    同じ(date, time)の行を1回の運動セッション(WorkoutLog)にまとめ、
    セッション内では`build_workout_log`と同じ規則
    (同じexercise_name・categoryの行を1種目・複数セットにまとめる)
    で種目へ変換する(log_entry.pyのdata_editorと同じ変換規則)。
    """
    sessions: dict[tuple[str, str], list[dict[str, str]]] = {}
    order: list[tuple[str, str]] = []
    errors: list[ImportRowError] = []
    row_numbers: dict[tuple[str, str], list[int]] = {}

    for row_number, row in enumerate(rows, start=2):
        try:
            session_date = _parse_date(row.get("date", ""), field="date")
            session_time = _parse_time(row.get("time", ""), field="time")
            name = (row.get("exercise_name") or "").strip()
            category_value = (row.get("category") or "").strip()
            if not name:
                raise ValueError("exercise_nameが空です")
            if category_value not in {c.value for c in ExerciseCategory}:
                valid = ", ".join(c.value for c in ExerciseCategory)
                raise ValueError(f"categoryが不正です({valid}のいずれか): {category_value!r}")
        except ValueError as e:
            errors.append(ImportRowError(row_number=row_number, message=str(e)))
            continue

        key = (session_date.isoformat(), session_time.isoformat())
        if key not in sessions:
            sessions[key] = []
            row_numbers[key] = []
            order.append(key)
        sessions[key].append(
            {
                "exercise_name": name,
                "category": category_value,
                "duration_minutes": row.get("duration_minutes"),
                "reps": row.get("reps"),
                "weight_kg": row.get("weight_kg"),
            }
        )
        row_numbers[key].append(row_number)

    logs: list[WorkoutLog] = []
    for key in order:
        session_date_text, session_time_text = key
        performed_at = combine_jst_to_utc(
            date_type.fromisoformat(session_date_text),
            time_type.fromisoformat(session_time_text),
        )
        workout_log = build_workout_log(
            sessions[key],  # type: ignore[arg-type]
            user_id=user_id,
            performed_at=performed_at,
        )
        if not workout_log.exercises:
            errors.append(
                ImportRowError(
                    row_number=row_numbers[key][0],
                    message="有効な種目がありません",
                )
            )
            continue
        logs.append(workout_log)

    return ImportResult(logs=logs, errors=errors)


def parse_learning_rows(rows: list[dict[str, str]], *, user_id: UUID) -> ImportResult[LearningLog]:
    """学習ログCSVを解析する。

    列: date(必須), time(任意・省略時00:00), category(exam_study/
    portfolio_dev/research/career_strategy、必須), location(任意:
    home/gym/coworking_space/cafe), content(任意), breakdown(任意、
    セミコロン区切り), duration_minutes(任意), keywords(任意、
    セミコロン区切り), notes(任意、セミコロン区切り)

    breakdown/keywords/notesは、他の複数値フィールド(symptoms)と同様に
    セミコロン区切りとする(CSVの区切り文字であるカンマや、アプリUI側の
    スラッシュ区切りとの衝突を避けるため)。
    """
    logs: list[LearningLog] = []
    errors: list[ImportRowError] = []

    for row_number, row in enumerate(rows, start=2):
        try:
            started_date = _parse_date(row.get("date", ""), field="date")
            started_time = _parse_time(row.get("time", ""), field="time", default=time_type(0, 0))

            category_text = (row.get("category") or "").strip()
            if not category_text:
                raise ValueError("categoryが空です")
            try:
                category = LearningCategory(category_text)
            except ValueError as e:
                valid = ", ".join(c.value for c in LearningCategory)
                raise ValueError(f"categoryが不正です({valid}のいずれか): {category_text!r}") from e

            location_text = (row.get("location") or "").strip()
            if location_text:
                try:
                    location = LearningLocation(location_text)
                except ValueError as e:
                    valid = ", ".join(loc.value for loc in LearningLocation)
                    raise ValueError(
                        f"locationが不正です({valid}のいずれか): {location_text!r}"
                    ) from e
            else:
                location = None

            duration_minutes = _parse_optional_int(row.get("duration_minutes"))
        except ValueError as e:
            errors.append(ImportRowError(row_number=row_number, message=str(e)))
            continue

        content = (row.get("content") or "").strip() or None
        breakdown = [s.strip() for s in (row.get("breakdown") or "").split(";") if s.strip()]
        keywords = [s.strip() for s in (row.get("keywords") or "").split(";") if s.strip()]
        notes = [s.strip() for s in (row.get("notes") or "").split(";") if s.strip()]

        logs.append(
            LearningLog(
                learning_log_id=uuid4(),
                user_id=user_id,
                started_at=combine_jst_to_utc(started_date, started_time),
                category=category,
                location=location,
                content=content,
                breakdown=breakdown,
                duration_minutes=duration_minutes,
                keywords=keywords,
                notes=notes,
            )
        )

    return ImportResult(logs=logs, errors=errors)
