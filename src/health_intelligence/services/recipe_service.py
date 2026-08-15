"""RecipeService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.ai.protocols import AIProvider
from health_intelligence.domain.models import Recipe, RecipeIngredient
from health_intelligence.repositories.unit_of_work import UnitOfWork


class RecipeService:
    """Recipeに関するユースケースを担当するService。

    レシピのAI生成には別途 `AIProvider` に依存する
    (architecture.md Section 10 AI Architecture)。
    """

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        ai_provider: AIProvider,
    ) -> None:
        self._uow_factory = uow_factory
        self._ai_provider = ai_provider

    def save_recipe(self, recipe: Recipe, ingredients: list[RecipeIngredient]) -> None:
        """Recipeとその材料一覧を1トランザクションで保存する。

        RecipeRepositoryとRecipeIngredientRepositoryという複数
        Repositoryにまたがる更新を、1つのUnitOfWorkで束ねる例
        (architecture.md Section 15 / Section 31)。
        片方の保存に失敗した場合は全体がrollbackされる。
        """
        with self._uow_factory() as uow:
            uow.recipes.add(recipe)
            for ingredient in ingredients:
                uow.recipe_ingredients.add(ingredient)
            uow.commit()

    def list_recipe_history(self, user_id: UUID) -> list[Recipe]:
        with self._uow_factory() as uow:
            return uow.recipes.list_by_user(user_id)

    def get_recipe_ingredients(self, recipe_id: UUID) -> list[RecipeIngredient]:
        with self._uow_factory() as uow:
            return uow.recipe_ingredients.list_by_recipe(recipe_id)

    def generate_recipe(self, user_id: UUID, ingredient_names: list[str]) -> Recipe:
        """食材リストからAIによってレシピを生成する。

        Prompt Builder / Structured Output / Retry・Timeout・
        Recipe Cacheの実装はPhase 5(Recommendation・AI Recipe Engine)
        で行う。ここではInterfaceの形だけを確定する。
        """
        raise NotImplementedError("Phase 5で実装する")
