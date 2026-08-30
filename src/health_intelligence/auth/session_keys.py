"""Streamlit Session Stateで使うキーの定義。

architecture.md Section 9 Session State Architecture:
主な状態としてauthenticated / user_idを管理する。文字列リテラルを
直書きせず、Enumとして集約することでtypoによる事故を防ぐ。
"""

from __future__ import annotations

from enum import StrEnum


class SessionKey(StrEnum):
    """`st.session_state`に格納する値のキー。"""

    AUTHENTICATED = "authenticated"
    USER_ID = "user_id"
    LOCALE = "locale"
