"""テスト・ローカル開発用のFakeAIProvider。

architecture.md Section 10.1 FakeAIProvider:
API Key不要のテスト、APIコスト削減、API障害時のテスト、
Deterministicなテスト、CIでのAI処理テストを目的とする。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from health_intelligence.ai.schemas import (
    EstimatedMealNutrition,
    GeneratedRecipe,
    GeneratedRecipeIngredient,
    MealNutritionInput,
    RecipeInput,
)
from health_intelligence.domain.enums import Locale


@dataclass
class FakeAIProvider:
    """Deterministicにレシピ(または注入した例外)を返すAIProvider実装。

    テストコードから `fixed_recipe` / `next_error` を設定することで、
    以下のようなケースを検証できる。

    - 正常系: 固定レシピ、または未指定時は入力食材から機械的に組み立てた
      レシピを返す
    - 異常系: `next_error` に `AIRateLimitError` 等を設定しておくと、
      次回の `generate_recipe` 呼び出しでその例外を送出する
      (一度使うと自動的にクリアされる)
    """

    fixed_recipe: GeneratedRecipe | None = None
    fixed_meal_nutrition: EstimatedMealNutrition | None = None
    next_error: Exception | None = None
    call_count: int = field(default=0, init=False)

    def generate_recipe(self, recipe_input: RecipeInput) -> GeneratedRecipe:
        self.call_count += 1

        if self.next_error is not None:
            error, self.next_error = self.next_error, None
            raise error

        if self.fixed_recipe is not None:
            return self.fixed_recipe

        if recipe_input.locale == Locale.EN:
            title = f"{', '.join(recipe_input.ingredient_names)} recipe"
            instructions = "1. Cut the ingredients\n2. Heat in the microwave\n3. Plate and serve"
            unit = "serving"
        else:
            title = f"{'・'.join(recipe_input.ingredient_names)}のレシピ"
            instructions = "1. 材料を切る\n2. 電子レンジで加熱する\n3. 盛り付ける"
            unit = "人前"

        return GeneratedRecipe(
            title=title,
            instructions=instructions,
            ingredients=[
                GeneratedRecipeIngredient(name=name, amount=1.0, unit=unit)
                for name in recipe_input.ingredient_names
            ],
            total_calories=400.0,
            protein_g=20.0,
            fat_g=15.0,
            carbohydrate_g=45.0,
        )

    def estimate_meal_nutrition(self, meal_input: MealNutritionInput) -> EstimatedMealNutrition:
        self.call_count += 1

        if self.next_error is not None:
            error, self.next_error = self.next_error, None
            raise error

        if self.fixed_meal_nutrition is not None:
            return self.fixed_meal_nutrition

        return EstimatedMealNutrition(
            calories=400.0,
            protein_g=20.0,
            fat_g=15.0,
            carbohydrate_g=45.0,
        )
