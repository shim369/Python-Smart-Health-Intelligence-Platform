"""SqlAlchemyによる`RecipeRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import RecipeORM
from health_intelligence.domain.enums import RecipeSource
from health_intelligence.domain.models import Recipe


def _to_domain(orm: RecipeORM) -> Recipe:
    return Recipe(
        recipe_id=orm.id,
        user_id=orm.user_id,
        title=orm.title,
        instructions=orm.instructions,
        source=RecipeSource(orm.source),
        created_at=orm.created_at,
    )


def _to_orm(recipe: Recipe) -> RecipeORM:
    return RecipeORM(
        id=recipe.recipe_id,
        user_id=recipe.user_id,
        title=recipe.title,
        instructions=recipe.instructions,
        source=recipe.source.value,
        created_at=recipe.created_at,
    )


class SqlAlchemyRecipeRepository:
    """`repositories.protocols.RecipeRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID, recipe_id: UUID) -> Recipe | None:
        stmt = select(RecipeORM).where(
            RecipeORM.id == recipe_id, RecipeORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def list_by_user(self, user_id: UUID) -> list[Recipe]:
        stmt = select(RecipeORM).where(RecipeORM.user_id == user_id)
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def add(self, recipe: Recipe) -> None:
        self._session.add(_to_orm(recipe))

    def delete(self, user_id: UUID, recipe_id: UUID) -> None:
        stmt = select(RecipeORM).where(
            RecipeORM.id == recipe_id, RecipeORM.user_id == user_id
        )
        orm = self._session.scalars(stmt).first()
        if orm is not None:
            self._session.delete(orm)
