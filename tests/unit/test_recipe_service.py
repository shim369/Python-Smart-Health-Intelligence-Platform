"""RecipeService.generate_recipeのテスト。"""

from __future__ import annotations

from uuid import UUID, uuid4

from health_intelligence.ai.fake_provider import FakeAIProvider
from health_intelligence.ai.schemas import GeneratedRecipe, GeneratedRecipeIngredient
from health_intelligence.domain.models import Ingredient, Recipe, RecipeIngredient
from health_intelligence.repositories.errors import DuplicateKeyError
from health_intelligence.services.recipe_service import RecipeService


class _FakeIngredientRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Ingredient] = {}

    def get_by_name(self, name: str) -> Ingredient | None:
        return next((i for i in self.items.values() if i.name.lower() == name.lower()), None)

    def add(self, ingredient: Ingredient) -> None:
        self.items[ingredient.ingredient_id] = ingredient


class _FakeRecipeRepository:
    def __init__(self) -> None:
        self.items: list[Recipe] = []

    def add(self, recipe: Recipe) -> None:
        self.items.append(recipe)


class _FakeRecipeIngredientRepository:
    """主キー(recipe_id, ingredient_id)の重複を実DBと同様に拒否する。"""

    def __init__(self) -> None:
        self.items: dict[tuple[UUID, UUID], RecipeIngredient] = {}

    def add(self, recipe_ingredient: RecipeIngredient) -> None:
        key = (recipe_ingredient.recipe_id, recipe_ingredient.ingredient_id)
        if key in self.items:
            raise AssertionError(f"duplicate primary key: {key}")
        self.items[key] = recipe_ingredient


def _generated(*ingredients: GeneratedRecipeIngredient) -> GeneratedRecipe:
    return GeneratedRecipe(
        title="鶏の照り焼き",
        instructions="焼く",
        ingredients=list(ingredients),
        total_calories=500.0,
        protein_g=30.0,
        fat_g=20.0,
        carbohydrate_g=40.0,
    )


def test_generate_recipe_merges_duplicate_ingredients(make_fake_uow_factory) -> None:
    ingredients = _FakeIngredientRepository()
    recipe_ingredients = _FakeRecipeIngredientRepository()
    uow_factory = make_fake_uow_factory(
        ingredients=ingredients,
        recipes=_FakeRecipeRepository(),
        recipe_ingredients=recipe_ingredients,
    )
    ai_provider = FakeAIProvider(
        fixed_recipe=_generated(
            GeneratedRecipeIngredient(name="鶏もも肉", amount=200, unit="g"),
            GeneratedRecipeIngredient(name="塩", amount=1, unit="g"),
            GeneratedRecipeIngredient(name=" 塩 ", amount=2, unit="g"),
            GeneratedRecipeIngredient(name="Soy Sauce", amount=1, unit="大さじ"),
            GeneratedRecipeIngredient(name="soy sauce", amount=1, unit="少々"),
        )
    )
    service = RecipeService(uow_factory, ai_provider)

    recipe = service.generate_recipe(uuid4(), ["鶏もも肉"])

    saved = {
        ingredients.items[ri.ingredient_id].name: (ri.amount, ri.unit)
        for ri in recipe_ingredients.items.values()
        if ri.recipe_id == recipe.recipe_id
    }
    assert saved == {
        "鶏もも肉": (200, "g"),
        "塩": (3, "g"),
        "Soy Sauce": (1, "大さじ"),
    }
    assert len(ingredients.items) == 3


class _RacingIngredientRepository(_FakeIngredientRepository):
    """`get_by_name`の直後に別リクエストが同名の食材を登録した状況を再現する。

    最初の`add`で、先に登録された食材(`winner`)をマスタへ入れたうえで
    実DBの一意制約違反と同様に`DuplicateKeyError`を送出する。
    """

    def __init__(self, winner: Ingredient) -> None:
        super().__init__()
        self._winner: Ingredient | None = winner

    def add(self, ingredient: Ingredient) -> None:
        if self._winner is not None:
            self.items[self._winner.ingredient_id] = self._winner
            self._winner = None
        if self.get_by_name(ingredient.name) is not None:
            raise DuplicateKeyError(ingredient.name)
        super().add(ingredient)


def test_generate_recipe_reuses_ingredient_created_concurrently(make_fake_uow_factory) -> None:
    winner = Ingredient(ingredient_id=uuid4(), name="鶏もも肉")
    ingredients = _RacingIngredientRepository(winner)
    recipe_ingredients = _FakeRecipeIngredientRepository()
    uow_factory = make_fake_uow_factory(
        ingredients=ingredients,
        recipes=_FakeRecipeRepository(),
        recipe_ingredients=recipe_ingredients,
    )
    ai_provider = FakeAIProvider(
        fixed_recipe=_generated(GeneratedRecipeIngredient(name="鶏もも肉", amount=200, unit="g"))
    )
    service = RecipeService(uow_factory, ai_provider)

    recipe = service.generate_recipe(uuid4(), ["鶏もも肉"])

    assert [ri.ingredient_id for ri in recipe_ingredients.items.values()] == [winner.ingredient_id]
    assert recipe_ingredients.items[(recipe.recipe_id, winner.ingredient_id)].amount == 200
    assert list(ingredients.items) == [winner.ingredient_id]
