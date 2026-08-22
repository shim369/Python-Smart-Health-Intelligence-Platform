"""AuthSessionStateのテスト。"""

from __future__ import annotations

from uuid import uuid4

import pytest

from health_intelligence.auth.session_state import AuthSessionState


@pytest.fixture
def state() -> AuthSessionState:
    return AuthSessionState({})


def test_initialize_sets_defaults(state: AuthSessionState) -> None:
    state.initialize()

    assert state.is_authenticated is False
    assert state.user_id is None


def test_require_user_id_raises_when_unauthenticated(
    state: AuthSessionState,
) -> None:
    state.initialize()

    with pytest.raises(RuntimeError):
        state.require_user_id()


def test_login_sets_authenticated_and_user_id(state: AuthSessionState) -> None:
    user_id = uuid4()

    state.login(user_id)

    assert state.is_authenticated is True
    assert state.require_user_id() == user_id


def test_logout_resets_state(state: AuthSessionState) -> None:
    state.login(uuid4())

    state.logout()

    assert state.is_authenticated is False
    assert state.user_id is None
