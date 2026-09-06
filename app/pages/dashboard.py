"""ダッシュボードページ。

過去7日間の睡眠・体調/食事/学習/PF開発・仕事/運動/家計を、
できるだけグラフのみで一覧できるようにする。
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.dashboard_charts import (  # noqa: E402
    group_average_by_date,
    group_sum_by_date,
    last_n_days,
)
from components.formatting import jst_date_of  # noqa: E402
from i18n import t  # noqa: E402
from services import (  # noqa: E402
    get_daily_journal_service,
    get_health_service,
    get_learning_service,
    get_meal_service,
    get_sleep_service,
    get_task_service,
    get_weight_service,
    get_workout_service,
)

from health_intelligence.domain.enums import (  # noqa: E402
    ExerciseCategory,
    GoalCategory,
    LearningCategory,
    TaskLogType,
)

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title(":material/dashboard: " + t("ダッシュボード"))

_DAYS = last_n_days(datetime.now(UTC).date(), 7)
_DATE_LABELS = [d.strftime("%m/%d") for d in _DAYS]


def _bar_chart(values: list[float], *, y_title: str, key: str, caption: str) -> None:
    date_col = t("日付")
    df = pd.DataFrame({date_col: _DATE_LABELS, y_title: values})
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
        .encode(x=alt.X(f"{date_col}:N", sort=None, title=None), y=alt.Y(f"{y_title}:Q"))
    )
    with st.container(border=True, key=f"dashboard-chart-{key}"):
        st.caption(caption)
        st.altair_chart(chart, width="stretch")


def _line_chart(
    series: dict[str, list[float | None]], *, y_title: str, key: str, caption: str
) -> None:
    date_col = t("日付")
    indicator_col = t("指標")
    frames = [
        pd.DataFrame({date_col: _DATE_LABELS, y_title: values, indicator_col: name})
        for name, values in series.items()
    ]
    df = pd.concat(frames, ignore_index=True)
    encode_kwargs: dict[str, object] = {
        "x": alt.X(f"{date_col}:N", sort=None, title=None),
        "y": alt.Y(f"{y_title}:Q"),
    }
    if len(series) > 1:
        encode_kwargs["color"] = alt.Color(
            f"{indicator_col}:N", title=indicator_col, sort=list(series)
        )
    chart = alt.Chart(df).mark_line(point=True).encode(**encode_kwargs)
    with st.container(border=True, key=f"dashboard-chart-{key}"):
        st.caption(caption)
        st.altair_chart(chart, width="stretch")


# ============================================================
# 睡眠・体調
# ============================================================
st.subheader(t("睡眠・体調"))

sleep_logs = get_sleep_service().list_sleep_logs(user_id)
sleep_col, condition_col = st.columns(2)
with sleep_col:
    _bar_chart(
        group_sum_by_date(
            sleep_logs,
            lambda s: jst_date_of(s.bedtime),
            lambda s: s.duration_minutes / 60,
            _DAYS,
        ),
        y_title=t("睡眠時間(h)"),
        key="sleep",
        caption=t("睡眠時間(h)"),
    )

health_logs = get_health_service().list_health_logs(user_id)
with condition_col:
    _line_chart(
        {
            t("総合"): group_average_by_date(
                health_logs,
                lambda h: jst_date_of(h.recorded_at),
                lambda h: h.condition_score,
                _DAYS,
            ),
            t("朝"): group_average_by_date(
                health_logs,
                lambda h: jst_date_of(h.recorded_at),
                lambda h: h.morning_condition,
                _DAYS,
            ),
            t("夜"): group_average_by_date(
                health_logs,
                lambda h: jst_date_of(h.recorded_at),
                lambda h: h.evening_condition,
                _DAYS,
            ),
            t("メンタル"): group_average_by_date(
                health_logs, lambda h: jst_date_of(h.recorded_at), lambda h: h.mental_score, _DAYS
            ),
            t("疲労"): group_average_by_date(
                health_logs, lambda h: jst_date_of(h.recorded_at), lambda h: h.fatigue_score, _DAYS
            ),
            t("ストレス"): group_average_by_date(
                health_logs, lambda h: jst_date_of(h.recorded_at), lambda h: h.stress_score, _DAYS
            ),
        },
        y_title=t("スコア"),
        key="condition",
        caption=t("体調スコア(1〜5)"),
    )

weight_logs = get_weight_service().list_weight_logs(user_id)
weight_values = group_average_by_date(
    weight_logs, lambda w: jst_date_of(w.recorded_at), lambda w: w.weight_kg, _DAYS
)
_date_col = t("日付")
_weight_col = t("体重(kg)")
weight_df = pd.DataFrame({_date_col: _DATE_LABELS, _weight_col: weight_values}).dropna()
with st.container(border=True, key="dashboard-chart-weight"):
    st.caption(_weight_col)
    if weight_df.empty:
        st.caption(t("直近7日間の体重記録がありません。"))
    else:
        # y軸は50〜75kgを5kg刻みで固定表示する(体重の目標レンジに合わせた見やすさのため)。
        weight_chart = (
            alt.Chart(weight_df)
            .mark_line(point=True)
            .encode(
                x=alt.X(f"{_date_col}:N", sort=None, title=None),
                y=alt.Y(
                    f"{_weight_col}:Q",
                    title=_weight_col,
                    scale=alt.Scale(domain=[50, 75]),
                    axis=alt.Axis(values=list(range(50, 76, 5))),
                ),
            )
        )
        st.altair_chart(weight_chart, width="stretch")

st.divider()

# ============================================================
# 食事
# ============================================================
st.subheader(t("食事"))

meal_logs = get_meal_service().list_meal_logs(user_id)
cal_col, pfc_col = st.columns(2)
with cal_col:
    _bar_chart(
        group_sum_by_date(
            meal_logs, lambda m: jst_date_of(m.consumed_at), lambda m: m.calories, _DAYS
        ),
        y_title=t("カロリー(kcal)"),
        key="calories",
        caption=t("カロリー(kcal)"),
    )
with pfc_col:
    date_col = t("日付")
    nutrient_col = t("栄養素")
    pfc_frames = []
    for label, getter in (
        (t("タンパク質"), lambda m: m.protein_g),
        (t("脂質"), lambda m: m.fat_g),
        (t("炭水化物"), lambda m: m.carbohydrate_g),
    ):
        values = group_sum_by_date(meal_logs, lambda m: jst_date_of(m.consumed_at), getter, _DAYS)
        pfc_frames.append(pd.DataFrame({date_col: _DATE_LABELS, "g": values, nutrient_col: label}))
    pfc_df = pd.concat(pfc_frames, ignore_index=True)
    pfc_chart = (
        alt.Chart(pfc_df)
        .mark_bar()
        .encode(
            x=alt.X(f"{date_col}:N", sort=None, title=None),
            y=alt.Y("g:Q", stack="zero"),
            color=alt.Color(
                f"{nutrient_col}:N",
                title=nutrient_col,
                sort=[t("タンパク質"), t("脂質"), t("炭水化物")],
            ),
        )
    )
    with st.container(border=True, key="dashboard-chart-pfc"):
        st.caption(t("PFC(g)"))
        st.altair_chart(pfc_chart, width="stretch")

st.divider()

# ============================================================
# 学習 / PF開発・仕事
# ============================================================
learning_logs = get_learning_service().list_learning_logs(user_id)
task_logs_by_day = {d: get_daily_journal_service().list_task_logs(user_id, d) for d in _DAYS}
all_tasks = get_task_service().list_tasks(user_id)
task_by_id = {t.task_id: t for t in all_tasks}


def _task_minutes_by_category(categories: set[GoalCategory]) -> list[float]:
    totals = dict.fromkeys(_DAYS, 0.0)
    for d, logs in task_logs_by_day.items():
        for log in logs:
            task = task_by_id.get(log.task_id)
            if (
                task is not None
                and task.category in categories
                and task.log_type == TaskLogType.COUNT_AND_DURATION
                and log.duration_minutes
            ):
                totals[d] += log.duration_minutes
    return [totals[d] for d in _DAYS]


study_col, pfdev_col = st.columns(2)
with study_col:
    st.subheader(t("学習"))
    learning_minutes = group_sum_by_date(
        [
            log
            for log in learning_logs
            if log.category in (LearningCategory.EXAM_STUDY, LearningCategory.RESEARCH)
        ],
        lambda log: jst_date_of(log.started_at),
        lambda log: log.duration_minutes or 0,
        _DAYS,
    )
    task_minutes = _task_minutes_by_category({GoalCategory.STUDY})
    _bar_chart(
        [a + b for a, b in zip(learning_minutes, task_minutes, strict=True)],
        y_title=t("学習時間(分)"),
        key="study",
        caption=t("学習時間(分) — 学習ログ + タスク実績"),
    )

with pfdev_col:
    st.subheader(t("PF開発・仕事"))
    pfdev_learning_minutes = group_sum_by_date(
        [
            log
            for log in learning_logs
            if log.category in (LearningCategory.PORTFOLIO_DEV, LearningCategory.CAREER_STRATEGY)
        ],
        lambda log: jst_date_of(log.started_at),
        lambda log: log.duration_minutes or 0,
        _DAYS,
    )
    pfdev_task_minutes = _task_minutes_by_category(
        {GoalCategory.PF_DEV, GoalCategory.WORK, GoalCategory.CAREER}
    )
    _bar_chart(
        [a + b for a, b in zip(pfdev_learning_minutes, pfdev_task_minutes, strict=True)],
        y_title=t("作業時間(分)"),
        key="pfdev",
        caption=t("作業時間(分) — 学習ログ + タスク実績"),
    )

st.divider()

# ============================================================
# 運動
# ============================================================
st.subheader(t("運動"))

workout_logs = get_workout_service().list_workout_logs(user_id)
session_col, cardio_col = st.columns(2)
with session_col:
    _bar_chart(
        group_sum_by_date(workout_logs, lambda w: jst_date_of(w.performed_at), lambda w: 1, _DAYS),
        y_title=t("セッション数"),
        key="workout-sessions",
        caption=t("運動セッション数"),
    )
with cardio_col:
    cardio_pairs = [
        (jst_date_of(w.performed_at), exercise.duration_minutes or 0)
        for w in workout_logs
        for exercise in w.exercises
        if exercise.category == ExerciseCategory.CARDIO
    ]
    _bar_chart(
        group_sum_by_date(cardio_pairs, lambda p: p[0], lambda p: p[1], _DAYS),
        y_title=t("有酸素運動時間(分)"),
        key="cardio",
        caption=t("有酸素運動時間(分)"),
    )

st.divider()

# ============================================================
# 家計
# ============================================================
st.subheader(t("家計"))

daily_journal_service = get_daily_journal_service()
journals = [daily_journal_service.get_journal(user_id, d) for d in _DAYS]
expense_values = [j.food_expense_yen or 0 if j is not None else 0 for j in journals]
_bar_chart(
    expense_values,
    y_title=t("食費合計(円)"),
    key="expense",
    caption=t("食費合計(円)"),
)
