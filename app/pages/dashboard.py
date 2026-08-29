"""ダッシュボードページ。

Health Score・週間サマリー・改善提案・体重推移グラフを表示する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import UTC, datetime, timedelta  # noqa: E402

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from services import get_recommendation_service, get_weight_service  # noqa: E402

from health_intelligence.ml.dataset import MIN_DAYS  # noqa: E402

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title("ダッシュボード")

recommendation_service = get_recommendation_service()
report = recommendation_service.get_recommendations(user_id)

st.subheader("Health Score")
st.metric("総合スコア", f"{report.health_score.overall_score:.0f} / 100")

col_nutrition, col_weight, col_sleep, col_workout = st.columns(4)
col_nutrition.metric("栄養", f"{report.health_score.nutrition.score:.0f}")
col_weight.metric("体重", f"{report.health_score.weight.score:.0f}")
col_sleep.metric("睡眠", f"{report.health_score.sleep.score:.0f}")
col_workout.metric("運動", f"{report.health_score.workout.score:.0f}")

st.caption("Health Scoreは医療診断を目的としない、本アプリ独自の健康管理支援指標です。")

st.subheader("改善提案")
if not report.recommendations:
    st.info("直近の記録が不足しているため、提案を表示できません。")
else:
    for recommendation in report.recommendations:
        if recommendation.priority >= 30:
            st.warning(f"[{recommendation.domain}] {recommendation.message}")
        else:
            st.info(f"[{recommendation.domain}] {recommendation.message}")

st.subheader("学習データの蓄積状況")
st.caption(
    "AIによる体重予測に必要なデータ量(食事・睡眠・運動・体重の記録が"
    "揃っている日数)の進捗です。基準を満たすまではルールベースの"
    "改善提案のみが表示されます。"
)
ml_progress = recommendation_service.get_ml_progress(user_id)
st.progress(
    min(ml_progress.total_days / MIN_DAYS, 1.0),
    text=f"学習データ: {ml_progress.total_days}/{MIN_DAYS}日",
)
if ml_progress.is_sufficient:
    st.success(ml_progress.reason)
else:
    st.caption(ml_progress.reason)

st.subheader("体重推移")
weight_service = get_weight_service()
weight_logs = weight_service.list_weight_logs(user_id)

recent_logs = [w for w in weight_logs if w.recorded_at >= datetime.now(UTC) - timedelta(days=90)]
if recent_logs:
    recent_logs.sort(key=lambda w: w.recorded_at)
    df = pd.DataFrame(
        {
            "日付": [w.recorded_at.date() for w in recent_logs],
            "体重(kg)": [w.weight_kg for w in recent_logs],
        }
    )
    # y軸は50〜75kgを5kg刻みで固定表示する(体重の目標レンジに合わせた
    # 見やすさのための固定範囲。実測値がこの範囲外の場合は軸の外に
    # はみ出して表示される)。
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("日付:T", title="日付"),
            y=alt.Y(
                "体重(kg):Q",
                title="体重(kg)",
                scale=alt.Scale(domain=[50, 75]),
                axis=alt.Axis(values=list(range(50, 76, 5))),
            ),
        )
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("直近90日間の体重記録がありません。")
