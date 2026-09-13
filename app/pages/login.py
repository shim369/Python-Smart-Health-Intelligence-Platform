"""ログインページ。

未認証時に`streamlit_app.py`のルーターから唯一表示されるページ。
上部にヘッダー(左端: ロゴ、右端: ログインボタン)、その下にヒーロー画像を
配置する。Googleアカウントでのログイン(`st.login()`)ボタンを表示するのみで、
ログイン成功後のUser取得/作成・許可リストチェックは`streamlit_app.py`側で行う。

ログイン画面には言語切り替えを置かない。`st.login()`はOAuthプロバイダを
経由するリダイレクトを伴い、戻ってきた時点でst.session_stateがリセット
されるため、ここでの切り替えをログイン後まで引き継ぐことができない
(streamlit_app.pyのdetect_browser_locale()参照)。そのためログイン画面の
文言は常に固定で英語表示にする。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

_HERO_IMAGE = Path(__file__).resolve().parents[2] / "docs" / "images" / "hero-trajectory-dashed.svg"

# ヒーロー画像はカード調の角丸+シャドウを付け、他要素(フォーム等)の
# 装飾(streamlit_app.py)と見た目を揃える。
st.markdown(
    """
    <style>
    [class*="st-key-login-hero"] [data-testid="stImage"] img {
        border-radius: 24px;
        box-shadow: 0 8px 30px rgba(15, 23, 42, 0.10);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
    st.markdown("### :material/monitor_heart: Smart Health Intelligence Platform")
    if not st.user.get("is_logged_in", False):
        st.button("Login", on_click=st.login, type="primary")

with st.container(key="login-hero"):
    st.image(str(_HERO_IMAGE), width="stretch")

if not st.user.get("is_logged_in", False):
    st.stop()
