"""UserService。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from health_intelligence.domain.enums import Locale
from health_intelligence.domain.models import User
from health_intelligence.repositories.errors import DuplicateKeyError
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
        """新規ユーザーを登録する。"""
        with self._uow_factory() as uow:
            uow.users.add(user)
            uow.commit()

    def get_or_create_user(self, *, email: str, display_name: str) -> User:
        """Google OAuthログイン成功時、メールアドレスをキーにUserを取得または新規作成する。

        `st.user.email`をキーに既存Userを検索し、無ければ自動作成する
        (docs/auth-migration-design.md 4.4)。パスワードは不要。

        事前チェック(`get_by_email`)をすり抜ける同時ログインの競合状態
        (TOCTOU)に備え、DB制約違反(`DuplicateKeyError`)時は新しい
        UnitOfWork(≒新しいSession)で改めて`get_by_email`を引き直す
        (DuplicateKeyError発生後のSessionは中断状態のため、同じUoW内では
        再利用できない)。
        """
        with self._uow_factory() as uow:
            user = uow.users.get_by_email(email)
            if user is not None:
                return user

            user = User(
                user_id=uuid4(),
                email=email,
                display_name=display_name,
                created_at=datetime.now(UTC),
            )
            try:
                uow.users.add(user)
                uow.commit()
            except DuplicateKeyError:
                pass
            else:
                return user

        with self._uow_factory() as uow:
            existing = uow.users.get_by_email(email)
            assert existing is not None
            return existing

    def update_locale(self, user_id: UUID, locale: Locale) -> None:
        with self._uow_factory() as uow:
            uow.users.update_locale(user_id, locale)
            uow.commit()
