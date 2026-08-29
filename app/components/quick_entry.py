"""「前回と同じ」「よく使う」入力を支援するロジック。

食事・運動は日々似た内容を繰り返すことが多いため、過去のログ履歴から
直近の1件、および頻出する組み合わせを抽出し、新規記録フォームへ
再利用しやすい形へ変換する。新しい永続化(テンプレートの保存)は
追加せず、既存のログ履歴から都度導出する。

Streamlitに依存しない純粋関数として実装し、単体テストで検証できる
ようにする(workout_form.py / csv_import.pyと同様のパターン)。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from health_intelligence.domain.enums import ExerciseCategory, MealType
from health_intelligence.domain.models import (
    LearningLog,
    MealLog,
    WorkoutExercise,
    WorkoutLog,
)


@dataclass(frozen=True, slots=True)
class MealTemplate:
    """頻出する食事内容の候補。"""

    memo: str
    meal_type: MealType
    calories: float
    protein_g: float
    fat_g: float
    carbohydrate_g: float
    usage_count: int


def most_recent_meal(meal_logs: list[MealLog]) -> MealLog | None:
    """直近の食事ログを返す(「前回と同じ」用)。"""
    if not meal_logs:
        return None
    return max(meal_logs, key=lambda m: m.consumed_at)


def frequent_meal_templates(
    meal_logs: list[MealLog], *, limit: int = 5
) -> list[MealTemplate]:
    """よく使う食事の候補を、使用頻度が高い順に返す。

    memoが空のログはテンプレート化できない(何を食べたか特定できない
    ため)ので除外する。同じ(memo, meal_type)が複数回記録されている
    場合、栄養値は最新の記録を採用する(同じメモでも量が変わっている
    可能性があり、頻度内の平均より直近の実績を優先するため)。
    """
    groups: dict[tuple[str, MealType], list[MealLog]] = {}
    for log in meal_logs:
        memo = (log.memo or "").strip()
        if not memo:
            continue
        groups.setdefault((memo, log.meal_type), []).append(log)

    templates = [
        MealTemplate(
            memo=memo,
            meal_type=meal_type,
            calories=(latest := max(logs, key=lambda m: m.consumed_at)).calories,
            protein_g=latest.protein_g,
            fat_g=latest.fat_g,
            carbohydrate_g=latest.carbohydrate_g,
            usage_count=len(logs),
        )
        for (memo, meal_type), logs in groups.items()
    ]
    templates.sort(key=lambda t: t.usage_count, reverse=True)
    return templates[:limit]


def most_recent_learning_log(learning_logs: list[LearningLog]) -> LearningLog | None:
    """直近の学習ログを返す(「前回と同じ内容を入力」用)。"""
    if not learning_logs:
        return None
    return max(learning_logs, key=lambda log: log.started_at)


@dataclass(frozen=True, slots=True)
class KeywordTemplate:
    """よく使う技術的成長キーワードの候補。"""

    keyword: str
    usage_count: int


def frequent_learning_keywords(
    learning_logs: list[LearningLog], *, limit: int = 8
) -> list[KeywordTemplate]:
    """よく使う技術的成長キーワードを、使用頻度が高い順に返す。

    1件の学習ログが複数キーワードを持つため(例: "Python", "SQL")、
    メール/運動のテンプレートとは異なりログ単位ではなくキーワード
    単位で集計する。カテゴリを問わず全ログを対象とする(同じ
    キーワードが複数カテゴリで使い回されるケースを想定)。
    """
    counts: dict[str, int] = {}
    for log in learning_logs:
        for keyword in log.keywords:
            counts[keyword] = counts.get(keyword, 0) + 1

    templates = [
        KeywordTemplate(keyword=keyword, usage_count=count)
        for keyword, count in counts.items()
    ]
    templates.sort(key=lambda t: t.usage_count, reverse=True)
    return templates[:limit]


@dataclass(frozen=True, slots=True)
class ExerciseTemplate:
    """よく使う種目の候補。直近の実績値をデフォルトとして持つ。"""

    exercise_name: str
    category: ExerciseCategory
    usage_count: int
    last_duration_minutes: int | None
    last_reps: int | None
    last_weight_kg: float | None


def frequent_exercise_templates(
    workout_logs: list[WorkoutLog], *, limit: int = 8
) -> list[ExerciseTemplate]:
    """よく使う種目の候補を、使用頻度が高い順に返す。

    (exercise_name, category)ごとに集計し、直近のセッションでの
    duration_minutes / 最終セットのreps・weight_kgをデフォルト値とする。
    """
    groups: dict[
        tuple[str, ExerciseCategory], list[tuple[WorkoutExercise, datetime]]
    ] = {}
    for log in workout_logs:
        for exercise in log.exercises:
            key = (exercise.exercise_name, exercise.category)
            groups.setdefault(key, []).append((exercise, log.performed_at))

    templates: list[ExerciseTemplate] = []
    for (name, category), items in groups.items():
        items.sort(key=lambda pair: pair[1])
        latest_exercise = items[-1][0]
        last_set = latest_exercise.sets[-1] if latest_exercise.sets else None
        templates.append(
            ExerciseTemplate(
                exercise_name=name,
                category=category,
                usage_count=len(items),
                last_duration_minutes=latest_exercise.duration_minutes,
                last_reps=last_set.reps if last_set is not None else None,
                last_weight_kg=last_set.weight_kg if last_set is not None else None,
            )
        )

    templates.sort(key=lambda t: t.usage_count, reverse=True)
    return templates[:limit]


def exercise_template_to_entry(template: ExerciseTemplate) -> dict[str, object]:
    """ExerciseTemplateを種目カードUI用のエントリ辞書(components/workout_form.py
    の`entries_to_rows`が受け付けるネスト構造)へ変換する。
    """
    if template.category == ExerciseCategory.CARDIO:
        return {
            "exercise_name": template.exercise_name,
            "category": template.category.value,
            "duration_minutes": template.last_duration_minutes,
            "sets": [],
        }
    return {
        "exercise_name": template.exercise_name,
        "category": template.category.value,
        "duration_minutes": None,
        "sets": [{"reps": template.last_reps, "weight_kg": template.last_weight_kg}],
    }
