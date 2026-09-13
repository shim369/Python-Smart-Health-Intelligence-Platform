"""Recipe Cardコンポーネント。"""

from __future__ import annotations

from collections.abc import Callable
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
    on_delete: Callable[[], None] | None = None,
) -> None:
    """1件のRecipeをカード形式で表示する。

    as_expander=Trueの場合、タイトルをクリックして開閉できるアコーディオン
    (st.expander)として表示する。
    on_deleteを渡した場合(as_expander=True時のみ有効)、タイトルの右端に
    削除ボタンを表示し、クリック確定(2回目クリックで確定)するとon_delete
    を呼び出す。
    """
    card_key = f"recipe-card-{key_prefix}{recipe.recipe_id}"

    if as_expander and on_delete is not None:
        title_col, delete_col = st.columns([0.88, 0.12])
        with title_col:
            container = st.expander(recipe.title, expanded=expanded, key=card_key)
        confirm_key = f"recipe-delete-confirming-{key_prefix}{recipe.recipe_id}"
        is_confirming = st.session_state.get(confirm_key, False)
        with delete_col:
            if is_confirming:
                if st.button(
                    t("本当に削除?"),
                    key=f"recipe-delete-confirm-{key_prefix}{recipe.recipe_id}",
                    type="primary",
                    help=t("クリックすると削除します"),
                ):
                    st.session_state[confirm_key] = False
                    on_delete()
            elif st.button(
                ":material/delete:",
                key=f"recipe-delete-{key_prefix}{recipe.recipe_id}",
                help=t("削除"),
            ):
                st.session_state[confirm_key] = True
                st.rerun()
    else:
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
