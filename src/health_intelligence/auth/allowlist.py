"""Google OAuthログインの許可リスト(ALLOWED_EMAILS)判定。

Streamlit本体(`st.secrets`)には依存しない純粋なロジックとして切り出し、
Unit Testを容易にする。
"""

from __future__ import annotations


def parse_allowed_emails(raw: str) -> frozenset[str]:
    """カンマ区切りの許可リスト文字列を、小文字化したメールアドレスの集合に変換する。"""
    return frozenset(email.strip().lower() for email in raw.split(",") if email.strip())


def is_email_allowed(email: str, allowed_emails: frozenset[str]) -> bool:
    """許可リストに基づき、ログインを許可するかどうかを判定する。

    許可リストが空(未設定)の場合は誰でも許可する。
    """
    if not allowed_emails:
        return True
    return email.lower() in allowed_emails
