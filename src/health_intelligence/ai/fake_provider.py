"""テスト・ローカル開発用のFakeAIProvider。

architecture.md Section 10.1 FakeAIProvider:
API Key不要のテスト、APIコスト削減、API障害時のテスト、
Deterministicなテスト、CIでのAI処理テストを目的とする。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from health_intelligence.ai.schemas import (
    GeneratedRecipe,
    GeneratedRecipeIngredient,
    RecipeInput,
)


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
    next_error: Exception | None = None
    call_count: int = field(default=0, init=False)

    def generate_recipe(self, recipe_input: RecipeInput) -> GeneratedRecipe:
        self.call_count += 1

        if self.next_error is not None:
            error, self.next_error = self.next_error, None
            raise error

        if self.fixed_recipe is not None:
            return self.fixed_recipe

        return GeneratedRecipe(
            title=f"{'・'.join(recipe_input.ingredient_names)}のレシピ",
            instructions="1. 材料を切る\n2. 加熱する\n3. 盛り付ける",
            ingredients=[
                GeneratedRecipeIngredient(name=name, amount=1.0, unit="人前")
                for name in recipe_input.ingredient_names
            ],
        )
