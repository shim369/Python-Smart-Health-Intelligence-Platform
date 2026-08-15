"""Unit of Work Interface。

複数Repositoryにまたがる更新処理を単一トランザクションとして扱うための
境界を定義する(architecture.md Section 15 / requirements.md 14章・17.5)。

Repositoryは原則としてUnitOfWorkを通じてのみ取得し、独自にSessionの
生成・commit・rollbackを行わない。Transactionの責務はService /
Unit of Work側に置く。

具体的な実装(SQLAlchemy Sessionのライフサイクル管理等)はPhase 2で
`repositories/sqlalchemy/unit_of_work.py` 等に追加する想定。
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from health_intelligence.repositories.protocols import (
    HealthLogRepository,
    IngredientRepository,
    MealLogRepository,
    RecipeIngredientRepository,
    RecipeRepository,
    SleepLogRepository,
    UserRepository,
    WeightLogRepository,
    WorkoutLogRepository,
)


class UnitOfWork(Protocol):
    """1つのトランザクション境界内で利用可能なRepository群。

    `with`文で利用することを想定する。

    ```python
    with uow_factory() as uow:
        uow.recipes.add(recipe)
        uow.recipe_ingredients.add(recipe_ingredient)
        uow.commit()
    ```

    `commit()`が呼ばれないまま`with`ブロックを抜けた場合(正常終了・
    例外いずれの場合も)、`__exit__`はrollbackする。
    """

    users: UserRepository
    health_logs: HealthLogRepository
    meal_logs: MealLogRepository
    workout_logs: WorkoutLogRepository
    sleep_logs: SleepLogRepository
    weight_logs: WeightLogRepository
    ingredients: IngredientRepository
    recipes: RecipeRepository
    recipe_ingredients: RecipeIngredientRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """with文を抜ける際、明示的にcommitされていなければrollbackする。"""
        ...

    def commit(self) -> None:
        """このUoW配下の全変更を確定する。"""
        ...

    def rollback(self) -> None:
        """このUoW配下の全変更を明示的に取り消す。"""
        ...
