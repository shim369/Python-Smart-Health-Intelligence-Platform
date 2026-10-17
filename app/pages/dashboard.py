"""ダッシュボードページ。

睡眠・体調/食事/学習/PF開発・仕事/運動/家計を、できるだけグラフのみで
一覧できるようにする。表示期間は7日/30日/90日から選べる(デフォルトは
日々の状態把握という元来の用途に合わせ7日間。CSVインポート等でまとめて
投入した過去のログを見たい場合は30日/90日に切り替える)。
"""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.dashboard_charts import (  # noqa: E402
    cardio_minutes_by_exercise,
    group_average_by_date,
    group_sum_by_date,
    last_n_days,
    strength_max_weight_by_exercise,
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
    prefetch,
)

from health_intelligence.domain.enums import (  # noqa: E402
    GoalCategory,
    LearningCategory,
    TaskLogType,
)
from health_intelligence.domain.models import DailyTaskLog, WorkoutLog  # noqa: E402

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title(":material/dashboard: " + t("ダッシュボード"))

# 表示期間の切り替え。CSVインポート等でまとめて投入した過去のログは
# 「直近7日間」の外に出てしまうことがあるため、7日/30日/90日から選べる
# ようにする(デフォルトは日々の状態把握という元来の用途に合わせ7日間)。
_PERIOD_OPTIONS = [7, 30, 90]
selected_period = st.radio(
    t("表示期間"),
    options=_PERIOD_OPTIONS,
    format_func=lambda n: t("直近{days}日間", days=n),
    horizontal=True,
    key="dashboard_period_days",
)

# 日付の区切りはJST基準(今日の手入力・CSVインポートと同じ規則)。
# datetime.now(UTC).date()をそのまま使うとJST 0:00〜8:59の間だけ
# 「今日」が1日ズレるため、jst_date_ofで変換してから使う。
_DAYS = last_n_days(jst_date_of(datetime.now(UTC)), selected_period)

prefetch(
    lambda: get_sleep_service().list_sleep_logs(user_id),
    lambda: get_health_service().list_health_logs(user_id),
    lambda: get_weight_service().list_weight_logs(user_id),
    lambda: get_meal_service().list_meal_logs(user_id),
    lambda: get_learning_service().list_learning_logs(user_id),
    lambda: get_daily_journal_service().list_task_logs_in_range(user_id, _DAYS[0], _DAYS[-1]),
    lambda: get_task_service().list_tasks(user_id),
    lambda: get_workout_service().list_workout_logs(user_id),
)
_DATE_LABELS = [d.strftime("%m/%d") for d in _DAYS]
# 表示日数が多いほど日付ラベルが重なるため、その場合は斜めにする。
_LABEL_ANGLE = 0 if selected_period <= 7 else -45


def _bar_chart(
    values: list[float],
    *,
    y_title: str,
    key: str,
    caption: str,
    integer_y: bool = False,
    y_domain: tuple[float, float] | None = None,
) -> None:
    """`integer_y=True`で、y軸の目盛りを整数のみにする(セッション数等、
    小数を取り得ない値用。指定しない場合、Altairが値の範囲に応じて
    0.5刻み等の目盛りを自動生成し、整数しかないデータでも小数表示に
    見えてしまうことがあるため)。`y_domain`でy軸の表示範囲を固定する
    (カロリー等、目安値に合わせた見やすさのため)。上限を超える日がある
    場合は、棒が描画領域からはみ出して見えなくならないよう上限をその値まで
    広げる。
    """
    date_col = t("日付")
    df = pd.DataFrame({date_col: _DATE_LABELS, y_title: values})
    y_axis = alt.Axis(tickMinStep=1, format="d") if integer_y else alt.Axis()
    y_scale = (
        alt.Scale(domain=[y_domain[0], max(y_domain[1], *values)])
        if y_domain is not None
        else alt.Undefined
    )
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
        .encode(
            x=alt.X(f"{date_col}:N", sort=None, title=None, axis=alt.Axis(labelAngle=_LABEL_ANGLE)),
            y=alt.Y(f"{y_title}:Q", axis=y_axis, scale=y_scale),
        )
    )
    with st.container(border=True, key=f"dashboard-chart-{key}"):
        st.caption(caption)
        st.altair_chart(chart, width="stretch")


def _line_chart(
    series: dict[str, list[float | None]],
    *,
    y_title: str,
    key: str,
    caption: str,
    integer_y: bool = False,
    connect_gaps: bool = False,
) -> None:
    """`integer_y=True`で、y軸の目盛りを整数のみにする(体調スコア等、
    値自体は1〜5の整数だが、1日に複数回記録した日はその日の平均を
    プロットするため点の位置は小数になり得る値用。目盛りだけを整数に
    揃え、点・線の位置(実際の平均値)自体は変えない)。

    `connect_gaps=True`で、記録の無い日(None)を飛ばして前後の点を線で
    結ぶ(筋トレ種目の重量等、数日おきにしか記録しない値用。既定では
    Noneの日で線が途切れ、点が孤立して推移が読み取れないため)。
    x軸には記録の無い日も含めて表示期間の全日付を並べる。
    """
    date_col = t("日付")
    indicator_col = t("指標")
    # 系列ごとのDataFrameをpd.concatすると、値がすべてNone(記録なし)の系列が
    # あるときpandasのFutureWarningが出るため、縦持ちの列を直接組み立てる。
    df = pd.DataFrame(
        {
            date_col: [label for _ in series for label in _DATE_LABELS],
            y_title: pd.Series([v for values in series.values() for v in values], dtype="float64"),
            indicator_col: [name for name, values in series.items() for _ in values],
        }
    )
    if connect_gaps:
        df = df.dropna(subset=[y_title])
    y_axis = alt.Axis(tickMinStep=1, format="d") if integer_y else alt.Axis()
    encode_kwargs: dict[str, object] = {
        "x": alt.X(
            f"{date_col}:N",
            sort=None,
            title=None,
            axis=alt.Axis(labelAngle=_LABEL_ANGLE),
            scale=alt.Scale(domain=_DATE_LABELS),
        ),
        "y": alt.Y(f"{y_title}:Q", axis=y_axis, scale=alt.Scale(zero=not connect_gaps)),
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
    integer_y=True,
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
        st.caption(t("直近{days}日間の体重記録がありません。", days=selected_period))
    else:
        # y軸は60〜75kgを5kg刻みで固定表示する(体重の目標レンジに合わせた見やすさのため)。
        weight_chart = (
            alt.Chart(weight_df)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    f"{_date_col}:N", sort=None, title=None, axis=alt.Axis(labelAngle=_LABEL_ANGLE)
                ),
                y=alt.Y(
                    f"{_weight_col}:Q",
                    title=_weight_col,
                    scale=alt.Scale(domain=[60, 75]),
                    axis=alt.Axis(values=list(range(60, 76, 5))),
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
_bar_chart(
    group_sum_by_date(meal_logs, lambda m: jst_date_of(m.consumed_at), lambda m: m.calories, _DAYS),
    y_title=t("カロリー(kcal)"),
    key="calories",
    caption=t("カロリー(kcal)"),
    y_domain=(0, 3500),
)
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
# カロリーと同様、積み上げ合計が固定上限(500g)を超える日は上限を広げる。
pfc_max = max(500.0, *pfc_df.groupby(date_col)["g"].sum())
pfc_chart = (
    alt.Chart(pfc_df)
    .mark_bar()
    .encode(
        x=alt.X(f"{date_col}:N", sort=None, title=None, axis=alt.Axis(labelAngle=_LABEL_ANGLE)),
        y=alt.Y("g:Q", stack="zero", scale=alt.Scale(domain=[0, pfc_max])),
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
# _DAYS分ループしてlist_task_logsを日毎に呼ぶとDBラウンドトリップが表示日数分
# 発生する(N+1)ため、range一括取得してからPython側で日付ごとに振り分ける。
task_logs_in_range = get_daily_journal_service().list_task_logs_in_range(
    user_id, _DAYS[0], _DAYS[-1]
)
task_logs_by_day: dict[date, list[DailyTaskLog]] = {d: [] for d in _DAYS}
for log in task_logs_in_range:
    if log.journal_date in task_logs_by_day:
        task_logs_by_day[log.journal_date].append(log)
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
    y_domain=(0, 600),
)

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
    y_domain=(0, 600),
)

st.divider()

# ============================================================
# 運動
# ============================================================
st.subheader(t("運動"))

workout_logs = get_workout_service().list_workout_logs(user_id)


def _workout_date(w: WorkoutLog) -> date:
    return jst_date_of(w.performed_at)


max_weight_series = strength_max_weight_by_exercise(workout_logs, _workout_date, _DAYS)
if max_weight_series:
    _line_chart(
        max_weight_series,
        y_title=t("重量(kg)"),
        key="strength-max-weight",
        caption=t("種目別の最大重量(kg) — 記録日数の多い上位5種目"),
        connect_gaps=True,
    )
else:
    with st.container(border=True, key="dashboard-chart-strength-max-weight"):
        st.caption(t("種目別の最大重量(kg) — 記録日数の多い上位5種目"))
        st.caption(t("直近{days}日間の筋トレ(重量あり)の記録がありません。", days=selected_period))

exercise_col = t("種目")
minutes_col = t("時間(分)")
cardio_series = cardio_minutes_by_exercise(workout_logs, _workout_date, _DAYS)
cardio_df = pd.DataFrame(
    {
        _date_col: [label for _ in cardio_series for label in _DATE_LABELS],
        minutes_col: pd.Series(
            [v for values in cardio_series.values() for v in values], dtype="float64"
        ),
        exercise_col: [name for name, values in cardio_series.items() for _ in values],
    }
)
# カロリー等と同様、積み上げ合計が固定上限(90分)を超える日は上限を広げる。
cardio_max = max([90.0, *(sum(day) for day in zip(*cardio_series.values(), strict=True))])
cardio_chart = (
    alt.Chart(cardio_df)
    .mark_bar()
    .encode(
        x=alt.X(
            f"{_date_col}:N",
            sort=None,
            title=None,
            axis=alt.Axis(labelAngle=_LABEL_ANGLE),
            scale=alt.Scale(domain=_DATE_LABELS),
        ),
        y=alt.Y(f"{minutes_col}:Q", stack="zero", scale=alt.Scale(domain=[0, cardio_max])),
        color=alt.Color(f"{exercise_col}:N", title=exercise_col, sort=list(cardio_series)),
    )
)
with st.container(border=True, key="dashboard-chart-cardio"):
    st.caption(t("有酸素運動時間(分) — 種目別"))
    st.altair_chart(cardio_chart, width="stretch")

st.divider()

# ============================================================
# 家計
# ============================================================
st.subheader(t("家計"))

daily_journal_service = get_daily_journal_service()
# get_journalを_DAYS分ループするとDBラウンドトリップが日数分発生する(N+1)
# ため、range一括取得してからPython側で日付ごとの食費に振り分ける。
journals_by_day = {
    j.journal_date: j
    for j in daily_journal_service.list_journals_in_range(user_id, _DAYS[0], _DAYS[-1])
}
expense_values = [
    journals_by_day[d].food_expense_yen or 0 if d in journals_by_day else 0 for d in _DAYS
]
_bar_chart(
    expense_values,
    y_title=t("食費合計(円)"),
    key="expense",
    caption=t("食費合計(円)"),
)
