"""AI Provider呼び出しのRetry/Timeout方針(数値)。

architecture.md Section 10.2 / requirements.md 10.4で定めた方針の
数値版。GeminiProvider(Phase 4B)はこの定数を用いてRetryを実装する。

FakeAIProviderは実際のRetryループを持たないため、この定数を直接は
使用しない(テストでは`next_error`による1回限りのエラー注入で十分)。
"""

from __future__ import annotations

from dataclasses import dataclass

from health_intelligence.ai.errors import AIRateLimitError, AIServiceUnavailableError


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """指数バックオフによるRetryの設定。"""

    max_attempts: int = 3
    """初回呼び出しを含む最大試行回数。"""

    base_delay_seconds: float = 1.0
    """1回目のRetry前に待機する基準秒数。"""

    backoff_multiplier: float = 2.0
    """試行ごとに待機時間を掛け合わせる倍率。"""

    jitter_ratio: float = 0.2
    """待機時間に加えるランダムなブレの割合(例: 0.2 = ±20%)。"""

    request_timeout_seconds: float = 20.0
    """1回の試行あたりのTimeout(秒)。"""

    def delay_seconds(self, attempt: int) -> float:
        """`attempt`回目(1始まり)のRetry前に待機する秒数を返す。

        Jitterを含まない基準値を返す。実装側(GeminiProvider)で
        `delay * random.uniform(1 - jitter_ratio, 1 + jitter_ratio)`
        のようにJitterを加える想定。
        """
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        return self.base_delay_seconds * (self.backoff_multiplier ** (attempt - 1))

    @property
    def worst_case_total_seconds(self) -> float:
        """全試行が失敗し続けた場合の最悪ケース総待ち時間(概算)。"""
        retry_count = self.max_attempts - 1
        total_delay = sum(self.delay_seconds(i + 1) for i in range(retry_count))
        return self.max_attempts * self.request_timeout_seconds + total_delay


DEFAULT_RETRY_POLICY = RetryPolicy()

RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    AIRateLimitError,
    AIServiceUnavailableError,
)
"""Retry対象の例外型。AITimeoutError/AIValidationErrorはここに含めない
(即座に失敗させ、無条件に再試行しない)。"""
