"""MealService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.ai.meal_nutrition_cache import MealNutritionCache
from health_intelligence.ai.protocols import AIProvider
from health_intelligence.ai.schemas import EstimatedMealNutrition, MealNutritionInput
from health_intelligence.domain.models import MealLog
from health_intelligence.repositories.unit_of_work import UnitOfWork


class MealService:
    """MealLogに関するユースケースを担当するService。

    食事内容の自由記述からのカロリー・PFC推定には`AIProvider`に
    依存する(RecipeServiceにおけるレシピ生成と同様のパターン。
    architecture.md Section 10 AI Architecture)。
    """

    def __init__(
        self, uow_factory: Callable[[], UnitOfWork], ai_provider: AIProvider
    ) -> None:
        self._uow_factory = uow_factory
        self._ai_provider = ai_provider
        self._nutrition_cache = MealNutritionCache()

    def estimate_nutrition(self, description: str) -> EstimatedMealNutrition:
        """食べたものの自由記述からカロリー・PFCを推定する。

        同一の記述に対しては`MealNutritionCache`により、AI Providerへの
        呼び出しを省略する(RecipeServiceのRecipeCacheと同様)。
        戻り値はあくまで目安であり、呼び出し側(Presentation Layer)で
        記録前にユーザーへ確認・修正させる想定。
        """
        meal_input = MealNutritionInput(description=description)

        cached = self._nutrition_cache.get(meal_input)
        if cached is not None:
            return cached

        estimated = self._ai_provider.estimate_meal_nutrition(meal_input)
        self._nutrition_cache.set(meal_input, estimated)
        return estimated

    def record_meal_log(self, meal_log: MealLog) -> None:
        with self._uow_factory() as uow:
            uow.meal_logs.add(meal_log)
            uow.commit()

    def list_meal_logs(self, user_id: UUID) -> list[MealLog]:
        with self._uow_factory() as uow:
            return uow.meal_logs.list_by_user(user_id)

    def get_meal_log(self, user_id: UUID, meal_log_id: UUID) -> MealLog | None:
        with self._uow_factory() as uow:
            return uow.meal_logs.get_by_id(user_id, meal_log_id)

    def update_meal_log(self, meal_log: MealLog) -> None:
        with self._uow_factory() as uow:
            uow.meal_logs.update(meal_log)
            uow.commit()

    def delete_meal_log(self, user_id: UUID, meal_log_id: UUID) -> None:
        with self._uow_factory() as uow:
            uow.meal_logs.delete(user_id, meal_log_id)
            uow.commit()
