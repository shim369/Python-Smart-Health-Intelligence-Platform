"""UserService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.domain.enums import Locale
from health_intelligence.domain.models import User
from health_intelligence.repositories.unit_of_work import UnitOfWork


class UserService:
    """Userに関するユースケースを担当するService。

    UnitOfWorkの具体的な実装(SQLAlchemy等)には直接依存しない。
    呼び出しごとに新しいトランザクション境界を作れるよう、UnitOfWork
    そのものではなくfactory関数を受け取る。
    """

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def get_user(self, user_id: UUID) -> User | None:
        with self._uow_factory() as uow:
            return uow.users.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        with self._uow_factory() as uow:
            return uow.users.get_by_email(email)

    def register_user(self, user: User) -> None:
        """新規ユーザーを登録する。

        メールアドレスの一意性検証など認証まわりの詳細は
        Phase 4A(認証PoC)/Phase 7(認証統合)で確定する。
        """
        with self._uow_factory() as uow:
            uow.users.add(user)
            uow.commit()

    def update_locale(self, user_id: UUID, locale: Locale) -> None:
        with self._uow_factory() as uow:
            uow.users.update_locale(user_id, locale)
            uow.commit()
