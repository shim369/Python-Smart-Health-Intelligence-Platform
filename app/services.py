"""Streamlit側でServiceインスタンスを組み立てるヘルパー。

`st.cache_resource`により、DB接続やAI Providerなど状態を持つ
オブジェクトをStreamlitの再実行(rerun)間で使い回す
(毎回の再実行でSQLAlchemy Engineを作り直さないようにするため)。
"""

from __future__ import annotations

import streamlit as st

from health_intelligence.auth import Authenticator, SessionTokenStore
from health_intelligence.config import get_ai_provider
from health_intelligence.repositories.sqlalchemy import build_uow_factory
from health_intelligence.services import (
    DailyJournalService,
    GoalService,
    HealthService,
    LearningService,
    MealService,
    RecipeService,
    RecommendationService,
    SleepService,
    TaskService,
    UserService,
    WeightService,
    WorkoutService,
)


@st.cache_resource
def _uow_factory():
    return build_uow_factory()


@st.cache_resource
def get_authenticator() -> Authenticator:
    return Authenticator(_uow_factory())


@st.cache_resource
def get_session_token_store() -> SessionTokenStore:
    """プロセス内で全ユーザー共有のSessionTokenStore。

    `st.cache_resource`はStreamlitプロセス全体で1つのインスタンスを
    共有する(ユーザーごとにキャッシュされるわけではない)ため、
    トークンストアの用途に合致する。
    """
    return SessionTokenStore()


@st.cache_resource
def get_user_service() -> UserService:
    return UserService(_uow_factory())


@st.cache_resource
def get_health_service() -> HealthService:
    return HealthService(_uow_factory())


@st.cache_resource
def get_learning_service() -> LearningService:
    return LearningService(_uow_factory())


@st.cache_resource
def get_meal_service() -> MealService:
    return MealService(_uow_factory(), get_ai_provider())


@st.cache_resource
def get_workout_service() -> WorkoutService:
    return WorkoutService(_uow_factory())


@st.cache_resource
def get_sleep_service() -> SleepService:
    return SleepService(_uow_factory())


@st.cache_resource
def get_weight_service() -> WeightService:
    return WeightService(_uow_factory())


@st.cache_resource
def get_recommendation_service() -> RecommendationService:
    """WeightPredictorServiceはmodel_predict_fn未指定(=常にRule-based
    Fallback)で組み立てる。ml/run_weight_pipeline.pyで実データによる
    評価が完了し、学習済みモデルのロード方法が整備され次第、
    model_predict_fnを差し込む(architecture.md Section 11.6)。
    """
    return RecommendationService(_uow_factory())


@st.cache_resource
def get_recipe_service() -> RecipeService:
    return RecipeService(_uow_factory(), get_ai_provider())


@st.cache_resource
def get_goal_service() -> GoalService:
    return GoalService(_uow_factory())


@st.cache_resource
def get_task_service() -> TaskService:
    return TaskService(_uow_factory())


@st.cache_resource
def get_daily_journal_service() -> DailyJournalService:
    return DailyJournalService(_uow_factory())
