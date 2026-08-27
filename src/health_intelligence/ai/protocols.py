"""AI Provider Interface(Protocol)。

architecture.md Section 10 AI Architecture:
AIサービスはProvider Patternによって抽象化する。Service層は具体的な
Gemini API等に直接依存しない。

```text
AIProvider (Protocol)
    ├── GeminiProvider      (Phase 4B / Phase 5で実装)
    └── FakeAIProvider      (fake_provider.py)
```
"""

from __future__ import annotations

from typing import Protocol

from health_intelligence.ai.schemas import (
    EstimatedMealNutrition,
    GeneratedRecipe,
    MealNutritionInput,
    RecipeInput,
)


class AIProvider(Protocol):
    """AIサービスへの依存を抽象化するInterface。"""

    def generate_recipe(self, recipe_input: RecipeInput) -> GeneratedRecipe:
        """食材等の入力からレシピを生成する。

        Retry(429/503への指数バックオフ)およびTimeoutは実装側
        (GeminiProvider等)の責務とする。呼び出し側は以下を想定する。

        - 正常終了: `GeneratedRecipe` を返す
        - Retry対象エラーが解消しなかった場合:
          `AIRateLimitError` / `AIServiceUnavailableError` を送出
        - Timeout: `AITimeoutError` を送出
        - レスポンスがSchemaを満たさない場合: `AIValidationError` を送出
        """
        ...

    def estimate_meal_nutrition(
        self, meal_input: MealNutritionInput
    ) -> EstimatedMealNutrition:
        """食事内容の自由記述からカロリー・PFCを推定する。

        Retry/Timeout/例外の扱いは`generate_recipe`と同様
        (GeminiProvider等、実装側の責務)。
        """
        ...
