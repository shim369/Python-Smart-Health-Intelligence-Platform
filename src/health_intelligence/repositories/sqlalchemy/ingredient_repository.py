"""SqlAlchemyによる`IngredientRepository`実装。

Ingredientはシステム共通データのため、user_idを境界条件に取らない。
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from health_intelligence.database.schema import IngredientORM
from health_intelligence.domain.models import Ingredient
from health_intelligence.repositories.errors import DuplicateKeyError


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

    def list_by_ids(self, ingredient_ids: list[UUID]) -> list[Ingredient]:
        """複数IDをIN句の1クエリでまとめて取得する(1件ずつのN+1クエリを避ける)。"""
        if not ingredient_ids:
            return []
        stmt = select(IngredientORM).where(IngredientORM.id.in_(ingredient_ids))
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def get_by_name(self, name: str) -> Ingredient | None:
        """大文字小文字を区別せず名前で検索する(get or create用)。"""
        # 一意インデックス(lower(name))と判定を揃えるため、比較対象もDB側でlowerする
        stmt = select(IngredientORM).where(func.lower(IngredientORM.name) == func.lower(name))
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_all(self) -> list[Ingredient]:
        stmt = select(IngredientORM)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, ingredient: Ingredient) -> None:
        """Ingredientを追加する。

        同名(大文字小文字を区別しない)の食材が既に存在する場合は
        `DuplicateKeyError`を送出する。

        レシピ生成ではIngredientのget-or-createとRecipeの保存を1つの
        トランザクションで行うため、SAVEPOINT(`begin_nested`)内で
        `flush()`して一意制約違反を検知する。違反時はSAVEPOINTまでしか
        rollbackされないので、呼び出し側は同じUnitOfWorkのまま
        `get_by_name`で引き直して処理を続行できる。
        """
        try:
            with self._session.begin_nested():
                self._session.add(_to_orm(ingredient))
        except IntegrityError as e:
            raise DuplicateKeyError(f"ingredient already exists: {ingredient.name}") from e
