"""SqlAlchemyによる`UserRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from health_intelligence.database.schema import UserORM
from health_intelligence.domain.models import User
from health_intelligence.logging_config import get_logger
from health_intelligence.repositories.errors import DuplicateKeyError

logger = get_logger(__name__)


def _to_domain(orm: UserORM) -> User:
    return User(
        user_id=orm.id,
        email=orm.email,
        display_name=orm.display_name,
        created_at=orm.created_at,
    )


def _to_orm(user: User) -> UserORM:
    return UserORM(
        id=user.user_id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
    )


class SqlAlchemyUserRepository:
    """`repositories.protocols.UserRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        orm = self._session.get(UserORM, user_id)
        return _to_domain(orm) if orm is not None else None

    def get_by_email(self, email: str) -> User | None:
        stmt = select(UserORM).where(UserORM.email == email)
        orm = self._session.scalars(stmt).first()
        return _to_domain(orm) if orm is not None else None

    def add(self, user: User) -> None:
        """Userを追加する。

        `flush()`でSQLを即座に発行し、この呼び出し内で一意制約違反
        (メールアドレスの重複)を検知できるようにする。`flush()`は
        commitではないため、トランザクション境界(UnitOfWork)には
        影響しない。

        `Authenticator.register()`は事前に`get_by_email`で重複を
        チェックしているが、同時に2件の登録リクエストが来た場合の
        競合状態(TOCTOU)を防ぐため、DB制約違反もここで検知する。
        """
        try:
            self._session.add(_to_orm(user))
            self._session.flush()
        except IntegrityError as e:
            logger.warning("duplicate user registration attempt: email=%s", user.email)
            raise DuplicateKeyError(f"email already exists: {user.email}") from e
