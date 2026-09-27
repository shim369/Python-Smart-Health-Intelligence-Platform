"""許可リスト(ALLOWED_EMAILS)判定のテスト。"""

from __future__ import annotations

from health_intelligence.auth.allowlist import is_email_allowed, parse_allowed_emails


def test_parse_allowed_emails_trims_and_lowercases() -> None:
    parsed = parse_allowed_emails(" Taro@Example.com , hanako@example.com ,,")

    assert parsed == {"taro@example.com", "hanako@example.com"}


def test_parse_allowed_emails_empty_string_is_empty_set() -> None:
    assert parse_allowed_emails("") == frozenset()


def test_is_email_allowed_rejects_everyone_when_unset() -> None:
    assert is_email_allowed("anyone@example.com", frozenset()) is False


def test_is_email_allowed_passes_everyone_with_wildcard() -> None:
    allowed = parse_allowed_emails("*")

    assert is_email_allowed("anyone@example.com", allowed) is True


def test_is_email_allowed_matches_case_insensitively() -> None:
    allowed = frozenset({"taro@example.com"})

    assert is_email_allowed("Taro@Example.com", allowed) is True


def test_is_email_allowed_rejects_unlisted_email() -> None:
    allowed = frozenset({"taro@example.com"})

    assert is_email_allowed("other@example.com", allowed) is False
