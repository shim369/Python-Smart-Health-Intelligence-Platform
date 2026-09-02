"""UserServiceのテスト。"""

from __future__ import annotations

from health_intelligence.services.user_service import UserService


def test_get_or_create_user_creates_new_user_when_not_found(
    make_fake_uow_factory, fake_user_repo
) -> None:
    uow_factory = make_fake_uow_factory(users=fake_user_repo)
    service = UserService(uow_factory)

    user = service.get_or_create_user(email="taro@example.com", display_name="Taro")

    assert user.email == "taro@example.com"
    assert user.display_name == "Taro"
    assert fake_user_repo.get_by_email("taro@example.com") == user


def test_get_or_create_user_returns_existing_user(make_fake_uow_factory, fake_user_repo) -> None:
    uow_factory = make_fake_uow_factory(users=fake_user_repo)
    service = UserService(uow_factory)
    first = service.get_or_create_user(email="taro@example.com", display_name="Taro")

    second = service.get_or_create_user(email="taro@example.com", display_name="Different Name")

    assert second.user_id == first.user_id
    assert second.display_name == "Taro"
