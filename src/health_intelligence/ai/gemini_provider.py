"""GeminiProvider。

`AIProvider` Protocolを満たすGemini API実装(architecture.md
Section 10 AI Architecture)。Retry/Timeoutはai/retry_policy.pyの
`RetryPolicy`に従う。google-genai SDK組み込みのRetryは無効化し
(`HttpRetryOptions(attempts=1)`)、自前のRetryループのみを使うことで
二重リトライによる待ち時間の肥大を避ける。

注意: google-genai SDKが実際にどの例外をどの条件で送出するかは
SDKバージョンにより変わりうる。ここでの分類(429→AIRateLimitError、
503→AIServiceUnavailableError、その他→AIProviderError)は
`google.genai.errors.APIError`の`.code`属性に基づく一般的な実装
だが、実際にAPIキーで疎通確認した際にズレがないか確認すること。
"""

from __future__ import annotations

import os
import random
import time

from google import genai
from google.genai import errors, types

from health_intelligence.ai.errors import (
    AIProviderError,
    AIRateLimitError,
    AIServiceUnavailableError,
    AITimeoutError,
    AIValidationError,
)
from health_intelligence.ai.retry_policy import DEFAULT_RETRY_POLICY, RetryPolicy
from health_intelligence.ai.schemas import GeneratedRecipe, RecipeInput

_DEFAULT_MODEL = "gemini-2.5-flash"
"""使用するGeminiモデル名。モデルの世代交代が早いため、実際に使う際は
最新の推奨モデル名を確認して更新すること。"""


def _build_prompt(recipe_input: RecipeInput) -> str:
    lines = [
        "以下の食材を使ったレシピを1件、日本語で提案してください。",
        f"食材: {', '.join(recipe_input.ingredient_names)}",
    ]
    if recipe_input.dietary_preference:
        lines.append(f"食事制限・好み: {recipe_input.dietary_preference}")
    if recipe_input.calorie_target is not None:
        lines.append(f"目標カロリー: 約{recipe_input.calorie_target:.0f}kcal")
    return "\n".join(lines)


class GeminiProvider:
    """`AIProvider` Protocolを満たすGemini API実装。"""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    ) -> None:
        resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_api_key:
            raise RuntimeError(
                "環境変数 GEMINI_API_KEY が設定されていません。"
                " ローカルでは.env、本番ではStreamlit Secretsで設定してください。"
            )

        self._model = model
        self._retry_policy = retry_policy
        self._client = genai.Client(
            api_key=resolved_api_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1),
                timeout=int(retry_policy.request_timeout_seconds * 1000),
            ),
        )

    def generate_recipe(self, recipe_input: RecipeInput) -> GeneratedRecipe:
        prompt = _build_prompt(recipe_input)
        last_error: Exception | None = None

        for attempt in range(1, self._retry_policy.max_attempts + 1):
            try:
                return self._call_once(prompt)
            except (AIRateLimitError, AIServiceUnavailableError) as e:
                last_error = e
                if attempt == self._retry_policy.max_attempts:
                    raise
                self._wait_before_retry(attempt)

        # 最終試行で必ずreturnかraiseするため実際には到達しないが、
        # 型チェッカー向けに明示しておく。
        assert last_error is not None
        raise last_error

    def _call_once(self, prompt: str) -> GeneratedRecipe:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeneratedRecipe,
                ),
            )
        except errors.APIError as e:
            code = getattr(e, "code", None)
            if code == 429:
                raise AIRateLimitError(str(e)) from e
            if code == 503:
                raise AIServiceUnavailableError(str(e)) from e
            raise AIProviderError(str(e)) from e
        except TimeoutError as e:
            raise AITimeoutError(str(e)) from e

        parsed = response.parsed
        if not isinstance(parsed, GeneratedRecipe):
            raise AIValidationError(
                "GeminiのレスポンスをGeneratedRecipeとして解釈できませんでした"
            )
        return parsed

    def _wait_before_retry(self, attempt: int) -> None:
        base_delay = self._retry_policy.delay_seconds(attempt)
        jitter_ratio = self._retry_policy.jitter_ratio
        delay = base_delay * random.uniform(1 - jitter_ratio, 1 + jitter_ratio)
        time.sleep(delay)
