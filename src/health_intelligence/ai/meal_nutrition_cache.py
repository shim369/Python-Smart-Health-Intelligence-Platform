"""食事栄養推定結果のプロセス内キャッシュ。

同一の食事内容の記述に対する重複したAI API呼び出しを抑制する
(RecipeCache: recipe_cache.pyと同様の目的・制約)。

プロセスメモリ上のキャッシュのため、アプリケーション再起動やStreamlit
Community Cloudのスリープ復帰では消える。
"""

from __future__ import annotations

from health_intelligence.ai.schemas import EstimatedMealNutrition, MealNutritionInput


def _cache_key(meal_input: MealNutritionInput) -> str:
    return meal_input.description.strip()


class MealNutritionCache:
    """`MealNutritionInput`をキーにした単純なプロセス内キャッシュ。"""

    def __init__(self) -> None:
        self._store: dict[str, EstimatedMealNutrition] = {}

    def get(self, meal_input: MealNutritionInput) -> EstimatedMealNutrition | None:
        return self._store.get(_cache_key(meal_input))

    def set(self, meal_input: MealNutritionInput, nutrition: EstimatedMealNutrition) -> None:
        self._store[_cache_key(meal_input)] = nutrition
