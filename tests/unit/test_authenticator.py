"""Authenticatorのテスト。"""

from __future__ import annotations

import pytest

from health_intelligence.auth.authenticator import (
    Authenticator,
    EmailAlreadyRegisteredError,
)


@pytest.fixture
def authenticator(make_fake_uow_factory, fake_user_repo, fake_credential_repo):
    uow_factory = make_fake_uow_factory(users=fake_user_repo, user_credentials=fake_credential_repo)
    return Authenticator(uow_factory)


def test_register_and_authenticate(authenticator: Authenticator) -> None:
    user = authenticator.register(email="taro@example.com", display_name="Taro", password="hunter2")

    authed = authenticator.authenticate(email="taro@example.com", password="hunter2")

    assert authed is not None
    assert authed.user_id == user.user_id


def test_duplicate_email_is_rejected(authenticator: Authenticator) -> None:
    authenticator.register(email="taro@example.com", display_name="Taro", password="x")

    with pytest.raises(EmailAlreadyRegisteredError):
        authenticator.register(email="taro@example.com", display_name="Taro2", password="y")


def test_wrong_password_is_rejected(authenticator: Authenticator) -> None:
    authenticator.register(email="taro@example.com", display_name="Taro", password="correct")

    assert authenticator.authenticate(email="taro@example.com", password="wrong") is None


def test_unknown_user_is_rejected(authenticator: Authenticator) -> None:
    assert authenticator.authenticate(email="nobody@example.com", password="x") is None


def test_race_condition_at_db_level_is_translated_to_public_error(
    make_fake_uow_factory,
) -> None:
    """`get_by_email`の事前チェックをすり抜けても、DB制約違反
    (`DuplicateKeyError`)が`EmailAlreadyRegisteredError`へ変換される
    ことを確認する(2件の登録リクエストがほぼ同時に来た場合を想定)。
    """
    from health_intelligence.repositories.errors import DuplicateKeyError

    class RaceyUserRepo:
        def get_by_id(self, user_id):
            return None

        def get_by_email(self, email):
            return None  # 事前チェックをすり抜ける

        def add(self, user):
            raise DuplicateKeyError("race condition simulated")

    class NoOpCredentialRepo:
        def get_password_hash(self, user_id):
            return None

        def set_password_hash(self, user_id, password_hash):
            pass

    uow_factory = make_fake_uow_factory(
        users=RaceyUserRepo(), user_credentials=NoOpCredentialRepo()
    )
    authenticator = Authenticator(uow_factory)

    with pytest.raises(EmailAlreadyRegisteredError):
        authenticator.register(email="race@example.com", display_name="Race", password="x")
