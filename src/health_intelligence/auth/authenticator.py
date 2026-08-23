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
from health_intelligence.logging_config import get_logger
from health_intelligence.repositories.errors import DuplicateKeyError
from health_intelligence.repositories.unit_of_work import UnitOfWork

logger = get_logger(__name__)


class EmailAlreadyRegisteredError(Exception):
    """登録しようとしたメールアドレスが既に使われている場合の例外。"""


class Authenticator:
    """Email + Passwordによるユーザー登録・認証を担当する。"""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def register(self, *, email: str, display_name: str, password: str) -> User:
        """新規ユーザーを登録する。

        メールアドレスが既に登録済みの場合は`EmailAlreadyRegisteredError`
        を送出する。事前チェック(`get_by_email`)に加え、同時登録による
        競合状態に備え、DB制約違反(`DuplicateKeyError`)もここで
        `EmailAlreadyRegisteredError`へ変換する
        (repositories/sqlalchemy/user_repository.py参照)。
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
            try:
                uow.users.add(user)
                uow.user_credentials.set_password_hash(
                    user.user_id, hash_password(password)
                )
                uow.commit()
            except DuplicateKeyError as e:
                raise EmailAlreadyRegisteredError(email) from e

            return user

    def authenticate(self, *, email: str, password: str) -> User | None:
        """認証に成功すればUserを、失敗すればNoneを返す。

        ユーザーが存在しない場合とパスワードが違う場合を区別せず
        Noneを返す(アカウントの存在有無を推測させないため)。
        """
        with self._uow_factory() as uow:
            user = uow.users.get_by_email(email)
            if user is None:
                logger.info("login attempt for unknown email")
                return None

            password_hash = uow.user_credentials.get_password_hash(user.user_id)
            if password_hash is None:
                return None

            if not verify_password(password, password_hash):
                logger.info("failed login attempt: user_id=%s", user.user_id)
                return None

            return user
