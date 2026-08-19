"""SqlAlchemyによる`IngredientRepository`実装。

Ingredientはシステム共通データのため、user_idを境界条件に取らない。
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import IngredientORM
from health_intelligence.domain.models import Ingredient


def _to_domain(orm: IngredientORM) -> Ingredient:
    return Ingredient(
        ingredient_id=orm.id,
        name=orm.name,
        calories_per_100g=orm.calories_per_100g,
        protein_per_100g=orm.protein_per_100g,
        fat_per_100g=orm.fat_per_100g,
        carbohydrate_per_100g=orm.carbohydrate_per_100g,
    )


def _to_orm(ingredient: Ingredient) -> IngredientORM:
    return IngredientORM(
        id=ingredient.ingredient_id,
        name=ingredient.name,
        calories_per_100g=ingredient.calories_per_100g,
        protein_per_100g=ingredient.protein_per_100g,
        fat_per_100g=ingredient.fat_per_100g,
        carbohydrate_per_100g=ingredient.carbohydrate_per_100g,
    )


class SqlAlchemyIngredientRepository:
    """`repositories.protocols.IngredientRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, ingredient_id: UUID) -> Ingredient | None:
        orm = self._session.get(IngredientORM, ingredient_id)
        return _to_domain(orm) if orm is not None else None

    def get_by_name(self, name: str) -> Ingredient | None:
        """大文字小文字を区別せず名前で検索する(get or create用)。"""
        stmt = select(IngredientORM).where(
            func.lower(IngredientORM.name) == name.lower()
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_all(self) -> list[Ingredient]:
        stmt = select(IngredientORM)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, ingredient: Ingredient) -> None:
        self._session.add(_to_orm(ingredient))
