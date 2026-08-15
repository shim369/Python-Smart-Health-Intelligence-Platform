"""AI Provider関連の例外定義。

architecture.md Section 10.2 AI Error Handling:
Timeout / 429 Rate Limit / 503 Service Unavailable / Validation Error /
その他API Errorを想定する。429・503はRetry対象、Validation Errorおよび
その他の一部エラーはRetry対象外とする。

Retry対象かどうかを型で区別できるよう、例外クラスを分ける。
実際のRetry(指数バックオフ)はGeminiProvider等、各実装の責務とする。
"""

from __future__ import annotations


class AIProviderError(Exception):
    """AI Provider呼び出しに関する例外の基底クラス。"""


class AITimeoutError(AIProviderError):
    """AI APIがTimeoutした場合の例外。Retry対象外。"""


class AIRateLimitError(AIProviderError):
    """429 Rate Limitを受け取った場合の例外。Retry対象。"""


class AIServiceUnavailableError(AIProviderError):
    """503 Service Unavailableを受け取った場合の例外。Retry対象。"""


class AIValidationError(AIProviderError):
    """AIレスポンスがSchema Validationに失敗した場合の例外。Retry対象外。"""
