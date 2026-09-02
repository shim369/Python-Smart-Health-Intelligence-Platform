"""ログインページ。

未認証時に`streamlit_app.py`のルーターから唯一表示されるページ。
Googleアカウントでのログイン(`st.login()`)ボタンを表示するのみで、
ログイン成功後のUser取得/作成・許可リストチェックは`streamlit_app.py`側で行う。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402
from i18n import t  # noqa: E402

st.title(":material/login: Smart Health Intelligence Platform")

if not st.user.get("is_logged_in", False):
    st.button(t("Googleでログイン"), on_click=st.login, type="primary")
    st.stop()
