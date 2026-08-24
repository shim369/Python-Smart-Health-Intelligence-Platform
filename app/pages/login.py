"""ログイン/新規登録ページ。

未認証時に`streamlit_app.py`のルーターから唯一表示されるページ。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402
from services import get_authenticator, get_session_token_store  # noqa: E402

from health_intelligence.auth import (  # noqa: E402
    AuthSessionState,
    EmailAlreadyRegisteredError,
)

auth_state = AuthSessionState(st.session_state)
auth_state.initialize()


def _login_and_persist(user_id) -> None:  # noqa: ANN001
    """Session Stateへログインし、ブラウザ更新に備えてトークンも発行する。"""
    auth_state.login(user_id)
    token = get_session_token_store().issue(user_id)
    st.query_params["session_token"] = token


st.title("Smart Health Intelligence Platform")

login_tab, register_tab = st.tabs(["ログイン", "新規登録"])

with login_tab:
    with st.form("login_form"):
        email = st.text_input("メールアドレス", key="login_email")
        password = st.text_input("パスワード", type="password", key="login_password")
        submitted = st.form_submit_button("ログイン")

    if submitted:
        authenticator = get_authenticator()
        user = authenticator.authenticate(email=email, password=password)
        if user is None:
            st.error("メールアドレスまたはパスワードが正しくありません。")
        else:
            _login_and_persist(user.user_id)
            st.rerun()

with register_tab:
    with st.form("register_form"):
        reg_email = st.text_input("メールアドレス", key="register_email")
        reg_display_name = st.text_input("表示名", key="register_display_name")
        reg_password = st.text_input(
            "パスワード", type="password", key="register_password"
        )
        register_submitted = st.form_submit_button("登録する")

    if register_submitted:
        authenticator = get_authenticator()
        try:
            user = authenticator.register(
                email=reg_email,
                display_name=reg_display_name,
                password=reg_password,
            )
        except EmailAlreadyRegisteredError:
            st.error("このメールアドレスは既に登録されています。")
        else:
            _login_and_persist(user.user_id)
            st.rerun()
