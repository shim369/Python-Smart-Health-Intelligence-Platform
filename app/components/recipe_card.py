"""Recipe Cardコンポーネント。"""

from __future__ import annotations

from uuid import UUID

import streamlit as st
from components.formatting import format_datetime_jst
from i18n import t

from health_intelligence.domain.models import Recipe, RecipeIngredient


def render_recipe_card(
    recipe: Recipe,
    ingredients: list[RecipeIngredient],
    ingredient_names: dict[UUID, str],
    key_prefix: str = "",
    as_expander: bool = False,
    expanded: bool = False,
) -> None:
    """1件のRecipeをカード形式で表示する。

    as_expander=Trueの場合、タイトルをクリックして開閉できるアコーディオン
    (st.expander)として表示する。
    """
    card_key = f"recipe-card-{key_prefix}{recipe.recipe_id}"
    container = (
        st.expander(recipe.title, expanded=expanded, key=card_key)
        if as_expander
        else st.container(border=True, key=card_key)
    )
    with container:
        if not as_expander:
            st.subheader(recipe.title)
        st.caption(format_datetime_jst(recipe.created_at))

        if recipe.total_calories is not None:
            st.markdown(
                f"**{recipe.total_calories:.0f}kcal** "
                f"(P: {recipe.protein_g:.0f}g, "
                f"F: {recipe.fat_g:.0f}g, "
                f"C: {recipe.carbohydrate_g:.0f}g)"
            )

        st.markdown(f"**{t('材料')}**")
        for ingredient in ingredients:
            name = ingredient_names.get(ingredient.ingredient_id, t("(不明)"))
            st.markdown(f"- {name}: {ingredient.amount:g}{ingredient.unit}")

        st.markdown(f"**{t('作り方')}**")
        st.write(recipe.instructions)
