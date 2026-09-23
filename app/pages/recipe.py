"""AIレシピ生成・履歴ページ。"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

# インポート前に app/ ディレクトリを sys.path へ追加
app_dir = Path(__file__).resolve().parents[1]
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.recipe_card import render_recipe_card  # noqa: E402
from i18n import t  # noqa: E402
from services import get_recipe_service, prefetch  # noqa: E402

from health_intelligence.ai.errors import AIProviderError  # noqa: E402

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title(":material/restaurant_menu: " + t("AIレシピ"))

recipe_service = get_recipe_service()

st.subheader(t("レシピを生成する"))
ingredients_text = st.text_area(
    t("使いたい食材(改行またはカンマ区切り)"),
    placeholder=t("鶏むね肉\nブロッコリー\n卵"),
)

if st.button(t("レシピを生成")):
    ingredient_names = [
        name.strip()
        for chunk in ingredients_text.replace(",", "\n").split("\n")
        for name in [chunk.strip()]
        if name
    ]
    if not ingredient_names:
        st.error(t("食材を1つ以上入力してください。"))
    else:
        with st.spinner(t("レシピを生成しています(最大3分程度かかる場合があります)...")):
            try:
                recipe = recipe_service.generate_recipe(user_id, ingredient_names)
            except AIProviderError as e:
                st.error(t("レシピの生成に失敗しました: {error}", error=e))
            else:
                st.success(t("レシピを生成しました。"))
                recipe_ingredients = recipe_service.get_recipe_ingredients(recipe.recipe_id)
                ingredient_names_map = recipe_service.get_ingredient_names(recipe_ingredients)
                render_recipe_card(
                    recipe, recipe_ingredients, ingredient_names_map, key_prefix="new-"
                )

st.divider()
st.subheader(t("レシピ履歴"))

history = recipe_service.list_recipe_history(user_id)
# 履歴1件ごとに材料・材料名を直列に取得するとDB往復が件数×2回積み上がるため、
# 先に並列で取得してキャッシュに載せておく(材料名は材料一覧に依存するため2段階)。
prefetch(*(lambda r=r: recipe_service.get_recipe_ingredients(r.recipe_id) for r in history))
prefetch(
    *(
        lambda r=r: recipe_service.get_ingredient_names(
            recipe_service.get_recipe_ingredients(r.recipe_id)
        )
        for r in history
    )
)
if not history:
    st.info(t("まだ生成されたレシピがありません。"))
else:
    for recipe in sorted(history, key=lambda r: r.created_at, reverse=True):
        recipe_ingredients = recipe_service.get_recipe_ingredients(recipe.recipe_id)
        ingredient_names_map = recipe_service.get_ingredient_names(recipe_ingredients)

        def delete_recipe(recipe_id: UUID = recipe.recipe_id) -> None:
            recipe_service.delete_recipe(user_id, recipe_id)
            st.success(t("レシピを削除しました。"))
            st.rerun()

        render_recipe_card(
            recipe,
            recipe_ingredients,
            ingredient_names_map,
            key_prefix="history-",
            as_expander=True,
            on_delete=delete_recipe,
        )
