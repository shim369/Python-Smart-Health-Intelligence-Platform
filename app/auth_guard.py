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

from health_intelligence.auth import AuthSessionState


def require_login() -> AuthSessionState:
    """未認証の場合はログインを促して描画を止める。認証済みなら
    サイドバーにログアウトボタンを表示する。"""
    auth_state = AuthSessionState(st.session_state)
    auth_state.initialize()

    if not auth_state.is_authenticated:
        st.warning("ログインしてください。")
        st.stop()

    with st.sidebar:
        if st.button("ログアウト"):
            auth_state.logout()
            st.rerun()

    return auth_state
