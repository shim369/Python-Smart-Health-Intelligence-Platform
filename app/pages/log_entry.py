"""ログ入力ページ。

食事・運動・睡眠・体重・体調の記録をタブで切り替えて入力する。
各タブには「新規記録」フォームと、既存記録を選んで編集・削除できる
「過去の記録」セクションを設ける。

日付・時刻の入力は日本時間(JST)で行い、保存時にUTCへ変換する
(components/formatting.py参照)。DB上は一貫してUTCで保持し、
表示・入力の境界でのみJSTへ変換する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import date, datetime  # noqa: E402
from uuid import uuid4  # noqa: E402

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.formatting import (  # noqa: E402
    combine_jst_to_utc,
    format_datetime_jst,
    jst_date_of,
    jst_time_of,
)
from components.workout_form import build_workout_log, workout_log_to_rows  # noqa: E402
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

st.title("📝 ログ入力")

meal_tab, workout_tab, sleep_tab, weight_tab, health_tab = st.tabs(
    ["食事", "運動", "睡眠", "体重", "体調"]
)

_MAX_HISTORY_ROWS = 30
"""過去の記録セクションに表示する最大件数(新しい順)。"""


# ============================================================
# 食事
# ============================================================
with meal_tab:
    st.subheader("新規記録")
    with st.form("meal_form"):
        meal_date = st.date_input("日付", value=date.today(), key="meal_date")
        meal_time = st.time_input("時刻", value=datetime.now().time(), key="meal_time")
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
            consumed_at=combine_jst_to_utc(meal_date, meal_time),
            meal_type=meal_type,
            calories=calories,
            protein_g=protein_g,
            fat_g=fat_g,
            carbohydrate_g=carbohydrate_g,
            memo=memo or None,
        )
        get_meal_service().record_meal_log(meal_log)
        st.success("食事記録を保存しました。")
        st.rerun()

    st.divider()
    st.subheader("過去の記録")
    meal_service = get_meal_service()
    meal_logs = sorted(
        meal_service.list_meal_logs(user_id), key=lambda m: m.consumed_at, reverse=True
    )[:_MAX_HISTORY_ROWS]

    if not meal_logs:
        st.info("まだ記録がありません。")
    else:
        st.dataframe(
            pd.DataFrame(
                {
                    "日時": [format_datetime_jst(m.consumed_at) for m in meal_logs],
                    "区分": [m.meal_type.value for m in meal_logs],
                    "kcal": [m.calories for m in meal_logs],
                    "P(g)": [m.protein_g for m in meal_logs],
                    "F(g)": [m.fat_g for m in meal_logs],
                    "C(g)": [m.carbohydrate_g for m in meal_logs],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        selected_meal = st.selectbox(
            "編集する記録を選択",
            options=meal_logs,
            format_func=lambda m: (
                f"{format_datetime_jst(m.consumed_at)} "
                f"{m.meal_type.value} {m.calories:.0f}kcal"
            ),
            key="meal_select",
        )

        if selected_meal is not None:
            with st.form(f"meal_edit_form_{selected_meal.meal_log_id}"):
                edit_date = st.date_input(
                    "日付", value=jst_date_of(selected_meal.consumed_at)
                )
                edit_time = st.time_input(
                    "時刻", value=jst_time_of(selected_meal.consumed_at)
                )
                edit_meal_type = st.selectbox(
                    "食事区分",
                    options=list(MealType),
                    index=list(MealType).index(selected_meal.meal_type),
                    format_func=lambda m: m.value,
                )
                edit_calories = st.number_input(
                    "カロリー(kcal)",
                    min_value=0.0,
                    step=10.0,
                    value=selected_meal.calories,
                )
                edit_protein_g = st.number_input(
                    "タンパク質(g)",
                    min_value=0.0,
                    step=1.0,
                    value=selected_meal.protein_g,
                )
                edit_fat_g = st.number_input(
                    "脂質(g)", min_value=0.0, step=1.0, value=selected_meal.fat_g
                )
                edit_carbohydrate_g = st.number_input(
                    "炭水化物(g)",
                    min_value=0.0,
                    step=1.0,
                    value=selected_meal.carbohydrate_g,
                )
                edit_memo = st.text_input("メモ(任意)", value=selected_meal.memo or "")
                col1, col2 = st.columns(2)
                update_clicked = col1.form_submit_button("更新する")
                delete_clicked = col2.form_submit_button("削除する")

            if update_clicked:
                updated = MealLog(
                    meal_log_id=selected_meal.meal_log_id,
                    user_id=user_id,
                    consumed_at=combine_jst_to_utc(edit_date, edit_time),
                    meal_type=edit_meal_type,
                    calories=edit_calories,
                    protein_g=edit_protein_g,
                    fat_g=edit_fat_g,
                    carbohydrate_g=edit_carbohydrate_g,
                    memo=edit_memo or None,
                )
                meal_service.update_meal_log(updated)
                st.success("更新しました。")
                st.rerun()

            if delete_clicked:
                meal_service.delete_meal_log(user_id, selected_meal.meal_log_id)
                st.success("削除しました。")
                st.rerun()


# ============================================================
# 運動
# ============================================================
with workout_tab:
    st.subheader("新規記録")
    st.caption(
        "同じ種目名・カテゴリの行はまとめて1種目・複数セットとして"
        "保存されます(例: レッグプレスを2行入力すると2セット扱い)。"
    )
    workout_date = st.date_input("日付", value=date.today(), key="workout_date")
    workout_time = st.time_input(
        "時刻", value=datetime.now().time(), key="workout_time"
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
            rows,
            user_id=user_id,
            performed_at=combine_jst_to_utc(workout_date, workout_time),
        )
        if not workout_log.exercises:
            st.error("有効な種目が入力されていません。")
        else:
            get_workout_service().record_workout_log(workout_log)
            st.success(f"運動記録({len(workout_log.exercises)}種目)を保存しました。")
            st.rerun()

    st.divider()
    st.subheader("過去の記録")
    workout_service = get_workout_service()
    workout_logs = sorted(
        workout_service.list_workout_logs(user_id),
        key=lambda w: w.performed_at,
        reverse=True,
    )[:_MAX_HISTORY_ROWS]

    if not workout_logs:
        st.info("まだ記録がありません。")
    else:
        st.dataframe(
            pd.DataFrame(
                {
                    "日時": [format_datetime_jst(w.performed_at) for w in workout_logs],
                    "種目数": [len(w.exercises) for w in workout_logs],
                    "種目": [
                        "、".join(e.exercise_name for e in w.exercises)
                        for w in workout_logs
                    ],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        selected_workout_index = st.selectbox(
            "編集する記録を選択",
            options=range(len(workout_logs)),
            format_func=lambda i: (
                f"{format_datetime_jst(workout_logs[i].performed_at)} "
                f"({len(workout_logs[i].exercises)}種目)"
            ),
            key="workout_select",
        )
        selected_workout = (
            workout_logs[selected_workout_index]
            if selected_workout_index is not None
            else None
        )

        if selected_workout is not None:
            edit_workout_date = st.date_input(
                "日付",
                value=jst_date_of(selected_workout.performed_at),
                key=f"workout_edit_date_{selected_workout.workout_log_id}",
            )
            edit_workout_time = st.time_input(
                "時刻",
                value=jst_time_of(selected_workout.performed_at),
                key=f"workout_edit_time_{selected_workout.workout_log_id}",
            )
            edit_default_rows = pd.DataFrame(workout_log_to_rows(selected_workout))
            edited_existing = st.data_editor(
                edit_default_rows,
                num_rows="dynamic",
                column_config={
                    "category": st.column_config.SelectboxColumn(
                        "カテゴリ", options=["cardio", "strength"]
                    ),
                },
                key=f"workout_edit_editor_{selected_workout.workout_log_id}",
            )

            col1, col2 = st.columns(2)
            if col1.button(
                "更新する", key=f"workout_update_{selected_workout.workout_log_id}"
            ):
                updated_rows = edited_existing.to_dict(orient="records")
                updated_workout = build_workout_log(
                    updated_rows,
                    user_id=user_id,
                    performed_at=combine_jst_to_utc(
                        edit_workout_date, edit_workout_time
                    ),
                    workout_log_id=selected_workout.workout_log_id,
                )
                if not updated_workout.exercises:
                    st.error("有効な種目が入力されていません。")
                else:
                    workout_service.update_workout_log(updated_workout)
                    st.success("更新しました。")
                    st.rerun()

            if col2.button(
                "削除する", key=f"workout_delete_{selected_workout.workout_log_id}"
            ):
                workout_service.delete_workout_log(
                    user_id, selected_workout.workout_log_id
                )
                st.success("削除しました。")
                st.rerun()


# ============================================================
# 睡眠
# ============================================================
with sleep_tab:
    st.subheader("新規記録")
    with st.form("sleep_form"):
        bedtime_date = st.date_input("就寝日")
        bedtime_time = st.time_input("就寝時刻")
        wake_date = st.date_input("起床日")
        wake_time_value = st.time_input("起床時刻")
        submitted_sleep = st.form_submit_button("記録する")

    if submitted_sleep:
        bedtime = combine_jst_to_utc(bedtime_date, bedtime_time)
        wake_time = combine_jst_to_utc(wake_date, wake_time_value)
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
            st.rerun()

    st.divider()
    st.subheader("過去の記録")
    sleep_service = get_sleep_service()
    sleep_logs = sorted(
        sleep_service.list_sleep_logs(user_id), key=lambda s: s.bedtime, reverse=True
    )[:_MAX_HISTORY_ROWS]

    if not sleep_logs:
        st.info("まだ記録がありません。")
    else:
        st.dataframe(
            pd.DataFrame(
                {
                    "就寝": [format_datetime_jst(s.bedtime) for s in sleep_logs],
                    "起床": [format_datetime_jst(s.wake_time) for s in sleep_logs],
                    "睡眠時間(分)": [s.duration_minutes for s in sleep_logs],
                    "品質": [
                        s.quality.value if s.quality is not None else "-"
                        for s in sleep_logs
                    ],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        selected_sleep = st.selectbox(
            "編集する記録を選択",
            options=sleep_logs,
            format_func=lambda s: (
                f"{format_datetime_jst(s.bedtime)} 就寝 ({s.duration_minutes}分)"
            ),
            key="sleep_select",
        )

        if selected_sleep is not None:
            with st.form(f"sleep_edit_form_{selected_sleep.sleep_log_id}"):
                edit_bedtime_date = st.date_input(
                    "就寝日", value=jst_date_of(selected_sleep.bedtime)
                )
                edit_bedtime_time = st.time_input(
                    "就寝時刻", value=jst_time_of(selected_sleep.bedtime)
                )
                edit_wake_date = st.date_input(
                    "起床日", value=jst_date_of(selected_sleep.wake_time)
                )
                edit_wake_time = st.time_input(
                    "起床時刻", value=jst_time_of(selected_sleep.wake_time)
                )
                col1, col2 = st.columns(2)
                update_sleep_clicked = col1.form_submit_button("更新する")
                delete_sleep_clicked = col2.form_submit_button("削除する")

            if update_sleep_clicked:
                new_bedtime = combine_jst_to_utc(edit_bedtime_date, edit_bedtime_time)
                new_wake_time = combine_jst_to_utc(edit_wake_date, edit_wake_time)
                if new_wake_time <= new_bedtime:
                    st.error("起床時刻は就寝時刻より後にしてください。")
                else:
                    updated_sleep = SleepLog(
                        sleep_log_id=selected_sleep.sleep_log_id,
                        user_id=user_id,
                        bedtime=new_bedtime,
                        wake_time=new_wake_time,
                        quality=selected_sleep.quality,
                    )
                    sleep_service.update_sleep_log(updated_sleep)
                    st.success("更新しました。")
                    st.rerun()

            if delete_sleep_clicked:
                sleep_service.delete_sleep_log(user_id, selected_sleep.sleep_log_id)
                st.success("削除しました。")
                st.rerun()


# ============================================================
# 体重
# ============================================================
with weight_tab:
    st.subheader("新規記録")
    with st.form("weight_form"):
        weight_date = st.date_input("日付", value=date.today(), key="weight_date")
        weight_time = st.time_input(
            "時刻", value=datetime.now().time(), key="weight_time"
        )
        weight_kg = st.number_input("体重(kg)", min_value=0.0, step=0.1)
        submitted_weight = st.form_submit_button("記録する")

    if submitted_weight:
        weight_log = WeightLog(
            weight_log_id=uuid4(),
            user_id=user_id,
            recorded_at=combine_jst_to_utc(weight_date, weight_time),
            weight_kg=weight_kg,
        )
        get_weight_service().record_weight_log(weight_log)
        st.success("体重記録を保存しました。")
        st.rerun()

    st.divider()
    st.subheader("過去の記録")
    weight_service = get_weight_service()
    weight_logs = sorted(
        weight_service.list_weight_logs(user_id),
        key=lambda w: w.recorded_at,
        reverse=True,
    )[:_MAX_HISTORY_ROWS]

    if not weight_logs:
        st.info("まだ記録がありません。")
    else:
        st.dataframe(
            pd.DataFrame(
                {
                    "日時": [format_datetime_jst(w.recorded_at) for w in weight_logs],
                    "体重(kg)": [w.weight_kg for w in weight_logs],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        selected_weight = st.selectbox(
            "編集する記録を選択",
            options=weight_logs,
            format_func=lambda w: (
                f"{format_datetime_jst(w.recorded_at)} {w.weight_kg}kg"
            ),
            key="weight_select",
        )

        if selected_weight is not None:
            with st.form(f"weight_edit_form_{selected_weight.weight_log_id}"):
                edit_weight_date = st.date_input(
                    "日付", value=jst_date_of(selected_weight.recorded_at)
                )
                edit_weight_time = st.time_input(
                    "時刻", value=jst_time_of(selected_weight.recorded_at)
                )
                edit_weight_kg = st.number_input(
                    "体重(kg)", min_value=0.0, step=0.1, value=selected_weight.weight_kg
                )
                col1, col2 = st.columns(2)
                update_weight_clicked = col1.form_submit_button("更新する")
                delete_weight_clicked = col2.form_submit_button("削除する")

            if update_weight_clicked:
                updated_weight = WeightLog(
                    weight_log_id=selected_weight.weight_log_id,
                    user_id=user_id,
                    recorded_at=combine_jst_to_utc(edit_weight_date, edit_weight_time),
                    weight_kg=edit_weight_kg,
                )
                weight_service.update_weight_log(updated_weight)
                st.success("更新しました。")
                st.rerun()

            if delete_weight_clicked:
                weight_service.delete_weight_log(user_id, selected_weight.weight_log_id)
                st.success("削除しました。")
                st.rerun()


# ============================================================
# 体調
# ============================================================
with health_tab:
    st.subheader("新規記録")
    with st.form("health_form"):
        health_date = st.date_input("日付", value=date.today(), key="health_date")
        health_time = st.time_input(
            "時刻", value=datetime.now().time(), key="health_time"
        )
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
            recorded_at=combine_jst_to_utc(health_date, health_time),
            condition_score=condition_score,
            symptoms=symptoms,
            memo=health_memo or None,
        )
        get_health_service().record_health_log(health_log)
        st.success("体調記録を保存しました。")
        st.rerun()

    st.divider()
    st.subheader("過去の記録")
    health_service = get_health_service()
    health_logs = sorted(
        health_service.list_health_logs(user_id),
        key=lambda h: h.recorded_at,
        reverse=True,
    )[:_MAX_HISTORY_ROWS]

    if not health_logs:
        st.info("まだ記録がありません。")
    else:
        st.dataframe(
            pd.DataFrame(
                {
                    "日時": [format_datetime_jst(h.recorded_at) for h in health_logs],
                    "スコア": [h.condition_score for h in health_logs],
                    "症状": [", ".join(h.symptoms) for h in health_logs],
                    "メモ": [h.memo or "" for h in health_logs],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        selected_health_index = st.selectbox(
            "編集する記録を選択",
            options=range(len(health_logs)),
            format_func=lambda i: (
                f"{format_datetime_jst(health_logs[i].recorded_at)} "
                f"スコア{health_logs[i].condition_score}"
            ),
            key="health_select",
        )
        selected_health = (
            health_logs[selected_health_index]
            if selected_health_index is not None
            else None
        )

        if selected_health is not None:
            with st.form(f"health_edit_form_{selected_health.health_log_id}"):
                edit_health_date = st.date_input(
                    "日付", value=jst_date_of(selected_health.recorded_at)
                )
                edit_health_time = st.time_input(
                    "時刻", value=jst_time_of(selected_health.recorded_at)
                )
                edit_condition_score = st.slider(
                    "体調スコア(1=不調 〜 5=良好)",
                    min_value=1,
                    max_value=5,
                    value=selected_health.condition_score or 3,
                )
                edit_symptoms_text = st.text_input(
                    "症状(カンマ区切り、任意)",
                    value=", ".join(selected_health.symptoms),
                )
                edit_health_memo = st.text_input(
                    "メモ(任意)", value=selected_health.memo or ""
                )
                col1, col2 = st.columns(2)
                update_health_clicked = col1.form_submit_button("更新する")
                delete_health_clicked = col2.form_submit_button("削除する")

            if update_health_clicked:
                edit_symptoms = [
                    s.strip() for s in edit_symptoms_text.split(",") if s.strip()
                ]
                updated_health = HealthLog(
                    health_log_id=selected_health.health_log_id,
                    user_id=user_id,
                    recorded_at=combine_jst_to_utc(edit_health_date, edit_health_time),
                    condition_score=edit_condition_score,
                    symptoms=edit_symptoms,
                    memo=edit_health_memo or None,
                )
                health_service.update_health_log(updated_health)
                st.success("更新しました。")
                st.rerun()

            if delete_health_clicked:
                health_service.delete_health_log(user_id, selected_health.health_log_id)
                st.success("削除しました。")
                st.rerun()
