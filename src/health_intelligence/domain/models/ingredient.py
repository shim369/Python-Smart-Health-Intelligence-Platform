"""Ingredient Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class Ingredient:
    """食材マスタを表すDomain Model。

    システム共通データであり、user_idを持たない
    (requirements.md 13.2「共通データ」に対応)。
    """

    ingredient_id: UUID
    name: str
    calories_per_100g: float | None = None
    protein_per_100g: float | None = None
    fat_per_100g: float | None = None
    carbohydrate_per_100g: float | None = None
