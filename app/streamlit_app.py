"""Streamlitアプリのエントリーポイント(ルーター)。

`st.navigation()` + `st.Page()`により、ファイル名(ASCII)と
サイドバー表示名(日本語)を分離する。未認証時はログインページのみを
ナビゲーションに含めることで、実質的な認証ガードとしても機能させる
(architecture.md Section 9.1 Session Lifecycle)。

ブラウザ更新で`st.session_state`が失われた場合に備え、URLの
`session_token`クエリパラメータからログイン状態を復元する
(auth/session_token_store.py参照)。

各ページ内の`auth_guard.require_login()`は、直接URLアクセス等に
対する防御として残す(多層防御)。
"""

from __future__ import annotations

import streamlit as st
from services import get_session_token_store

from health_intelligence.auth import AuthSessionState
from health_intelligence.config import load_environment
from health_intelligence.logging_config import configure_logging

load_environment()
configure_logging()

# ブラウザのタブ情報
st.set_page_config(page_title="Smart Health Intelligence Platform")

# 全ページのタイトルサイズ（h1）を一括で28pxに調整するCSSだけを適用
st.markdown(
    """
    <style>
    h1 {
        font-size: clamp(18px, 4vw, 28px) !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

auth_state = AuthSessionState(st.session_state)
auth_state.initialize()

if not auth_state.is_authenticated:
    token = st.query_params.get("session_token")
    if token:
        user_id = get_session_token_store().resolve(token)
        if user_id is not None:
            auth_state.login(user_id)

login_page = st.Page("pages/login.py", title="ログイン")

if not auth_state.is_authenticated:
    pg = st.navigation([login_page])
else:
    dashboard_page = st.Page("pages/dashboard.py", title="ダッシュボード", default=True)
    log_entry_page = st.Page("pages/log_entry.py", title="ログ入力")
    recipe_page = st.Page("pages/recipe.py", title="レシピ")
    pg = st.navigation([dashboard_page, log_entry_page, recipe_page])

pg.run()
