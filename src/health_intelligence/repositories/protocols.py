"""Repository層のInterface(Protocol)定義。

Serviceはこれらのprotocolに依存し、具体的なSQLAlchemy実装には
直接依存しない(architecture.md Section 16 Dependency Direction)。

Repositoryはビジネスルールを持たず、CRUD/Queryのみを責務とする
(architecture.md Section 6.5)。ユーザー所有データを扱うメソッドは
原則として`user_id`を境界条件として受け取る
(architecture.md Section 8, requirements.md 13章)。

`update`は、渡されたDomain Modelの`*_id`と`user_id`に一致する
既存レコードの全フィールドを置き換える(部分更新ではない)。
対象が見つからない場合は`RecordNotFoundError`を送出する
(repositories/errors.py参照)。

具体的な実装クラス(例: SQLAlchemyによる実装)はPhase 2で追加する。
"""

from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID

from health_intelligence.domain.enums import Locale
from health_intelligence.domain.models import (
    DailyJournal,
    DailyPlanItem,
    DailyTaskLog,
    Goal,
    HealthLog,
    Ingredient,
    LearningLog,
    MealLog,
    Recipe,
    RecipeIngredient,
    SleepLog,
    Task,
    User,
    WeightLog,
    WorkoutLog,
)


class UserRepository(Protocol):
    """Userの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> None: ...

    def update_locale(self, user_id: UUID, locale: Locale) -> None: ...


class HealthLogRepository(Protocol):
    """HealthLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, health_log_id: UUID) -> HealthLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[HealthLog]: ...

    def add(self, health_log: HealthLog) -> None: ...

    def update(self, health_log: HealthLog) -> None: ...

    def delete(self, user_id: UUID, health_log_id: UUID) -> None: ...


class LearningLogRepository(Protocol):
    """LearningLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, learning_log_id: UUID) -> LearningLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[LearningLog]: ...

    def add(self, learning_log: LearningLog) -> None: ...

    def update(self, learning_log: LearningLog) -> None: ...

    def delete(self, user_id: UUID, learning_log_id: UUID) -> None: ...


class MealLogRepository(Protocol):
    """MealLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, meal_log_id: UUID) -> MealLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[MealLog]: ...

    def add(self, meal_log: MealLog) -> None: ...

    def update(self, meal_log: MealLog) -> None: ...

    def delete(self, user_id: UUID, meal_log_id: UUID) -> None: ...


class WorkoutLogRepository(Protocol):
    """WorkoutLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, workout_log_id: UUID) -> WorkoutLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[WorkoutLog]: ...

    def add(self, workout_log: WorkoutLog) -> None: ...

    def update(self, workout_log: WorkoutLog) -> None: ...

    def delete(self, user_id: UUID, workout_log_id: UUID) -> None: ...


class SleepLogRepository(Protocol):
    """SleepLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, sleep_log_id: UUID) -> SleepLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[SleepLog]: ...

    def add(self, sleep_log: SleepLog) -> None: ...

    def update(self, sleep_log: SleepLog) -> None: ...

    def delete(self, user_id: UUID, sleep_log_id: UUID) -> None: ...


class WeightLogRepository(Protocol):
    """WeightLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, weight_log_id: UUID) -> WeightLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[WeightLog]: ...

    def add(self, weight_log: WeightLog) -> None: ...

    def update(self, weight_log: WeightLog) -> None: ...

    def delete(self, user_id: UUID, weight_log_id: UUID) -> None: ...


class IngredientRepository(Protocol):
    """Ingredientの永続化を担うRepository。

    Ingredientはシステム共通データのため、user_idを境界条件に取らない
    (requirements.md 13.2)。
    """

    def get_by_id(self, ingredient_id: UUID) -> Ingredient | None: ...

    def list_by_ids(self, ingredient_ids: list[UUID]) -> list[Ingredient]: ...

    def get_by_name(self, name: str) -> Ingredient | None: ...

    def list_all(self) -> list[Ingredient]: ...

    def add(self, ingredient: Ingredient) -> None: ...


class RecipeRepository(Protocol):
    """Recipeの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, recipe_id: UUID) -> Recipe | None: ...

    def list_by_user(self, user_id: UUID) -> list[Recipe]: ...

    def add(self, recipe: Recipe) -> None: ...

    def delete(self, user_id: UUID, recipe_id: UUID) -> None: ...


class RecipeIngredientRepository(Protocol):
    """RecipeIngredientの永続化を担うRepository。"""

    def list_by_recipe(self, recipe_id: UUID) -> list[RecipeIngredient]: ...

    def add(self, recipe_ingredient: RecipeIngredient) -> None: ...


class GoalRepository(Protocol):
    """Goalの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, goal_id: UUID) -> Goal | None: ...

    def list_by_user(self, user_id: UUID) -> list[Goal]: ...

    def add(self, goal: Goal) -> None: ...

    def update(self, goal: Goal) -> None: ...

    def delete(self, user_id: UUID, goal_id: UUID) -> None: ...


class TaskRepository(Protocol):
    """Taskの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, task_id: UUID) -> Task | None: ...

    def list_by_user(
        self, user_id: UUID, *, goal_id: UUID | None = None, include_archived: bool = True
    ) -> list[Task]:
        """goal_idを指定した場合はそのGoal配下のTaskのみに絞り込む。

        `goal_id=None`かつ`include_archived=True`の場合は全Task(未分類含む)、
        Goal管理画面の「未分類タスク」セクションでは`goal_id`未指定のまま
        呼び出し側でTask.goal_idがNoneのものを絞り込む用途を想定する。
        """
        ...

    def add(self, task: Task) -> None: ...

    def update(self, task: Task) -> None: ...

    def delete(self, user_id: UUID, task_id: UUID) -> None: ...


class DailyPlanItemRepository(Protocol):
    """DailyPlanItemの永続化を担うRepository。"""

    def list_by_date(self, user_id: UUID, journal_date: date) -> list[DailyPlanItem]: ...

    def replace_for_date(self, user_id: UUID, journal_date: date, task_ids: list[UUID]) -> None:
        """指定日のPをtask_idsの内容へまるごと置き換える(削除+追加)。"""
        ...


class DailyTaskLogRepository(Protocol):
    """DailyTaskLogの永続化を担うRepository。"""

    def get_by_task_and_date(
        self, user_id: UUID, task_id: UUID, journal_date: date
    ) -> DailyTaskLog | None: ...

    def list_by_date(self, user_id: UUID, journal_date: date) -> list[DailyTaskLog]: ...

    def list_by_date_range(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[DailyTaskLog]:
        """ダッシュボードの期間集計用、[start_date, end_date]の全日分を1回で返す。

        `list_by_date`を表示日数分ループ呼び出しするとDBラウンドトリップが
        日数分発生してしまう(N+1)ため、範囲一括取得用に用意する。
        """
        ...

    def list_by_task(self, user_id: UUID, task_id: UUID) -> list[DailyTaskLog]:
        """Goalの進捗集計(累計問題数・累計時間等)のため、同一Taskの全日分を返す。"""
        ...

    def list_by_tasks(self, user_id: UUID, task_ids: list[UUID]) -> list[DailyTaskLog]:
        """複数Task分の全日分を1回で返す(`list_by_task`のTask数分ループ=N+1を避ける)。"""
        ...

    def add(self, daily_task_log: DailyTaskLog) -> None: ...

    def update(self, daily_task_log: DailyTaskLog) -> None: ...

    def delete(self, user_id: UUID, daily_task_log_id: UUID) -> None: ...


class DailyJournalRepository(Protocol):
    """DailyJournalの永続化を担うRepository。"""

    def get_by_date(self, user_id: UUID, journal_date: date) -> DailyJournal | None: ...

    def list_by_date_range(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[DailyJournal]:
        """ダッシュボードの期間集計用、[start_date, end_date]の全日分を1回で返す。

        `get_by_date`を表示日数分ループ呼び出しするとDBラウンドトリップが
        日数分発生してしまう(N+1)ため、範囲一括取得用に用意する。
        """
        ...

    def add(self, daily_journal: DailyJournal) -> None: ...

    def update(self, daily_journal: DailyJournal) -> None: ...
