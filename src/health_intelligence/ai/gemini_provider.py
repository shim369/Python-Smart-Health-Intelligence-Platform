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
from typing import TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from health_intelligence.ai.errors import (
    AIProviderError,
    AIRateLimitError,
    AIServiceUnavailableError,
    AITimeoutError,
    AIValidationError,
)
from health_intelligence.ai.retry_policy import DEFAULT_RETRY_POLICY, RetryPolicy
from health_intelligence.ai.schemas import (
    EstimatedMealNutrition,
    GeneratedRecipe,
    MealNutritionInput,
    RecipeInput,
)
from health_intelligence.logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_MODEL = "gemini-3.6-flash"
"""使用するGeminiモデル名。モデルの世代交代が早いため、実際に使う際は
最新の推奨モデル名を確認して更新すること。"""

_ResponseSchemaT = TypeVar("_ResponseSchemaT", bound=BaseModel)


def _build_recipe_prompt(recipe_input: RecipeInput) -> str:
    lines = [
        "以下の食材を使ったレシピを1件、日本語で提案してください。",
        f"食材: {', '.join(recipe_input.ingredient_names)}",
        "調理方法は電子レンジのみを使う前提にしてください"
        "(コンロ・オーブン・フライパンでの加熱は使わないでください)。",
        "タイトルは料理名のみとし、「レンジで簡単」「お手軽」「クイック」のような"
        "調理方法や難易度を煽る修飾語は付けないでください。",
        "material(材料)に記載した分量全体でのおおよその推定カロリー(kcal)と、"
        "タンパク質・脂質・炭水化物の推定量(g)も算出して含めてください。"
        "厳密な栄養計算ではなく目安で構いません。",
    ]
    if recipe_input.dietary_preference:
        lines.append(f"食事制限・好み: {recipe_input.dietary_preference}")
    if recipe_input.calorie_target is not None:
        lines.append(f"目標カロリー: 約{recipe_input.calorie_target:.0f}kcal")
    return "\n".join(lines)


def _build_meal_nutrition_prompt(meal_input: MealNutritionInput) -> str:
    return "\n".join(
        [
            "以下の食事内容から、おおよその推定カロリー(kcal)と、"
            "タンパク質・脂質・炭水化物の推定量(g)を算出してください。",
            "厳密な栄養計算ではなく目安で構いません。"
            "分量が曖昧な場合は一般的な1食分の量として見積もってください。",
            f"食事内容: {meal_input.description}",
        ]
    )


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
        prompt = _build_recipe_prompt(recipe_input)
        return self._call_with_retry(prompt, GeneratedRecipe)

    def estimate_meal_nutrition(self, meal_input: MealNutritionInput) -> EstimatedMealNutrition:
        prompt = _build_meal_nutrition_prompt(meal_input)
        return self._call_with_retry(prompt, EstimatedMealNutrition)

    def _call_with_retry(
        self, prompt: str, response_schema: type[_ResponseSchemaT]
    ) -> _ResponseSchemaT:
        last_error: Exception | None = None

        for attempt in range(1, self._retry_policy.max_attempts + 1):
            try:
                return self._call_once(prompt, response_schema)
            except (AIRateLimitError, AIServiceUnavailableError) as e:
                last_error = e
                if attempt == self._retry_policy.max_attempts:
                    logger.warning(
                        "Gemini API call failed after %d attempts: %s",
                        attempt,
                        e,
                    )
                    raise
                logger.info(
                    "Gemini API call failed (attempt %d/%d), retrying: %s",
                    attempt,
                    self._retry_policy.max_attempts,
                    e,
                )
                self._wait_before_retry(attempt)

        # 最終試行で必ずreturnかraiseするため実際には到達しないが、
        # 型チェッカー向けに明示しておく。
        assert last_error is not None
        raise last_error

    def _call_once(self, prompt: str, response_schema: type[_ResponseSchemaT]) -> _ResponseSchemaT:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
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
        if not isinstance(parsed, response_schema):
            raise AIValidationError(
                f"Geminiのレスポンスを{response_schema.__name__}として解釈できませんでした"
            )
        return parsed

    def _wait_before_retry(self, attempt: int) -> None:
        base_delay = self._retry_policy.delay_seconds(attempt)
        jitter_ratio = self._retry_policy.jitter_ratio
        delay = base_delay * random.uniform(1 - jitter_ratio, 1 + jitter_ratio)
        time.sleep(delay)
