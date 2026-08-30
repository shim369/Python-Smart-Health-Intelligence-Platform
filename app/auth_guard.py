"""各ページの先頭で認証状態をチェックするヘルパー。

architecture.md Section 9 Session State Architecture:
`AuthSessionState`(auth/session_state.py)をStreamlitの
`st.session_state`にバインドして使う。

`streamlit_app.py`のst.navigation()ルーターが未認証時はログイン
ページしか表示しないため、通常はここでの未認証到達は起きない想定
だが、直接URLアクセス等への防御としてここでもチェックする
(多層防御)。
"""

from __future__ import annotations

import streamlit as st
from i18n import LOCALE_LABELS, t
from services import get_session_token_store, get_user_service

from health_intelligence.auth import AuthSessionState


def require_login() -> AuthSessionState:
    """未認証の場合はログインを促して描画を止める。認証済みなら
    サイドバーに言語切り替え・ログアウトボタンを表示する。"""
    auth_state = AuthSessionState(st.session_state)
    auth_state.initialize()

    if not auth_state.is_authenticated:
        st.warning(t("ログインしてください。"))
        st.stop()

    with st.sidebar:
        locales = list(LOCALE_LABELS)
        selected_locale = st.selectbox(
            t("言語"),
            options=locales,
            index=locales.index(auth_state.locale),
            format_func=lambda loc: LOCALE_LABELS[loc],
            key="locale_switcher",
            label_visibility="collapsed",
        )
        if selected_locale != auth_state.locale:
            auth_state.set_locale(selected_locale)
            get_user_service().update_locale(auth_state.require_user_id(), selected_locale)
            st.rerun()

        if st.button(t("ログアウト")):
            token = st.query_params.get("session_token")
            if token:
                get_session_token_store().revoke(token)
            st.query_params.clear()
            auth_state.logout()
            st.rerun()

    return auth_state
