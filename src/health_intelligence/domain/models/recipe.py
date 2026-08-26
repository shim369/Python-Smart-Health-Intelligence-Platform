"""Recipe Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from health_intelligence.domain.enums import RecipeSource


@dataclass(frozen=True, kw_only=True, slots=True)
class Recipe:
    """レシピを表すDomain Model。

    AI生成・手動作成の両方を保存対象とする(source で区別する)。
    ユーザーが生成・保存したRecipeはuser_idによって所有者を識別する。

    栄養情報(total_calories等)はAI生成時のみ推定値として付与される。
    手動作成レシピや、栄養情報導入前に生成された既存レシピとの互換性
    のため、いずれもNoneを許容する。
    """

    recipe_id: UUID
    user_id: UUID
    title: str
    instructions: str
    source: RecipeSource
    created_at: datetime
    total_calories: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    carbohydrate_g: float | None = None
