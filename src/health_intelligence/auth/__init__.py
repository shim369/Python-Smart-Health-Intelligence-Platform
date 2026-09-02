"""Auth Layer。

Google OAuth(OIDC)による認証はStreamlit標準の`st.login()` / `st.user` /
`st.logout()`に一本化する。ここではStreamlit本体に依存しない、
Session State管理と許可リスト判定のみを扱う。
"""

from health_intelligence.auth.allowlist import is_email_allowed, parse_allowed_emails
from health_intelligence.auth.session_keys import SessionKey
from health_intelligence.auth.session_state import AuthSessionState

__all__ = [
    "AuthSessionState",
    "SessionKey",
    "is_email_allowed",
    "parse_allowed_emails",
]
