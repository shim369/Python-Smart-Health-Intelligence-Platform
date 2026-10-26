"""RecipeService。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from health_intelligence.ai.protocols import AIProvider
from health_intelligence.ai.recipe_cache import RecipeCache
from health_intelligence.ai.schemas import GeneratedRecipeIngredient, RecipeInput
from health_intelligence.domain.enums import Locale, RecipeSource
from health_intelligence.domain.models import Ingredient, Recipe, RecipeIngredient
from health_intelligence.repositories.errors import DuplicateKeyError
from health_intelligence.repositories.unit_of_work import UnitOfWork


class RecipeService:
    """Recipeに関するユースケースを担当するService。

    レシピのAI生成には`AIProvider`に依存する
    (architecture.md Section 10 AI Architecture)。
    """

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        ai_provider: AIProvider,
    ) -> None:
        self._uow_factory = uow_factory
        self._ai_provider = ai_provider
        self._recipe_cache = RecipeCache()

    def save_recipe(self, recipe: Recipe, ingredients: list[RecipeIngredient]) -> None:
        """Recipeとその材料一覧を1トランザクションで保存する。

        RecipeRepositoryとRecipeIngredientRepositoryという複数
        Repositoryにまたがる更新を、1つのUnitOfWorkで束ねる例
        (architecture.md Section 15 / Section 31)。
        片方の保存に失敗した場合は全体がrollbackされる。

        `generate_recipe`はIngredientのget-or-createも含めて1つの
        トランザクションで完結させたいため、この関数を呼ばず自前で
        UnitOfWorkを開く(手動でRecipeを組み立てて保存したい場合向けの
        独立したエントリーポイントとして残す)。
        """
        with self._uow_factory() as uow:
            uow.recipes.add(recipe)
            for ingredient in ingredients:
                uow.recipe_ingredients.add(ingredient)
            uow.commit()

    def list_recipe_history(self, user_id: UUID) -> list[Recipe]:
        with self._uow_factory() as uow:
            return uow.recipes.list_by_user(user_id)

    def delete_recipe(self, user_id: UUID, recipe_id: UUID) -> None:
        """Recipeを削除する。

        RecipeORM.ingredients のORMレベルcascade(`delete-orphan`)により、
        紐づくRecipeIngredientも合わせて削除される。
        """
        with self._uow_factory() as uow:
            uow.recipes.delete(user_id, recipe_id)
            uow.commit()

    def get_recipe_ingredients(self, recipe_id: UUID) -> list[RecipeIngredient]:
        with self._uow_factory() as uow:
            return uow.recipe_ingredients.list_by_recipe(recipe_id)

    def get_ingredient_names(self, recipe_ingredients: list[RecipeIngredient]) -> dict[UUID, str]:
        """RecipeIngredientのingredient_idからIngredient名を引く。

        Presentation Layer(app/)がIngredientRepositoryへ直接
        アクセスしないよう、Service経由でまとめて解決する。
        """
        ingredient_ids = list({ri.ingredient_id for ri in recipe_ingredients})
        with self._uow_factory() as uow:
            return {i.ingredient_id: i.name for i in uow.ingredients.list_by_ids(ingredient_ids)}

    def generate_recipe(
        self, user_id: UUID, ingredient_names: list[str], locale: Locale = Locale.JA
    ) -> Recipe:
        """食材リストからAIによってレシピを生成し、保存する。

        同一の食材リスト(+食事制限+カロリー目標)で生成済みの場合は
        RecipeCacheを利用し、AI Providerへの呼び出しを省略する
        (requirements.md 11章)。

        生成されたレシピの材料は、既存のIngredientマスタと名前で突合し
        (`get_by_name`)、一致しなければ新規Ingredientとして作成する
        (get-or-createパターン)。IngredientのGet-or-createとRecipe/
        RecipeIngredientの保存は同じトランザクション内で行う。

        `locale`はレシピ本文を書く言語(UIの表示言語を渡す想定)。
        """
        recipe_input = RecipeInput(ingredient_names=ingredient_names, locale=locale)

        generated = self._recipe_cache.get(recipe_input)
        if generated is None:
            generated = self._ai_provider.generate_recipe(recipe_input)
            self._recipe_cache.set(recipe_input, generated)

        recipe = Recipe(
            recipe_id=uuid4(),
            user_id=user_id,
            title=generated.title,
            instructions=generated.instructions,
            source=RecipeSource.AI_GENERATED,
            created_at=datetime.now(UTC),
            total_calories=generated.total_calories,
            protein_g=generated.protein_g,
            fat_g=generated.fat_g,
            carbohydrate_g=generated.carbohydrate_g,
        )

        with self._uow_factory() as uow:
            recipe_ingredients = [
                RecipeIngredient(
                    recipe_id=recipe.recipe_id,
                    ingredient_id=self._get_or_create_ingredient(
                        uow, generated_ingredient
                    ).ingredient_id,
                    amount=generated_ingredient.amount,
                    unit=generated_ingredient.unit,
                )
                for generated_ingredient in _merge_duplicate_ingredients(generated.ingredients)
            ]

            uow.recipes.add(recipe)
            for recipe_ingredient in recipe_ingredients:
                uow.recipe_ingredients.add(recipe_ingredient)
            uow.commit()

        return recipe

    @staticmethod
    def _get_or_create_ingredient(
        uow: UnitOfWork, generated_ingredient: GeneratedRecipeIngredient
    ) -> Ingredient:
        existing = uow.ingredients.get_by_name(generated_ingredient.name)
        if existing is not None:
            return existing

        ingredient = Ingredient(ingredient_id=uuid4(), name=generated_ingredient.name)
        try:
            uow.ingredients.add(ingredient)
        except DuplicateKeyError:
            # 事前チェック(`get_by_name`)をすり抜けて、別リクエストが同時に
            # 同じ食材を登録した場合(TOCTOU)。`add`はSAVEPOINTまでしか
            # rollbackしないため、同じUnitOfWorkのまま登録済みの食材を引き直す。
            existing = uow.ingredients.get_by_name(generated_ingredient.name)
            assert existing is not None
            return existing
        return ingredient


def _merge_duplicate_ingredients(
    ingredients: list[GeneratedRecipeIngredient],
) -> list[GeneratedRecipeIngredient]:
    """AIの出力に同じ食材が複数回含まれる場合、1件にまとめる。

    recipe_ingredientsの主キーは(recipe_id, ingredient_id)のため、
    「塩」が2回(例: 下味用と仕上げ用)返ってくると保存時に主キー違反と
    なり、レシピ生成全体が失敗する。しかもAIの結果はRecipeCacheに
    保存済みのため、同じ食材で再実行しても同じ結果で失敗し続ける。

    食材名は`IngredientRepository.get_by_name`と同じく大文字小文字を
    区別せず(前後の空白も無視して)突合する。単位が同じなら分量を合算し、
    単位が異なる場合(例: "大さじ"と"少々")は合算できないため最初の
    分量を採用する。
    """
    merged: dict[str, GeneratedRecipeIngredient] = {}
    for ingredient in ingredients:
        name = ingredient.name.strip()
        key = name.lower()
        existing = merged.get(key)
        if existing is None:
            merged[key] = ingredient.model_copy(update={"name": name})
        elif existing.unit == ingredient.unit:
            merged[key] = existing.model_copy(
                update={"amount": existing.amount + ingredient.amount}
            )
    return list(merged.values())
