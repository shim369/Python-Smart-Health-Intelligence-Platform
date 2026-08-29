"""SqlAlchemyによる`UserCredentialRepository`実装。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from health_intelligence.database.schema import UserCredentialORM


class SqlAlchemyUserCredentialRepository:
    """`repositories.protocols.UserCredentialRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_password_hash(self, user_id: UUID) -> str | None:
        orm = self._session.get(UserCredentialORM, user_id)
        return orm.password_hash if orm is not None else None

    def set_password_hash(self, user_id: UUID, password_hash: str) -> None:
        orm = self._session.get(UserCredentialORM, user_id)
        if orm is not None:
            orm.password_hash = password_hash
        else:
            self._session.add(UserCredentialORM(user_id=user_id, password_hash=password_hash))
