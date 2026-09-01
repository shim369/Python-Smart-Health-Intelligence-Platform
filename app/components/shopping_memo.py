"""買い物メモ×レシピ連動関連の、Streamlit非依存の純粋関数。
requirements.md 4.5節(買い物メモとレシピ機能の連動)。

新しいテーブルは不要。既存のRecipe/RecipeIngredientから材料名を取得し、
買い物メモのテキストへ追記するだけの軽量な機能とする。
"""

from __future__ import annotations

from health_intelligence.domain.models import Recipe


def format_recipe_ingredients_line(recipe: Recipe, ingredient_names: list[str]) -> str:
    """例: "鶏むね肉とキャベツの塩昆布炒め: 鶏むね肉, キャベツ, ごま油, 塩昆布, 酒, 醤油" """
    return f"{recipe.title}: {', '.join(ingredient_names)}"


def append_recipe_ingredients(
    existing_memo: str, recipe: Recipe, ingredient_names: list[str]
) -> str:
    """既存の買い物メモへ、選んだレシピの材料名の行を追記する。

    追記後は自由に編集可能(家にある食材を消す等)。既存メモが空の場合は
    改行を挟まずそのまま1行目として追加する。
    """
    line = format_recipe_ingredients_line(recipe, ingredient_names)
    return f"{existing_memo}\n{line}" if existing_memo.strip() else line
