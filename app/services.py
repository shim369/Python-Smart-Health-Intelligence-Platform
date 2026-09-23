"""Streamlit側でServiceインスタンスを組み立てるヘルパー。

`st.cache_resource`により、DB接続やAI Providerなど状態を持つ
オブジェクトをStreamlitの再実行(rerun)間で使い回す
(毎回の再実行でSQLAlchemy Engineを作り直さないようにするため)。

加えて、各Serviceを`_CachedService`で包み、読み取り系メソッド
(list_/get_/compute_)の結果をキャッシュする。DBはリモート(Neon)で
1回のService呼び出しに数百msかかる一方、Streamlitはウィジェット操作の
たびにページ全体を再実行するため、キャッシュ無しでは操作のたびに
全ログを取得し直して画面が重くなる。書き込み系メソッドが呼ばれたら
そのServiceと、同じテーブルを読む関連Service(`_DEPENDENTS`)の
キャッシュを破棄するので、このアプリ経由の更新は即座に反映される
(アプリ外からのDB直接変更はTTL経過後に反映される)。
"""

from __future__ import annotations

import copy
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

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

_CACHE_TTL_SECONDS = 600.0
_READ_PREFIXES = ("list_", "get_", "compute_")
_WRITE_METHODS = {"get_or_create_user"}
"""名前はget_で始まるが、Userを新規作成しうるため書き込みとして扱う。"""
_PASSTHROUGH_METHODS = {"estimate_nutrition"}
"""DBを読み書きしない(AI推定のみ)ため、キャッシュも破棄もしない。"""
_DEPENDENTS: dict[str, set[str]] = {
    "MealService": {"RecommendationService"},
    "SleepService": {"RecommendationService"},
    "WeightService": {"RecommendationService"},
    "WorkoutService": {"RecommendationService"},
    "GoalService": {"TaskService", "DailyJournalService"},
    "TaskService": {"GoalService", "DailyJournalService"},
    "DailyJournalService": {"GoalService", "TaskService"},
}
"""書き込んだServiceのキャッシュに加えて破棄すべき、他Serviceの名前。
あるServiceのテーブル(例: TaskのDailyTaskLog)を別Service(例:
GoalServiceの進捗計算)も読んでいる組み合わせを列挙する
(src/health_intelligence/services/ の各uow.<repo>参照から導出)。
Goal/Task/DailyJournalは相互に参照し合うため1グループとして扱う。"""


def _freeze(value: Any) -> Any:
    """キャッシュキーにするため、list/dictを再帰的にhash可能な形へ変換する。"""
    if isinstance(value, list | tuple):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    return value


class _ReadCache:
    """全Service共通の読み取り結果キャッシュ(スレッドセーフ)。

    エントリはService名(namespace)ごとに分けて保持し、書き込み時は
    namespace単位で破棄する。
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, dict[Any, tuple[float, Any]]] = {}
        self._generations: dict[str, int] = {}

    def get_or_load(self, namespace: str, key: Any, loader: Callable[[], Any]) -> Any:
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(namespace, {}).get(key)
            if entry is not None and entry[0] > now:
                return entry[1]
            generation = self._generations.get(namespace, 0)
        value = loader()
        with self._lock:
            # 読み込み中に別セッションが書き込んだ場合、古い値を保存しない。
            if generation == self._generations.get(namespace, 0):
                self._entries.setdefault(namespace, {})[key] = (
                    now + _CACHE_TTL_SECONDS,
                    value,
                )
        return value

    def invalidate(self, namespaces: set[str]) -> None:
        with self._lock:
            for namespace in namespaces:
                self._entries.pop(namespace, None)
                self._generations[namespace] = self._generations.get(namespace, 0) + 1


class _CachedService:
    """Serviceへの呼び出しを中継し、読み取り結果をキャッシュするProxy。"""

    def __init__(self, service: object, cache: _ReadCache) -> None:
        self._service = service
        self._cache = cache
        self._namespace = type(service).__name__

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._service, name)
        if name.startswith("_") or not callable(attr) or name in _PASSTHROUGH_METHODS:
            return attr

        if name.startswith(_READ_PREFIXES) and name not in _WRITE_METHODS:

            def cached_read(*args: Any, **kwargs: Any) -> Any:
                key = (name, _freeze(args), _freeze(kwargs))
                try:
                    hash(key)
                except TypeError:
                    return attr(*args, **kwargs)
                value = self._cache.get_or_load(self._namespace, key, lambda: attr(*args, **kwargs))
                # 呼び出し側でlist/dictを破壊的に変更されてもキャッシュが
                # 汚れないよう、コンテナはコピーして返す(要素のDomain Modelは
                # frozen dataclassのため共有してよい)。
                return copy.copy(value) if isinstance(value, list | dict) else value

            return cached_read

        def write(*args: Any, **kwargs: Any) -> Any:
            try:
                return attr(*args, **kwargs)
            finally:
                self._cache.invalidate({self._namespace, *_DEPENDENTS.get(self._namespace, set())})

        return write


@st.cache_resource
def _read_cache() -> _ReadCache:
    return _ReadCache()


def _cached[T](service: T) -> T:
    return cast(T, _CachedService(service, _read_cache()))


def prefetch(*loaders: Callable[[], object]) -> None:
    """互いに独立した読み取り系Service呼び出しを並列実行し、キャッシュを温める。

    キャッシュが空の初回表示や書き込み直後は、ページ冒頭の読み取りが
    DB往復分ずつ直列に積み上がって遅くなるため、先にまとめて並列に
    実行しておく。直後のページ本体からの同じ呼び出しはキャッシュから
    即座に返る(引数が完全に一致する呼び出しのみヒットする点に注意)。
    例外はここでは握りつぶし、ページ本体の同じ呼び出しで改めて
    発生させる(通常の実行経路でエラー表示させるため)。

    ワーカースレッドには呼び出し元のScriptRunContextを引き継ぐ。loader内で
    `get_*_service()`(`st.cache_resource`)を呼ぶため、引き継がないと
    「missing ScriptRunContext」警告がスレッド数分出力される。
    """
    if not loaders:
        return

    ctx = get_script_run_ctx()

    def run(loader: Callable[[], object]) -> None:
        try:
            loader()
        except Exception:  # noqa: BLE001
            pass

    with ThreadPoolExecutor(
        max_workers=min(len(loaders), 8),
        initializer=lambda: add_script_run_ctx(threading.current_thread(), ctx),
    ) as executor:
        list(executor.map(run, loaders))


@st.cache_resource
def _uow_factory():
    return build_uow_factory()


@st.cache_resource
def get_user_service() -> UserService:
    return _cached(UserService(_uow_factory()))


@st.cache_resource
def get_health_service() -> HealthService:
    return _cached(HealthService(_uow_factory()))


@st.cache_resource
def get_learning_service() -> LearningService:
    return _cached(LearningService(_uow_factory()))


@st.cache_resource
def get_meal_service() -> MealService:
    return _cached(MealService(_uow_factory(), get_ai_provider()))


@st.cache_resource
def get_workout_service() -> WorkoutService:
    return _cached(WorkoutService(_uow_factory()))


@st.cache_resource
def get_sleep_service() -> SleepService:
    return _cached(SleepService(_uow_factory()))


@st.cache_resource
def get_weight_service() -> WeightService:
    return _cached(WeightService(_uow_factory()))


@st.cache_resource
def get_recommendation_service() -> RecommendationService:
    """WeightPredictorServiceはmodel_predict_fn未指定(=常にRule-based
    Fallback)で組み立てる。ml/run_weight_pipeline.pyで実データによる
    評価が完了し、学習済みモデルのロード方法が整備され次第、
    model_predict_fnを差し込む(architecture.md Section 11.6)。
    """
    return _cached(RecommendationService(_uow_factory()))


@st.cache_resource
def get_recipe_service() -> RecipeService:
    return _cached(RecipeService(_uow_factory(), get_ai_provider()))


@st.cache_resource
def get_goal_service() -> GoalService:
    return _cached(GoalService(_uow_factory()))


@st.cache_resource
def get_task_service() -> TaskService:
    return _cached(TaskService(_uow_factory()))


@st.cache_resource
def get_daily_journal_service() -> DailyJournalService:
    return _cached(DailyJournalService(_uow_factory()))
