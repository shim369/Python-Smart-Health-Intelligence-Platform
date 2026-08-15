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
from health_intelligence.ai.protocols import AIProvider
from health_intelligence.ai.schemas import (
    GeneratedRecipe,
    GeneratedRecipeIngredient,
    RecipeInput,
)

__all__ = [
    "AIProvider",
    "AIProviderError",
    "AIRateLimitError",
    "AIServiceUnavailableError",
    "AITimeoutError",
    "AIValidationError",
    "FakeAIProvider",
    "GeneratedRecipe",
    "GeneratedRecipeIngredient",
    "RecipeInput",
]
