"""MealService.estimate_nutritionのテスト。"""

from __future__ import annotations

import pytest

from health_intelligence.ai.errors import AIRateLimitError
from health_intelligence.ai.fake_provider import FakeAIProvider
from health_intelligence.ai.schemas import EstimatedMealNutrition
from health_intelligence.services.meal_service import MealService


def _make_service(make_fake_uow_factory, ai_provider: FakeAIProvider) -> MealService:
    uow_factory = make_fake_uow_factory()
    return MealService(uow_factory, ai_provider)


def test_estimate_nutrition_returns_ai_provider_result(make_fake_uow_factory) -> None:
    fixed = EstimatedMealNutrition(
        calories=350.0, protein_g=18.0, fat_g=10.0, carbohydrate_g=40.0
    )
    ai_provider = FakeAIProvider(fixed_meal_nutrition=fixed)
    service = _make_service(make_fake_uow_factory, ai_provider)

    result = service.estimate_nutrition("納豆1パック、ご飯茶碗1杯")

    assert result == fixed
    assert ai_provider.call_count == 1


def test_estimate_nutrition_caches_identical_description(make_fake_uow_factory) -> None:
    ai_provider = FakeAIProvider()
    service = _make_service(make_fake_uow_factory, ai_provider)

    service.estimate_nutrition("鶏むね肉のサラダ")
    service.estimate_nutrition("鶏むね肉のサラダ")

    assert ai_provider.call_count == 1


def test_estimate_nutrition_propagates_ai_provider_error(make_fake_uow_factory) -> None:
    ai_provider = FakeAIProvider(next_error=AIRateLimitError("rate limited"))
    service = _make_service(make_fake_uow_factory, ai_provider)

    with pytest.raises(AIRateLimitError):
        service.estimate_nutrition("味噌汁")
