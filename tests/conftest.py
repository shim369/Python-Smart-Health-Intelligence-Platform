"""pytest共通フィクスチャ。

実DB・実AI APIを使わずにService/Authenticator層のロジックを検証する
ための、最小限のFake Repository/UnitOfWorkを提供する。
"""

from __future__ import annotations

from typing import TypeVar
from uuid import UUID

import pytest
from dotenv import load_dotenv

from health_intelligence.domain.models import User

load_dotenv()

T = TypeVar("T")


class FakeUserRepository:
    """`UserRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self) -> None:
        self._by_email: dict[str, User] = {}
        self._by_id: dict[UUID, User] = {}

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email)

    def add(self, user: User) -> None:
        self._by_email[user.email] = user
        self._by_id[user.user_id] = user


class FakeUserCredentialRepository:
    """`UserCredentialRepository` Protocolを満たすインメモリ実装。"""

    def __init__(self) -> None:
        self._hashes: dict[UUID, str] = {}

    def get_password_hash(self, user_id: UUID) -> str | None:
        return self._hashes.get(user_id)

    def set_password_hash(self, user_id: UUID, password_hash: str) -> None:
        self._hashes[user_id] = password_hash


class FakeListRepository[T]:
    """`list_by_user`のみを提供する汎用Fake Repository。

    RecommendationServiceのテスト等、`list_by_user`しか使わない
    Repositoryを毎回書くのを避けるための共通実装。
    """

    def __init__(self, items: list[T]) -> None:
        self._items = items

    def list_by_user(self, user_id: UUID) -> list[T]:
        return self._items


class FakeUnitOfWork:
    """テストで使うRepositoryだけを動的に持たせるUnitOfWork。

    UnitOfWork Protocolはstructural typing(Protocol)のため、実行時に
    使わない属性が存在しなくても、そのテストが触れない限り問題ない。
    """

    def __init__(self, **repositories: object) -> None:
        for name, repo in repositories.items():
            setattr(self, name, repo)

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


@pytest.fixture
def fake_user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def fake_credential_repo() -> FakeUserCredentialRepository:
    return FakeUserCredentialRepository()


@pytest.fixture
def make_fake_uow_factory():
    """任意のRepositoryキーワード引数からFakeUnitOfWork factoryを組み立てる。

    使用例: `make_fake_uow_factory(users=fake_user_repo, ...)`
    """

    def _factory(**repositories: object):
        return lambda: FakeUnitOfWork(**repositories)

    return _factory


@pytest.fixture
def fake_list_repository_factory():
    """`FakeListRepository`のコンストラクタをそのまま返すフィクスチャ。"""
    return FakeListRepository
