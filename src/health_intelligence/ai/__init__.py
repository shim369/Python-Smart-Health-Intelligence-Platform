"""AI Layer。

外部AIサービス(Gemini等)への依存をProvider Patternで抽象化する。
Service層は`AIProvider` Protocolにのみ依存し、具体的な実装
(GeminiProvider / FakeAIProvider)には依存しない。
"""

from health_intelligence.ai.errors import (
    AIProviderError,
    AIRateLimitError,
    AIServiceUnavailableError,
    AITimeoutError,
    AIValidationError,
)
from health_intelligence.ai.fake_provider import FakeAIProvider
from health_intelligence.ai.gemini_provider import GeminiProvider
from health_intelligence.ai.protocols import AIProvider
from health_intelligence.ai.retry_policy import (
    DEFAULT_RETRY_POLICY,
    RETRYABLE_ERRORS,
    RetryPolicy,
)
from health_intelligence.ai.schemas import (
    GeneratedRecipe,
    GeneratedRecipeIngredient,
    RecipeInput,
)

__all__ = [
    "DEFAULT_RETRY_POLICY",
    "RETRYABLE_ERRORS",
    "AIProvider",
    "AIProviderError",
    "AIRateLimitError",
    "AIServiceUnavailableError",
    "AITimeoutError",
    "AIValidationError",
    "FakeAIProvider",
    "GeminiProvider",
    "GeneratedRecipe",
    "GeneratedRecipeIngredient",
    "RecipeInput",
    "RetryPolicy",
]
