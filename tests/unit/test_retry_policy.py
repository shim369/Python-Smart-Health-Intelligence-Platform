"""ai/retry_policy.pyのテスト。"""

from __future__ import annotations

import pytest

from health_intelligence.ai.errors import (
    AIRateLimitError,
    AIServiceUnavailableError,
    AITimeoutError,
    AIValidationError,
)
from health_intelligence.ai.retry_policy import DEFAULT_RETRY_POLICY, RETRYABLE_ERRORS


def test_default_policy_values() -> None:
    assert DEFAULT_RETRY_POLICY.max_attempts == 3
    assert DEFAULT_RETRY_POLICY.base_delay_seconds == 1.0
    assert DEFAULT_RETRY_POLICY.backoff_multiplier == 2.0
    assert DEFAULT_RETRY_POLICY.request_timeout_seconds == 60.0


def test_delay_seconds_follows_exponential_backoff() -> None:
    assert DEFAULT_RETRY_POLICY.delay_seconds(1) == 1.0
    assert DEFAULT_RETRY_POLICY.delay_seconds(2) == 2.0
    assert DEFAULT_RETRY_POLICY.delay_seconds(3) == 4.0


def test_delay_seconds_rejects_non_positive_attempt() -> None:
    with pytest.raises(ValueError):
        DEFAULT_RETRY_POLICY.delay_seconds(0)


def test_worst_case_total_seconds() -> None:
    # 3回 x 60秒 + (1秒 + 2秒) = 183秒
    assert DEFAULT_RETRY_POLICY.worst_case_total_seconds == pytest.approx(183.0)


def test_only_rate_limit_and_service_unavailable_are_retryable() -> None:
    assert AIRateLimitError in RETRYABLE_ERRORS
    assert AIServiceUnavailableError in RETRYABLE_ERRORS
    assert AITimeoutError not in RETRYABLE_ERRORS
    assert AIValidationError not in RETRYABLE_ERRORS
