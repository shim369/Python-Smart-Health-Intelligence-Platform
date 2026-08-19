"""Authenticator。

Email + Passwordによるユーザー登録・認証を担当する。

`register()`は User(識別情報)と UserCredential(パスワードハッシュ)
という複数Repositoryにまたがる書き込みを1つのUnitOfWorkで行う
(architecture.md Section 15 Unit of Workの実例)。
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from health_intelligence.auth.password_hashing import hash_password, verify_password
from health_intelligence.domain.models import User
from health_intelligence.repositories.unit_of_work import UnitOfWork


class EmailAlreadyRegisteredError(Exception):
    """登録しようとしたメールアドレスが既に使われている場合の例外。"""


class Authenticator:
    """Email + Passwordによるユーザー登録・認証を担当する。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def register(self, *, email: str, display_name: str, password: str) -> User:
        """新規ユーザーを登録する。

        メールアドレスが既に登録済みの場合は`EmailAlreadyRegisteredError`
        を送出する。
        """
        with self._uow_factory() as uow:
            if uow.users.get_by_email(email) is not None:
                raise EmailAlreadyRegisteredError(email)

            user = User(
                user_id=uuid4(),
                email=email,
                display_name=display_name,
                created_at=datetime.now(UTC),
            )
            uow.users.add(user)
            uow.user_credentials.set_password_hash(
                user.user_id, hash_password(password)
            )
            uow.commit()
            return user

    def authenticate(self, *, email: str, password: str) -> User | None:
        """認証に成功すればUserを、失敗すればNoneを返す。

        ユーザーが存在しない場合とパスワードが違う場合を区別せず
        Noneを返す(アカウントの存在有無を推測させないため)。
        """
        with self._uow_factory() as uow:
            user = uow.users.get_by_email(email)
            if user is None:
                return None

            password_hash = uow.user_credentials.get_password_hash(user.user_id)
            if password_hash is None:
                return None

            if not verify_password(password, password_hash):
                return None

            return user
