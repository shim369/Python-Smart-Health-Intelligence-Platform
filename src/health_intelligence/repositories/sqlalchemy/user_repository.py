"""SqlAlchemyによる`UserRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import UserORM
from health_intelligence.domain.models import User


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
        self._session.add(_to_orm(user))
