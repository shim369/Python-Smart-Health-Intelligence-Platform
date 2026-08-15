"""Repository層のInterface(Protocol)定義。

Serviceはこれらのprotocolに依存し、具体的なSQLAlchemy実装には
直接依存しない(architecture.md Section 16 Dependency Direction)。

Repositoryはビジネスルールを持たず、CRUD/Queryのみを責務とする
(architecture.md Section 6.5)。ユーザー所有データを扱うメソッドは
原則として`user_id`を境界条件として受け取る
(architecture.md Section 8, requirements.md 13章)。

具体的な実装クラス(例: SQLAlchemyによる実装)はPhase 2で追加する。
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from health_intelligence.domain.models import (
    HealthLog,
    Ingredient,
    MealLog,
    Recipe,
    RecipeIngredient,
    SleepLog,
    User,
    WeightLog,
    WorkoutLog,
)


class UserRepository(Protocol):
    """Userの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> None: ...


class HealthLogRepository(Protocol):
    """HealthLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, health_log_id: UUID) -> HealthLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[HealthLog]: ...

    def add(self, health_log: HealthLog) -> None: ...

    def delete(self, user_id: UUID, health_log_id: UUID) -> None: ...


class MealLogRepository(Protocol):
    """MealLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, meal_log_id: UUID) -> MealLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[MealLog]: ...

    def add(self, meal_log: MealLog) -> None: ...

    def delete(self, user_id: UUID, meal_log_id: UUID) -> None: ...


class WorkoutLogRepository(Protocol):
    """WorkoutLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, workout_log_id: UUID) -> WorkoutLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[WorkoutLog]: ...

    def add(self, workout_log: WorkoutLog) -> None: ...

    def delete(self, user_id: UUID, workout_log_id: UUID) -> None: ...


class SleepLogRepository(Protocol):
    """SleepLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, sleep_log_id: UUID) -> SleepLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[SleepLog]: ...

    def add(self, sleep_log: SleepLog) -> None: ...

    def delete(self, user_id: UUID, sleep_log_id: UUID) -> None: ...


class WeightLogRepository(Protocol):
    """WeightLogの永続化を担うRepository。"""

    def get_by_id(self, user_id: UUID, weight_log_id: UUID) -> WeightLog | None: ...

    def list_by_user(self, user_id: UUID) -> list[WeightLog]: ...

    def add(self, weight_log: WeightLog) -> None: ...

    def delete(self, user_id: UUID, weight_log_id: UUID) -> None: ...


class IngredientRepository(Protocol):
    """Ingredientの永続化を担うRepository。

    Ingredientはシステム共通データのため、user_idを境界条件に取らない
    (requirements.md 13.2)。
    """

    def get_by_id(self, ingredient_id: UUID) -> Ingredient | None: ...

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
