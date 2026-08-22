"""SessionTokenStoreのテスト。"""

from __future__ import annotations

import time
from uuid import uuid4

from health_intelligence.auth.session_token_store import SessionTokenStore


def test_issue_and_resolve() -> None:
    store = SessionTokenStore()
    user_id = uuid4()

    token = store.issue(user_id)

    assert store.resolve(token) == user_id


def test_revoke_invalidates_token() -> None:
    store = SessionTokenStore()
    token = store.issue(uuid4())

    store.revoke(token)

    assert store.resolve(token) is None


def test_expired_token_returns_none() -> None:
    store = SessionTokenStore(ttl_seconds=0.05)
    token = store.issue(uuid4())

    time.sleep(0.1)

    assert store.resolve(token) is None


def test_unknown_token_returns_none() -> None:
    store = SessionTokenStore()

    assert store.resolve("does-not-exist") is None
