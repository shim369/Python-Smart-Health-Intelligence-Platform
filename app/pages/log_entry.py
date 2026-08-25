"""ログ入力ページ。

食事・運動・睡眠・体重・体調の記録をタブで切り替えて入力する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import UTC, datetime  # noqa: E402
from uuid import uuid4  # noqa: E402

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.workout_form import build_workout_log  # noqa: E402
from services import (  # noqa: E402
    get_health_service,
    get_meal_service,
    get_sleep_service,
    get_weight_service,
    get_workout_service,
)

from health_intelligence.domain.enums import MealType  # noqa: E402
from health_intelligence.domain.models import (  # noqa: E402
    HealthLog,
    MealLog,
    SleepLog,
    WeightLog,
)

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title("ログ入力")

meal_tab, workout_tab, sleep_tab, weight_tab, health_tab = st.tabs(
    ["食事", "運動", "睡眠", "体重", "体調"]
)

with meal_tab:
    with st.form("meal_form"):
        meal_type = st.selectbox(
            "食事区分",
            options=list(MealType),
            format_func=lambda m: m.value,
        )
        calories = st.number_input("カロリー(kcal)", min_value=0.0, step=10.0)
        protein_g = st.number_input("タンパク質(g)", min_value=0.0, step=1.0)
        fat_g = st.number_input("脂質(g)", min_value=0.0, step=1.0)
        carbohydrate_g = st.number_input("炭水化物(g)", min_value=0.0, step=1.0)
        memo = st.text_input("メモ(任意)", key="meal_memo")
        submitted = st.form_submit_button("記録する")

    if submitted:
        meal_log = MealLog(
            meal_log_id=uuid4(),
            user_id=user_id,
            consumed_at=datetime.now(UTC),
            meal_type=meal_type,
            calories=calories,
            protein_g=protein_g,
            fat_g=fat_g,
            carbohydrate_g=carbohydrate_g,
            memo=memo or None,
        )
        get_meal_service().record_meal_log(meal_log)
        st.success("食事記録を保存しました。")

with workout_tab:
    st.caption(
        "同じ種目名・カテゴリの行はまとめて1種目・複数セットとして"
        "保存されます(例: レッグプレスを2行入力すると2セット扱い)。"
    )
    default_rows = pd.DataFrame(
        [
            {
                "exercise_name": "",
                "category": "strength",
                "duration_minutes": None,
                "reps": None,
                "weight_kg": None,
            }
        ]
    )
    edited = st.data_editor(
        default_rows,
        num_rows="dynamic",
        column_config={
            "category": st.column_config.SelectboxColumn(
                "カテゴリ", options=["cardio", "strength"]
            ),
        },
        key="workout_editor",
    )

    if st.button("運動記録を保存する"):
        rows = edited.to_dict(orient="records")
        workout_log = build_workout_log(
            rows, user_id=user_id, performed_at=datetime.now(UTC)
        )
        if not workout_log.exercises:
            st.error("有効な種目が入力されていません。")
        else:
            get_workout_service().record_workout_log(workout_log)
            st.success(f"運動記録({len(workout_log.exercises)}種目)を保存しました。")

with sleep_tab:
    with st.form("sleep_form"):
        bedtime_date = st.date_input("就寝日")
        bedtime_time = st.time_input("就寝時刻")
        wake_date = st.date_input("起床日")
        wake_time_value = st.time_input("起床時刻")
        submitted_sleep = st.form_submit_button("記録する")

    if submitted_sleep:
        bedtime = datetime.combine(bedtime_date, bedtime_time, tzinfo=UTC)
        wake_time = datetime.combine(wake_date, wake_time_value, tzinfo=UTC)
        if wake_time <= bedtime:
            st.error("起床時刻は就寝時刻より後にしてください。")
        else:
            sleep_log = SleepLog(
                sleep_log_id=uuid4(),
                user_id=user_id,
                bedtime=bedtime,
                wake_time=wake_time,
            )
            get_sleep_service().record_sleep_log(sleep_log)
            st.success(f"睡眠記録({sleep_log.duration_minutes}分)を保存しました。")

with weight_tab:
    with st.form("weight_form"):
        weight_kg = st.number_input("体重(kg)", min_value=0.0, step=0.1)
        submitted_weight = st.form_submit_button("記録する")

    if submitted_weight:
        weight_log = WeightLog(
            weight_log_id=uuid4(),
            user_id=user_id,
            recorded_at=datetime.now(UTC),
            weight_kg=weight_kg,
        )
        get_weight_service().record_weight_log(weight_log)
        st.success("体重記録を保存しました。")

with health_tab:
    with st.form("health_form"):
        condition_score = st.slider(
            "体調スコア(1=不調 〜 5=良好)", min_value=1, max_value=5, value=3
        )
        symptoms_text = st.text_input(
            "症状(カンマ区切り、任意)", placeholder="例: 頭痛, 倦怠感"
        )
        health_memo = st.text_input("メモ(任意)", key="health_memo")
        submitted_health = st.form_submit_button("記録する")

    if submitted_health:
        symptoms = [s.strip() for s in symptoms_text.split(",") if s.strip()]
        health_log = HealthLog(
            health_log_id=uuid4(),
            user_id=user_id,
            recorded_at=datetime.now(UTC),
            condition_score=condition_score,
            symptoms=symptoms,
            memo=health_memo or None,
        )
        get_health_service().record_health_log(health_log)
        st.success("体調記録を保存しました。")
