"""ブラウザ更新後もログイン状態を復元するためのSession Token Store。

Streamlitの`st.session_state`はブラウザの再接続(タブの再読み込み等)で
失われるため、URLのクエリパラメータに乗せられるランダムトークンを
発行し、サーバー側でトークン→user_idの対応を保持する
(requirements.md 12章、architecture.md Section 9のSession State
Architectureを補完する仕組み)。

現状はプロセスメモリ上の実装であり、以下の制約を許容している。

- Streamlitプロセスの再起動でセッションは失われる
- 複数プロセス/インスタンスにスケールアウトする場合は共有できない
  (Streamlit Community Cloud等、単一プロセス運用を前提とした簡易実装)
- トークンをURLへ乗せるため、ブラウザ履歴やリファラ経由で漏洩する
  リスクがある

より厳密なセッション管理(httponly Cookie、DB/Redisでの永続化)は
Phase 9以降で必要に応じて検討する。
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from uuid import UUID

_DEFAULT_TTL_SECONDS = 60 * 60 * 24 * 7
"""トークンの有効期限(秒)。デフォルト7日間。"""


@dataclass
class _Entry:
    user_id: UUID
    expires_at: float


class SessionTokenStore:
    """トークン文字列とuser_idの対応を保持するプロセス内ストア。"""

    def __init__(self, ttl_seconds: float = _DEFAULT_TTL_SECONDS) -> None:
        self._ttl_seconds = ttl_seconds
        self._entries: dict[str, _Entry] = {}

    def issue(self, user_id: UUID) -> str:
        """新しいトークンを発行する。"""
        token = secrets.token_urlsafe(32)
        self._entries[token] = _Entry(
            user_id=user_id, expires_at=time.time() + self._ttl_seconds
        )
        return token

    def resolve(self, token: str) -> UUID | None:
        """トークンからuser_idを引く。期限切れ・不明なトークンはNoneを返す。"""
        entry = self._entries.get(token)
        if entry is None:
            return None
        if entry.expires_at < time.time():
            del self._entries[token]
            return None
        return entry.user_id

    def revoke(self, token: str) -> None:
        """トークンを無効化する(ログアウト時)。"""
        self._entries.pop(token, None)
