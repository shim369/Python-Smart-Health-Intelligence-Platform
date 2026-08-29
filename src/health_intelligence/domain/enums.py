"""Domain Modelで利用するEnum定義。

外部入力(Pydantic Schema等)との境界でも同じEnumを再利用してよいが、
Enumの値そのものはDatabase固有の表現に依存させない。
"""

from __future__ import annotations

from enum import StrEnum


class MealType(StrEnum):
    """MealLogの食事区分。"""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


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
