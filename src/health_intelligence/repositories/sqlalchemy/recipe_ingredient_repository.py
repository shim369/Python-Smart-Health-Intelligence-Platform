"""SqlAlchemyによる`RecipeIngredientRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import RecipeIngredientORM
from health_intelligence.domain.models import RecipeIngredient


def _to_domain(orm: RecipeIngredientORM) -> RecipeIngredient:
    return RecipeIngredient(
        recipe_id=orm.recipe_id,
        ingredient_id=orm.ingredient_id,
        amount=orm.amount,
        unit=orm.unit,
    )


def _to_orm(recipe_ingredient: RecipeIngredient) -> RecipeIngredientORM:
    return RecipeIngredientORM(
        recipe_id=recipe_ingredient.recipe_id,
        ingredient_id=recipe_ingredient.ingredient_id,
        amount=recipe_ingredient.amount,
        unit=recipe_ingredient.unit,
    )


class SqlAlchemyRecipeIngredientRepository:
    """`repositories.protocols.RecipeIngredientRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_recipe(self, recipe_id: UUID) -> list[RecipeIngredient]:
        stmt = select(RecipeIngredientORM).where(
            RecipeIngredientORM.recipe_id == recipe_id
        )
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, recipe_ingredient: RecipeIngredient) -> None:
        self._session.add(_to_orm(recipe_ingredient))
