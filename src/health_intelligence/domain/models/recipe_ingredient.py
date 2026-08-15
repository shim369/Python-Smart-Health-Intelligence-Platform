"""RecipeIngredient Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class RecipeIngredient:
    """RecipeとIngredientの関連(分量情報付き)を表すDomain Model。"""

    recipe_id: UUID
    ingredient_id: UUID
    amount: float
    unit: str
    """分量の単位。例: "g", "ml", "個"。"""
