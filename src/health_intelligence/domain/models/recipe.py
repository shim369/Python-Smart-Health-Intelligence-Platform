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
    """

    recipe_id: UUID
    user_id: UUID
    title: str
    instructions: str
    source: RecipeSource
    created_at: datetime
