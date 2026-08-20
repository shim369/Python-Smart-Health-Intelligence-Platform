"""Streamlitアプリのエントリーポイント(ルーター)。

`st.navigation()` + `st.Page()`により、ファイル名(ASCII)と
サイドバー表示名(日本語)を分離する。未認証時はログインページのみを
ナビゲーションに含めることで、実質的な認証ガードとしても機能させる
(architecture.md Section 9.1 Session Lifecycle)。

各ページ内の`auth_guard.require_login()`は、直接URLアクセス等に
対する防御として残す(多層防御)。
"""

from __future__ import annotations

import streamlit as st

from health_intelligence.auth import AuthSessionState

st.set_page_config(page_title="Smart Health Intelligence Platform", page_icon="🩺")

auth_state = AuthSessionState(st.session_state)
auth_state.initialize()

login_page = st.Page("pages/login.py", title="ログイン", icon="🔑")

if not auth_state.is_authenticated:
    pg = st.navigation([login_page])
else:
    dashboard_page = st.Page(
        "pages/dashboard.py", title="ダッシュボード", icon="📊", default=True
    )
    log_entry_page = st.Page("pages/log_entry.py", title="ログ入力", icon="📝")
    recipe_page = st.Page("pages/recipe.py", title="レシピ", icon="🍳")
    pg = st.navigation([dashboard_page, log_entry_page, recipe_page])

pg.run()
