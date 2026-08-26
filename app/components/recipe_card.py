"""Recipe Cardコンポーネント。"""

from __future__ import annotations

from uuid import UUID

import streamlit as st
from components.formatting import format_datetime_jst

from health_intelligence.domain.models import Recipe, RecipeIngredient


def render_recipe_card(
    recipe: Recipe,
    ingredients: list[RecipeIngredient],
    ingredient_names: dict[UUID, str],
) -> None:
    """1件のRecipeをカード形式で表示する。"""
    with st.container(border=True):
        st.subheader(recipe.title)
        st.caption(format_datetime_jst(recipe.created_at))

        if recipe.total_calories is not None:
            st.markdown(
                f"**{recipe.total_calories:.0f}kcal** "
                f"(P: {recipe.protein_g:.0f}g, "
                f"F: {recipe.fat_g:.0f}g, "
                f"C: {recipe.carbohydrate_g:.0f}g)"
            )

        st.markdown("**材料**")
        for ingredient in ingredients:
            name = ingredient_names.get(ingredient.ingredient_id, "(不明)")
            st.markdown(f"- {name}: {ingredient.amount:g}{ingredient.unit}")

        st.markdown("**作り方**")
        st.write(recipe.instructions)
