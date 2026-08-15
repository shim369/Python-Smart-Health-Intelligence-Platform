"""Auth Layer。

Streamlit Session Stateを利用した認証状態の管理を担当する。
認証方式そのもの(ログイン処理・パスワード検証等)はPhase 4A(認証PoC)
で別途設計する。ここではSession State Architectureの骨格のみを扱う。
"""

from health_intelligence.auth.session_keys import SessionKey
from health_intelligence.auth.session_state import AuthSessionState

__all__ = ["AuthSessionState", "SessionKey"]
