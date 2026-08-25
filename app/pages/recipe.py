"""AIレシピ生成・履歴ページ。"""

from __future__ import annotations

import sys
from pathlib import Path

# インポート前に app/ ディレクトリを sys.path へ追加
app_dir = Path(__file__).resolve().parents[1]
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.recipe_card import render_recipe_card  # noqa: E402
from services import get_recipe_service  # noqa: E402

from health_intelligence.ai.errors import AIProviderError  # noqa: E402

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title("AIレシピ")

recipe_service = get_recipe_service()

st.subheader("レシピを生成する")
ingredients_text = st.text_area(
    "使いたい食材(改行またはカンマ区切り)",
    placeholder="鶏むね肉\nブロッコリー\n卵",
)

if st.button("レシピを生成"):
    ingredient_names = [
        name.strip()
        for chunk in ingredients_text.replace(",", "\n").split("\n")
        for name in [chunk.strip()]
        if name
    ]
    if not ingredient_names:
        st.error("食材を1つ以上入力してください。")
    else:
        with st.spinner("レシピを生成しています(最大1分程度かかる場合があります)..."):
            try:
                recipe = recipe_service.generate_recipe(user_id, ingredient_names)
            except AIProviderError as e:
                st.error(f"レシピの生成に失敗しました: {e}")
            else:
                st.success("レシピを生成しました。")
                recipe_ingredients = recipe_service.get_recipe_ingredients(
                    recipe.recipe_id
                )
                ingredient_names_map = recipe_service.get_ingredient_names(
                    recipe_ingredients
                )
                render_recipe_card(recipe, recipe_ingredients, ingredient_names_map)

st.divider()
st.subheader("レシピ履歴")

history = recipe_service.list_recipe_history(user_id)
if not history:
    st.info("まだ生成されたレシピがありません。")
else:
    for recipe in sorted(history, key=lambda r: r.created_at, reverse=True):
        recipe_ingredients = recipe_service.get_recipe_ingredients(recipe.recipe_id)
        ingredient_names_map = recipe_service.get_ingredient_names(recipe_ingredients)
        render_recipe_card(recipe, recipe_ingredients, ingredient_names_map)
