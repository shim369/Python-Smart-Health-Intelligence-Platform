"""Domain Modelで利用するEnum定義。

外部入力(Pydantic Schema等)との境界でも同じEnumを再利用してよいが、
Enumの値そのものはDatabase固有の表現に依存させない。
"""

from __future__ import annotations

from enum import StrEnum


class Locale(StrEnum):
    """UIの表示言語。Userごとに永続化する(domain/models/user.py参照)。"""

    JA = "ja"
    EN = "en"


class MealType(StrEnum):
    """MealLogの食事区分。"""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    PRE_WORKOUT = "pre_workout"


class ExerciseCategory(StrEnum):
    """WorkoutExerciseの種目カテゴリ。

    有酸素運動は`duration_minutes`、筋力トレーニングは`sets`で
    記録する(workout_log.pyのWorkoutExercise参照)。
    """

    CARDIO = "cardio"
    STRENGTH = "strength"


class SleepQuality(StrEnum):
    """SleepLogの主観的な睡眠品質。"""

    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class RecipeSource(StrEnum):
    """Recipeの生成元。"""

    MANUAL = "manual"
    AI_GENERATED = "ai_generated"


class LearningCategory(StrEnum):
    """LearningLogの学習区分。

    区分ごとに使用するフィールドが異なる(試験勉強はcontent/breakdown、
    キャリア戦略はnotesを使う等)。learning_log.py参照。
    """

    EXAM_STUDY = "exam_study"
    PORTFOLIO_DEV = "portfolio_dev"
    RESEARCH = "research"
    CAREER_STRATEGY = "career_strategy"


class LearningLocation(StrEnum):
    """LearningLogを記録した場所。"""

    HOME = "home"
    GYM = "gym"
    COWORKING_SPACE = "coworking_space"
    CAFE = "cafe"


class GoalCategory(StrEnum):
    """Goal/Taskのカテゴリ(daily-journal-design.md 3.2節)。

    `TaskLogType`の既定値は各カテゴリで異なる(task.py参照)が、
    Task単位で個別に上書きできる。
    """

    STUDY = "study"
    PF_DEV = "pf_dev"
    WORK = "work"
    DIET = "diet"
    EXERCISE = "exercise"
    SLEEP = "sleep"
    CAREER = "career"
    LIFE = "life"


class GoalStatus(StrEnum):
    """Goalの進行状況。"""

    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    SUSPENDED = "suspended"


class TaskLogType(StrEnum):
    """Task.log_typeによる実績記録方式の区分(daily-journal-design.md 3.3節)。

    COUNT_AND_DURATIONは`DailyTaskLog`(数量・時間・メモ)で実績を記録する。
    PLAN_ONLYは選ぶだけで、実績は既存のMealLog/WorkoutLog/SleepLogが担う。
    """

    COUNT_AND_DURATION = "count_and_duration"
    PLAN_ONLY = "plan_only"
