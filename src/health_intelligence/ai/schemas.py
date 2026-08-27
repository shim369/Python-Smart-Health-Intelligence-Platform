"""AI Provider境界で利用するPydantic Schema。

architecture.md Section 6.4: 外部境界(AI Structured Output等)には
Pydanticを利用する。ここで定義するSchemaはAIProviderの入出力にのみ
使い、Domain Model(Recipe/RecipeIngredient)への変換はService層で行う。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecipeInput(BaseModel):
    """レシピ生成のためのAIへの入力。"""

    ingredient_names: list[str] = Field(min_length=1)
    dietary_preference: str | None = None
    calorie_target: float | None = None


class GeneratedRecipeIngredient(BaseModel):
    """AIが生成したレシピの材料1件分。"""

    name: str
    amount: float
    unit: str


class GeneratedRecipe(BaseModel):
    """AIのStructured Outputとして受け取るレシピ本体。

    Pydantic Validationにより、Schemaを満たさないレスポンスは
    AIValidationErrorとして呼び出し側へ伝播させる想定
    (実際のValidation Error変換は各Provider実装側で行う)。
    """

    title: str
    instructions: str
    ingredients: list[GeneratedRecipeIngredient] = Field(min_length=1)
    total_calories: float
    """レシピ全体(材料表記の分量全体)の推定カロリー(kcal)。"""
    protein_g: float
    """レシピ全体の推定タンパク質量(g)。"""
    fat_g: float
    """レシピ全体の推定脂質量(g)。"""
    carbohydrate_g: float
    """レシピ全体の推定炭水化物量(g)。"""


class MealNutritionInput(BaseModel):
    """食事記録の栄養推定のためのAIへの入力。"""

    description: str = Field(min_length=1)
    """食べたものの自由記述(例: 「納豆1パック、ご飯茶碗1杯」)。"""


class EstimatedMealNutrition(BaseModel):
    """AIが推定した食事1件分の栄養情報。

    厳密な栄養計算ではなく目安であり、ユーザーは記録前に確認・修正
    できる想定(requirements.mdの食事記録機能を参照)。
    """

    calories: float
    protein_g: float
    fat_g: float
    carbohydrate_g: float
