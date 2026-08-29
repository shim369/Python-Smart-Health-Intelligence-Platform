"""ログ入力ページ。

食事・運動・睡眠・体重・体調・学習の記録をタブで切り替えて入力する。
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

from collections.abc import Callable  # noqa: E402
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
from components.learning_form import (  # noqa: E402
    combine_duration_minutes,
    join_comma_list,
    join_lines_list,
    join_slash_list,
    split_comma_list,
    split_duration_minutes,
    split_lines_list,
    split_slash_list,
)
from components.quick_entry import (  # noqa: E402
    exercise_template_to_entry,
    frequent_exercise_templates,
    frequent_learning_keywords,
    frequent_meal_templates,
    most_recent_learning_log,
    most_recent_meal,
)
from components.workout_form import (  # noqa: E402
    build_workout_log,
    entries_to_rows,
    format_exercise_line,
    rows_to_entries,
    workout_log_to_rows,
)
from services import (  # noqa: E402
    get_health_service,
    get_learning_service,
    get_meal_service,
    get_sleep_service,
    get_weight_service,
    get_workout_service,
)

from health_intelligence.ai.errors import AIProviderError  # noqa: E402
from health_intelligence.domain.enums import (  # noqa: E402
    LearningCategory,
    LearningLocation,
    MealType,
)
from health_intelligence.domain.models import (  # noqa: E402
    HealthLog,
    LearningLog,
    MealLog,
    SleepLog,
    WeightLog,
    WorkoutLog,
)

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title("📝 ログ入力")

meal_tab, workout_tab, sleep_tab, weight_tab, health_tab, learning_tab = st.tabs(
    ["食事", "運動", "睡眠", "体重", "体調", "学習"]
)

_LEARNING_CATEGORY_LABELS: dict[LearningCategory, str] = {
    LearningCategory.EXAM_STUDY: "試験勉強",
    LearningCategory.PORTFOLIO_DEV: "PF開発",
    LearningCategory.RESEARCH: "調べ物",
    LearningCategory.CAREER_STRATEGY: "キャリア・プロダクト戦略設計",
}

_LEARNING_LOCATION_LABELS: dict[LearningLocation | None, str] = {
    None: "未選択",
    LearningLocation.HOME: "自宅",
    LearningLocation.GYM: "ジム",
    LearningLocation.COWORKING_SPACE: "コワーキングスペース",
    LearningLocation.CAFE: "カフェ",
}

_MAX_HISTORY_ROWS = 30
"""過去の記録セクションに表示する最大件数(新しい順)。"""


# ============================================================
# 食事
# ============================================================
@st.dialog("食事記録を編集")
def _meal_edit_dialog(log: MealLog) -> None:
    meal_service = get_meal_service()
    edit_date = st.date_input("日付", value=jst_date_of(log.consumed_at))
    edit_time = st.time_input("時刻", value=jst_time_of(log.consumed_at))
    edit_meal_type = st.selectbox(
        "食事区分",
        options=list(MealType),
        index=list(MealType).index(log.meal_type),
        format_func=lambda m: m.value,
    )
    edit_calories = st.number_input("カロリー(kcal)", min_value=0.0, step=10.0, value=log.calories)
    edit_protein_g = st.number_input("タンパク質(g)", min_value=0.0, step=1.0, value=log.protein_g)
    edit_fat_g = st.number_input("脂質(g)", min_value=0.0, step=1.0, value=log.fat_g)
    edit_carbohydrate_g = st.number_input(
        "炭水化物(g)", min_value=0.0, step=1.0, value=log.carbohydrate_g
    )
    edit_memo = st.text_input("メモ(任意)", value=log.memo or "")
    delete_confirmed = st.checkbox(
        "本当に削除しますか?(元に戻せません)", key=f"meal_delete_confirm_{log.meal_log_id}"
    )
    col1, col2 = st.columns(2)
    if col1.button(
        "更新する", type="primary", key=f"meal_update_{log.meal_log_id}", width="stretch"
    ):
        updated = MealLog(
            meal_log_id=log.meal_log_id,
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
    if col2.button("削除する", key=f"meal_delete_{log.meal_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning("削除するには「本当に削除しますか?」にチェックを入れてください。")
        else:
            meal_service.delete_meal_log(user_id, log.meal_log_id)
            st.success("削除しました。")
            st.rerun()


with meal_tab:
    st.subheader("新規記録")

    all_meal_logs = get_meal_service().list_meal_logs(user_id)
    last_meal = most_recent_meal(all_meal_logs)
    meal_templates = frequent_meal_templates(all_meal_logs)

    quick_meal_col1, quick_meal_col2 = st.columns(2)
    with quick_meal_col1:
        if st.button(
            "前回と同じ内容を入力",
            key="meal_repeat_button",
            disabled=last_meal is None,
            width="stretch",
        ):
            assert last_meal is not None
            st.session_state["meal_type_input"] = last_meal.meal_type
            st.session_state["meal_calories_input"] = last_meal.calories
            st.session_state["meal_protein_input"] = last_meal.protein_g
            st.session_state["meal_fat_input"] = last_meal.fat_g
            st.session_state["meal_carb_input"] = last_meal.carbohydrate_g
            st.session_state["meal_memo"] = last_meal.memo or ""
            st.rerun()
    with quick_meal_col2:
        if meal_templates:
            selected_meal_template = st.selectbox(
                "よく使う食事",
                options=meal_templates,
                format_func=lambda t: f"{t.memo}({t.usage_count}回)",
                key="meal_template_select",
                label_visibility="collapsed",
            )
            if (
                st.button("選んだ食事を入力", key="meal_template_apply_button")
                and selected_meal_template is not None
            ):
                st.session_state["meal_type_input"] = selected_meal_template.meal_type
                st.session_state["meal_calories_input"] = selected_meal_template.calories
                st.session_state["meal_protein_input"] = selected_meal_template.protein_g
                st.session_state["meal_fat_input"] = selected_meal_template.fat_g
                st.session_state["meal_carb_input"] = selected_meal_template.carbohydrate_g
                st.session_state["meal_memo"] = selected_meal_template.memo
                st.rerun()
        else:
            st.caption("よく使う食事はまだありません(メモ付きで記録すると候補に出ます)。")

    st.caption(
        "食べたものを文章で入力すると、AIがカロリー・PFCを推定してフォームに"
        "反映します(あくまで目安です。記録前に下記フォームで確認・修正してください)。"
    )
    meal_description = st.text_input(
        "食べたもの",
        placeholder="例: 納豆1パック、ご飯茶碗1杯",
        key="meal_description",
    )
    if st.button("AIで栄養を推定", key="meal_estimate_button"):
        if not meal_description.strip():
            st.warning("食べたものを入力してください。")
        else:
            with st.spinner("栄養を推定しています..."):
                try:
                    estimated = get_meal_service().estimate_nutrition(meal_description)
                except AIProviderError as e:
                    st.error(f"栄養推定に失敗しました: {e}")
                else:
                    st.session_state["meal_calories_input"] = estimated.calories
                    st.session_state["meal_protein_input"] = estimated.protein_g
                    st.session_state["meal_fat_input"] = estimated.fat_g
                    st.session_state["meal_carb_input"] = estimated.carbohydrate_g
                    st.success(
                        "推定結果を下記フォームに反映しました。"
                        "必要に応じて修正してから記録してください。"
                    )
                    st.rerun()

    with st.form("meal_form"):
        meal_date = st.date_input("日付", value=date.today(), key="meal_date")
        meal_time = st.time_input("時刻", value=datetime.now().time(), key="meal_time")
        meal_type = st.selectbox(
            "食事区分",
            options=list(MealType),
            format_func=lambda m: m.value,
            key="meal_type_input",
        )
        calories = st.number_input(
            "カロリー(kcal)", min_value=0.0, step=10.0, key="meal_calories_input"
        )
        protein_g = st.number_input(
            "タンパク質(g)", min_value=0.0, step=1.0, key="meal_protein_input"
        )
        fat_g = st.number_input("脂質(g)", min_value=0.0, step=1.0, key="meal_fat_input")
        carbohydrate_g = st.number_input(
            "炭水化物(g)", min_value=0.0, step=1.0, key="meal_carb_input"
        )
        memo = st.text_input("メモ(任意)", key="meal_memo")
        submitted = st.form_submit_button("記録する", type="primary")

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
        for key in (
            "meal_description",
            "meal_type_input",
            "meal_calories_input",
            "meal_protein_input",
            "meal_fat_input",
            "meal_carb_input",
            "meal_memo",
        ):
            st.session_state.pop(key, None)
        st.success("食事記録を保存しました。")
        st.rerun()

    st.divider()
    st.subheader("過去の記録")
    meal_logs = sorted(all_meal_logs, key=lambda m: m.consumed_at, reverse=True)[:_MAX_HISTORY_ROWS]

    if not meal_logs:
        st.info("まだ記録がありません。")
    else:
        meal_table_event = st.dataframe(
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
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="meal_table",
        )
        meal_selected_rows = meal_table_event.selection.rows
        selected_meal = meal_logs[meal_selected_rows[0]] if meal_selected_rows else None

        if (
            st.button("編集する", key="meal_edit_open_button", disabled=selected_meal is None)
            and selected_meal is not None
        ):
            _meal_edit_dialog(selected_meal)


# ============================================================
# 運動
# ============================================================
def _new_workout_entry(category: str = "strength") -> dict[str, object]:
    """種目カード1件分の初期状態を生成する。`_id`はウィジェットキーの安定した
    紐付け用で、保存時(entries_to_rows)には無視される。
    """
    return {
        "_id": uuid4().hex,
        "exercise_name": "",
        "category": category,
        "duration_minutes": None,
        "sets": [{"reps": None, "weight_kg": None}],
    }


def _render_workout_entries(entries: list[dict[str, object]], *, key_prefix: str) -> None:
    """種目カードのリストをスマホでもタップしやすい縦積みUIとして描画する。

    `entries`(セッション状態のリスト)を直接書き換えるため、呼び出し側は
    描画後にそのまま`entries_to_rows(entries)`で保存用の行データへ変換できる。
    種目の削除・セット追加/削除はその場でst.rerun()し、data_editorの
    ような表操作ではなく単純なタップ操作で完結させる。
    """
    remove_entry_id: str | None = None

    for entry in entries:
        eid = entry["_id"]
        with st.container(border=True):
            name_col, del_col = st.columns([4, 1])
            entry["exercise_name"] = name_col.text_input(
                "種目名",
                value=entry.get("exercise_name") or "",
                placeholder="例: レッグプレス",
                key=f"{key_prefix}_wo_name_{eid}",
            )
            if del_col.button("🗑削除", key=f"{key_prefix}_wo_del_{eid}", width="stretch"):
                remove_entry_id = eid

            entry["category"] = st.radio(
                "カテゴリ",
                options=["strength", "cardio"],
                format_func=lambda c: "筋トレ" if c == "strength" else "有酸素",
                horizontal=True,
                index=0 if entry.get("category", "strength") == "strength" else 1,
                key=f"{key_prefix}_wo_cat_{eid}",
            )

            if entry["category"] == "cardio":
                entry["duration_minutes"] = st.number_input(
                    "時間(分)",
                    min_value=0,
                    step=1,
                    value=entry.get("duration_minutes"),
                    key=f"{key_prefix}_wo_dur_{eid}",
                )
            else:
                sets = entry.setdefault("sets", [])
                if not sets:
                    sets.append({"reps": None, "weight_kg": None})

                remove_set_index: int | None = None
                for i, workout_set in enumerate(sets):
                    label_col, reps_col, weight_col, set_del_col = st.columns([1, 2, 2, 1])
                    label_col.markdown(f"**{i + 1}セット目**")
                    workout_set["reps"] = reps_col.number_input(
                        "回数",
                        min_value=0,
                        step=1,
                        value=workout_set.get("reps"),
                        key=f"{key_prefix}_wo_reps_{eid}_{i}",
                        label_visibility="collapsed",
                    )
                    workout_set["weight_kg"] = weight_col.number_input(
                        "重量(kg)",
                        min_value=0.0,
                        step=1.0,
                        value=workout_set.get("weight_kg"),
                        key=f"{key_prefix}_wo_weight_{eid}_{i}",
                        label_visibility="collapsed",
                    )
                    if len(sets) > 1 and set_del_col.button(
                        "×", key=f"{key_prefix}_wo_setdel_{eid}_{i}"
                    ):
                        remove_set_index = i

                if remove_set_index is not None:
                    sets.pop(remove_set_index)
                    st.rerun(scope="fragment")

                if st.button(
                    "+ セット追加",
                    key=f"{key_prefix}_wo_addset_{eid}",
                    width="stretch",
                ):
                    sets.append({"reps": None, "weight_kg": None})
                    st.rerun(scope="fragment")

    if remove_entry_id is not None:
        entries[:] = [e for e in entries if e["_id"] != remove_entry_id]
        st.rerun(scope="fragment")


@st.dialog("運動記録を編集", width="large")
def _workout_edit_dialog(log: WorkoutLog) -> None:
    workout_service = get_workout_service()
    edit_workout_date = st.date_input(
        "日付", value=jst_date_of(log.performed_at), key=f"workout_edit_date_{log.workout_log_id}"
    )
    edit_workout_time = st.time_input(
        "時刻", value=jst_time_of(log.performed_at), key=f"workout_edit_time_{log.workout_log_id}"
    )
    edit_state_key = f"workout_edit_entries_{log.workout_log_id}"
    if edit_state_key not in st.session_state:
        edit_entries = rows_to_entries(workout_log_to_rows(log))
        for e in edit_entries:
            e["_id"] = uuid4().hex
        st.session_state[edit_state_key] = edit_entries or [_new_workout_entry()]

    _render_workout_entries(
        st.session_state[edit_state_key], key_prefix=f"edit_{log.workout_log_id}"
    )

    if st.button(
        "+ 種目を追加",
        key=f"workout_edit_add_entry_{log.workout_log_id}",
        width="stretch",
    ):
        st.session_state[edit_state_key].append(_new_workout_entry())
        st.rerun(scope="fragment")

    workout_delete_confirmed = st.checkbox(
        "本当に削除しますか?(元に戻せません)",
        key=f"workout_delete_confirm_{log.workout_log_id}",
    )
    col1, col2 = st.columns(2)
    if col1.button("更新する", key=f"workout_update_{log.workout_log_id}", type="primary"):
        updated_rows = entries_to_rows(st.session_state[edit_state_key])
        updated_workout = build_workout_log(
            updated_rows,
            user_id=user_id,
            performed_at=combine_jst_to_utc(edit_workout_date, edit_workout_time),
            workout_log_id=log.workout_log_id,
        )
        if not updated_workout.exercises:
            st.error("有効な種目が入力されていません。")
        else:
            workout_service.update_workout_log(updated_workout)
            st.session_state.pop(edit_state_key, None)
            st.success("更新しました。")
            st.rerun()

    if col2.button("削除する", key=f"workout_delete_{log.workout_log_id}"):
        if not workout_delete_confirmed:
            st.warning("削除するには「本当に削除しますか?」にチェックを入れてください。")
        else:
            workout_service.delete_workout_log(user_id, log.workout_log_id)
            st.session_state.pop(edit_state_key, None)
            st.success("削除しました。")
            st.rerun()


@st.fragment
def _render_workout_new_record_section(all_workout_logs: list[WorkoutLog]) -> None:
    """新規記録フォームをフラグメント化し、種目名・回数などの入力による
    再実行をこのフラグメント内に留める(食事・体重等はst.form内の入力
    なのでウィジェット変更のたびに全体再実行されないが、運動は種目の
    動的追加/削除に対応するためst.formが使えず、フラグメント化しないと
    1文字入力するたびに全タブ分のDB再読み込みが走り体感が重くなる)。
    """
    if "workout_entries" not in st.session_state:
        st.session_state["workout_entries"] = [_new_workout_entry()]

    exercise_templates = frequent_exercise_templates(all_workout_logs)

    workout_date = st.date_input("日付", value=date.today(), key="workout_date")
    workout_time = st.time_input("時刻", value=datetime.now().time(), key="workout_time")

    quick_workout_col1, quick_workout_col2 = st.columns([1, 2])
    with quick_workout_col1:
        if st.button(
            "前回と同じメニューを入力",
            key="workout_repeat_button",
            disabled=not all_workout_logs,
            width="stretch",
        ):
            last_workout = max(all_workout_logs, key=lambda w: w.performed_at)
            new_entries = rows_to_entries(workout_log_to_rows(last_workout))
            for e in new_entries:
                e["_id"] = uuid4().hex
            st.session_state["workout_entries"] = new_entries or [_new_workout_entry()]
            st.rerun(scope="fragment")
    with quick_workout_col2:
        if exercise_templates:
            selected_exercise_templates = st.multiselect(
                "よく使う種目を追加",
                options=exercise_templates,
                format_func=lambda t: f"{t.exercise_name}({t.category.value}・{t.usage_count}回)",
                key="workout_template_select",
                label_visibility="collapsed",
            )
            if st.button("選択した種目を追加する", key="workout_template_apply_button"):
                current_entries = [
                    e
                    for e in st.session_state["workout_entries"]
                    if str(e.get("exercise_name") or "").strip()
                ]
                for t in selected_exercise_templates:
                    new_entry = exercise_template_to_entry(t)
                    new_entry["_id"] = uuid4().hex
                    current_entries.append(new_entry)
                st.session_state["workout_entries"] = current_entries or [_new_workout_entry()]
                st.rerun(scope="fragment")
        else:
            st.caption("よく使う種目はまだありません。")

    _render_workout_entries(st.session_state["workout_entries"], key_prefix="new")

    if st.button("+ 種目を追加", key="workout_add_entry", width="stretch"):
        st.session_state["workout_entries"].append(_new_workout_entry())
        st.rerun(scope="fragment")

    if st.button(
        "運動記録を保存する",
        type="primary",
        width="stretch",
    ):
        rows = entries_to_rows(st.session_state["workout_entries"])
        workout_log = build_workout_log(
            rows,
            user_id=user_id,
            performed_at=combine_jst_to_utc(workout_date, workout_time),
        )
        if not workout_log.exercises:
            st.error("有効な種目が入力されていません。")
        else:
            get_workout_service().record_workout_log(workout_log)
            st.session_state["workout_entries"] = [_new_workout_entry()]
            st.success(f"運動記録({len(workout_log.exercises)}種目)を保存しました。")
            st.rerun()


with workout_tab:
    st.subheader("新規記録")

    all_workout_logs = get_workout_service().list_workout_logs(user_id)
    _render_workout_new_record_section(all_workout_logs)

    st.divider()
    st.subheader("過去の記録")
    workout_logs = sorted(
        all_workout_logs,
        key=lambda w: w.performed_at,
        reverse=True,
    )[:_MAX_HISTORY_ROWS]

    if not workout_logs:
        st.info("まだ記録がありません。")
    else:
        workout_table_event = st.dataframe(
            pd.DataFrame(
                {
                    "日時": [format_datetime_jst(w.performed_at) for w in workout_logs],
                    "種目数": [len(w.exercises) for w in workout_logs],
                    "種目": [
                        " / ".join(format_exercise_line(e) for e in w.exercises)
                        for w in workout_logs
                    ],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="workout_table",
        )
        workout_selected_rows = workout_table_event.selection.rows
        selected_workout = workout_logs[workout_selected_rows[0]] if workout_selected_rows else None

        if (
            st.button("編集する", key="workout_edit_open_button", disabled=selected_workout is None)
            and selected_workout is not None
        ):
            _workout_edit_dialog(selected_workout)


# ============================================================
# 睡眠
# ============================================================
@st.dialog("睡眠記録を編集")
def _sleep_edit_dialog(log: SleepLog) -> None:
    sleep_service = get_sleep_service()
    edit_bedtime_date = st.date_input("就寝日", value=jst_date_of(log.bedtime))
    edit_bedtime_time = st.time_input("就寝時刻", value=jst_time_of(log.bedtime))
    edit_wake_date = st.date_input("起床日", value=jst_date_of(log.wake_time))
    edit_wake_time = st.time_input("起床時刻", value=jst_time_of(log.wake_time))
    delete_confirmed = st.checkbox(
        "本当に削除しますか?(元に戻せません)", key=f"sleep_delete_confirm_{log.sleep_log_id}"
    )
    col1, col2 = st.columns(2)
    if col1.button(
        "更新する", type="primary", key=f"sleep_update_{log.sleep_log_id}", width="stretch"
    ):
        new_bedtime = combine_jst_to_utc(edit_bedtime_date, edit_bedtime_time)
        new_wake_time = combine_jst_to_utc(edit_wake_date, edit_wake_time)
        if new_wake_time <= new_bedtime:
            st.error("起床時刻は就寝時刻より後にしてください。")
        else:
            updated_sleep = SleepLog(
                sleep_log_id=log.sleep_log_id,
                user_id=user_id,
                bedtime=new_bedtime,
                wake_time=new_wake_time,
                quality=log.quality,
            )
            sleep_service.update_sleep_log(updated_sleep)
            st.success("更新しました。")
            st.rerun()
    if col2.button("削除する", key=f"sleep_delete_{log.sleep_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning("削除するには「本当に削除しますか?」にチェックを入れてください。")
        else:
            sleep_service.delete_sleep_log(user_id, log.sleep_log_id)
            st.success("削除しました。")
            st.rerun()


with sleep_tab:
    st.subheader("新規記録")
    with st.form("sleep_form"):
        bedtime_date = st.date_input("就寝日")
        bedtime_time = st.time_input("就寝時刻")
        wake_date = st.date_input("起床日")
        wake_time_value = st.time_input("起床時刻")
        submitted_sleep = st.form_submit_button("記録する", type="primary")

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
        sleep_table_event = st.dataframe(
            pd.DataFrame(
                {
                    "就寝": [format_datetime_jst(s.bedtime) for s in sleep_logs],
                    "起床": [format_datetime_jst(s.wake_time) for s in sleep_logs],
                    "睡眠時間(分)": [s.duration_minutes for s in sleep_logs],
                    "品質": [s.quality.value if s.quality is not None else "-" for s in sleep_logs],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="sleep_table",
        )
        sleep_selected_rows = sleep_table_event.selection.rows
        selected_sleep = sleep_logs[sleep_selected_rows[0]] if sleep_selected_rows else None

        if (
            st.button("編集する", key="sleep_edit_open_button", disabled=selected_sleep is None)
            and selected_sleep is not None
        ):
            _sleep_edit_dialog(selected_sleep)


# ============================================================
# 体重
# ============================================================
@st.dialog("体重記録を編集")
def _weight_edit_dialog(log: WeightLog) -> None:
    weight_service = get_weight_service()
    edit_weight_date = st.date_input("日付", value=jst_date_of(log.recorded_at))
    edit_weight_time = st.time_input("時刻", value=jst_time_of(log.recorded_at))
    edit_weight_kg = st.number_input("体重(kg)", min_value=0.0, step=0.1, value=log.weight_kg)
    delete_confirmed = st.checkbox(
        "本当に削除しますか?(元に戻せません)", key=f"weight_delete_confirm_{log.weight_log_id}"
    )
    col1, col2 = st.columns(2)
    if col1.button(
        "更新する",
        type="primary",
        key=f"weight_update_{log.weight_log_id}",
        width="stretch",
    ):
        updated_weight = WeightLog(
            weight_log_id=log.weight_log_id,
            user_id=user_id,
            recorded_at=combine_jst_to_utc(edit_weight_date, edit_weight_time),
            weight_kg=edit_weight_kg,
        )
        weight_service.update_weight_log(updated_weight)
        st.success("更新しました。")
        st.rerun()
    if col2.button("削除する", key=f"weight_delete_{log.weight_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning("削除するには「本当に削除しますか?」にチェックを入れてください。")
        else:
            weight_service.delete_weight_log(user_id, log.weight_log_id)
            st.success("削除しました。")
            st.rerun()


with weight_tab:
    st.subheader("新規記録")
    with st.form("weight_form"):
        weight_date = st.date_input("日付", value=date.today(), key="weight_date")
        weight_time = st.time_input("時刻", value=datetime.now().time(), key="weight_time")
        weight_kg = st.number_input("体重(kg)", min_value=0.0, step=0.1)
        submitted_weight = st.form_submit_button("記録する", type="primary")

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
        weight_table_event = st.dataframe(
            pd.DataFrame(
                {
                    "日時": [format_datetime_jst(w.recorded_at) for w in weight_logs],
                    "体重(kg)": [w.weight_kg for w in weight_logs],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="weight_table",
        )
        weight_selected_rows = weight_table_event.selection.rows
        selected_weight = weight_logs[weight_selected_rows[0]] if weight_selected_rows else None

        if (
            st.button("編集する", key="weight_edit_open_button", disabled=selected_weight is None)
            and selected_weight is not None
        ):
            _weight_edit_dialog(selected_weight)


# ============================================================
# 体調
# ============================================================
@st.dialog("体調記録を編集")
def _health_edit_dialog(log: HealthLog) -> None:
    health_service = get_health_service()
    edit_health_date = st.date_input("日付", value=jst_date_of(log.recorded_at))
    edit_health_time = st.time_input("時刻", value=jst_time_of(log.recorded_at))
    edit_condition_score = st.slider(
        "体調スコア(1=不調 〜 5=良好)", min_value=1, max_value=5, value=log.condition_score or 3
    )
    edit_symptoms_text = st.text_input("症状(カンマ区切り、任意)", value=", ".join(log.symptoms))
    edit_health_memo = st.text_input("メモ(任意)", value=log.memo or "")
    delete_confirmed = st.checkbox(
        "本当に削除しますか?(元に戻せません)", key=f"health_delete_confirm_{log.health_log_id}"
    )
    col1, col2 = st.columns(2)
    if col1.button(
        "更新する",
        type="primary",
        key=f"health_update_{log.health_log_id}",
        width="stretch",
    ):
        edit_symptoms = [s.strip() for s in edit_symptoms_text.split(",") if s.strip()]
        updated_health = HealthLog(
            health_log_id=log.health_log_id,
            user_id=user_id,
            recorded_at=combine_jst_to_utc(edit_health_date, edit_health_time),
            condition_score=edit_condition_score,
            symptoms=edit_symptoms,
            memo=edit_health_memo or None,
        )
        health_service.update_health_log(updated_health)
        st.success("更新しました。")
        st.rerun()
    if col2.button("削除する", key=f"health_delete_{log.health_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning("削除するには「本当に削除しますか?」にチェックを入れてください。")
        else:
            health_service.delete_health_log(user_id, log.health_log_id)
            st.success("削除しました。")
            st.rerun()


with health_tab:
    st.subheader("新規記録")
    with st.form("health_form"):
        health_date = st.date_input("日付", value=date.today(), key="health_date")
        health_time = st.time_input("時刻", value=datetime.now().time(), key="health_time")
        condition_score = st.slider(
            "体調スコア(1=不調 〜 5=良好)", min_value=1, max_value=5, value=3
        )
        symptoms_text = st.text_input("症状(カンマ区切り、任意)", placeholder="例: 頭痛, 倦怠感")
        health_memo = st.text_input("メモ(任意)", key="health_memo")
        submitted_health = st.form_submit_button("記録する", type="primary")

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
        health_table_event = st.dataframe(
            pd.DataFrame(
                {
                    "日時": [format_datetime_jst(h.recorded_at) for h in health_logs],
                    "スコア": [h.condition_score for h in health_logs],
                    "症状": [", ".join(h.symptoms) for h in health_logs],
                    "メモ": [h.memo or "" for h in health_logs],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="health_table",
        )
        health_selected_rows = health_table_event.selection.rows
        selected_health = health_logs[health_selected_rows[0]] if health_selected_rows else None

        if (
            st.button("編集する", key="health_edit_open_button", disabled=selected_health is None)
            and selected_health is not None
        ):
            _health_edit_dialog(selected_health)


# ============================================================
# 学習
# ============================================================
def _render_learning_category_fields(
    category: LearningCategory,
    *,
    key: Callable[[str], str],
    prefill: LearningLog | None,
) -> dict[str, object]:
    """カテゴリに応じた学習ログの入力欄を描画し、構築済みの値を返す。

    新規記録・編集フォームの両方から呼び出す。`key`はウィジェットキーを
    (新規記録ではそのまま、編集ではレコードIDを付与して)組み立てる
    関数、`prefill`はNoneなら新規記録(値はセッション状態頼み)、
    指定すればその記録の値をデフォルト値として表示する。
    """
    content: str | None = None
    breakdown: list[str] = []
    duration_minutes: int | None = None
    keywords: list[str] = []
    notes: list[str] = []

    if category in (LearningCategory.EXAM_STUDY, LearningCategory.PORTFOLIO_DEV):
        is_exam = category == LearningCategory.EXAM_STUDY
        content_kwargs = {} if prefill is None else {"value": prefill.content or ""}
        content_placeholder = "例: ○○問題集 過去問" if is_exam else "例: 個人ブログのSSR化"
        content = (
            st.text_input(
                "勉強内容" if is_exam else "PF開発内容",
                placeholder=content_placeholder,
                key=key("learning_content_input"),
                **content_kwargs,
            )
            or None
        )

        if is_exam:
            breakdown_kwargs = (
                {} if prefill is None else {"value": join_comma_list(prefill.breakdown)}
            )
            breakdown_text = st.text_input(
                "内訳(カンマ区切り)",
                placeholder="例: Chapter3, Chapter5",
                key=key("learning_breakdown_text"),
                **breakdown_kwargs,
            )
            breakdown = split_comma_list(breakdown_text)

        prefill_hours, prefill_minutes = (
            (0, 0) if prefill is None else split_duration_minutes(prefill.duration_minutes)
        )
        duration_hours_col, duration_minutes_col = st.columns(2)
        duration_hours_kwargs = {} if prefill is None else {"value": prefill_hours}
        duration_hours = duration_hours_col.number_input(
            "時間",
            min_value=0,
            step=1,
            key=key("learning_duration_hours"),
            **duration_hours_kwargs,
        )
        duration_minutes_kwargs = {} if prefill is None else {"value": prefill_minutes}
        duration_minutes_input = duration_minutes_col.number_input(
            "分",
            min_value=0,
            max_value=59,
            step=5,
            key=key("learning_duration_minutes_input"),
            **duration_minutes_kwargs,
        )
        duration_minutes = combine_duration_minutes(duration_hours, duration_minutes_input)

        keywords_kwargs = {} if prefill is None else {"value": join_slash_list(prefill.keywords)}
        keywords_text = st.text_input(
            "技術的成長キーワード(スラッシュ区切り)",
            placeholder="例: Python / SQL",
            key=key("learning_keywords_text"),
            **keywords_kwargs,
        )
        keywords = split_slash_list(keywords_text)

    elif category == LearningCategory.RESEARCH:
        keywords_kwargs = {} if prefill is None else {"value": join_slash_list(prefill.keywords)}
        keywords_text = st.text_input(
            "技術的成長キーワード(スラッシュ区切り)",
            placeholder="例: Python / SQL",
            key=key("learning_keywords_text"),
            **keywords_kwargs,
        )
        keywords = split_slash_list(keywords_text)

    elif category == LearningCategory.CAREER_STRATEGY:
        prefill_hours_career = (
            0.0
            if prefill is None or prefill.duration_minutes is None
            else prefill.duration_minutes / 60
        )
        duration_hours_career_kwargs = {} if prefill is None else {"value": prefill_hours_career}
        duration_hours_career = st.number_input(
            "時間(h)",
            min_value=0.0,
            step=0.5,
            key=key("learning_duration_hours_career"),
            **duration_hours_career_kwargs,
        )
        duration_minutes = combine_duration_minutes(duration_hours_career, None)

        notes_kwargs = {} if prefill is None else {"value": join_lines_list(prefill.notes)}
        notes_text = st.text_area(
            "箇条書きメモ(1行1項目)",
            placeholder="例: ・案A: 新規事業\n・案B: 既存機能強化",
            key=key("learning_notes_text"),
            **notes_kwargs,
        )
        notes = split_lines_list(notes_text)

    return {
        "content": content,
        "breakdown": breakdown,
        "duration_minutes": duration_minutes,
        "keywords": keywords,
        "notes": notes,
    }


@st.dialog("学習記録を編集", width="large")
def _learning_edit_dialog(log: LearningLog) -> None:
    learning_service = get_learning_service()
    edit_learning_date = st.date_input(
        "日付", value=jst_date_of(log.started_at), key=f"learning_edit_date_{log.learning_log_id}"
    )
    edit_learning_time = st.time_input(
        "時刻", value=jst_time_of(log.started_at), key=f"learning_edit_time_{log.learning_log_id}"
    )
    edit_learning_location = st.selectbox(
        "場所",
        options=[None, *LearningLocation],
        index=[None, *LearningLocation].index(log.location),
        format_func=lambda location: _LEARNING_LOCATION_LABELS[location],
        key=f"learning_edit_location_{log.learning_log_id}",
    )
    edit_learning_category = st.selectbox(
        "カテゴリ",
        options=list(LearningCategory),
        index=list(LearningCategory).index(log.category),
        format_func=lambda category: _LEARNING_CATEGORY_LABELS[category],
        key=f"learning_edit_category_{log.learning_log_id}",
    )

    edit_learning_fields = _render_learning_category_fields(
        edit_learning_category,
        key=(lambda base, _id=log.learning_log_id: f"{base}_{_id}"),
        prefill=log,
    )

    delete_confirmed = st.checkbox(
        "本当に削除しますか?(元に戻せません)",
        key=f"learning_delete_confirm_{log.learning_log_id}",
    )
    col1, col2 = st.columns(2)
    if col1.button(
        "更新する",
        key=f"learning_update_{log.learning_log_id}",
        type="primary",
        width="stretch",
    ):
        updated_learning = LearningLog(
            learning_log_id=log.learning_log_id,
            user_id=user_id,
            started_at=combine_jst_to_utc(edit_learning_date, edit_learning_time),
            category=edit_learning_category,
            location=edit_learning_location,
            content=edit_learning_fields["content"],
            breakdown=edit_learning_fields["breakdown"],
            duration_minutes=edit_learning_fields["duration_minutes"],
            keywords=edit_learning_fields["keywords"],
            notes=edit_learning_fields["notes"],
        )
        learning_service.update_learning_log(updated_learning)
        st.success("更新しました。")
        st.rerun()
    if col2.button("削除する", key=f"learning_delete_{log.learning_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning("削除するには「本当に削除しますか?」にチェックを入れてください。")
        else:
            learning_service.delete_learning_log(user_id, log.learning_log_id)
            st.success("削除しました。")
            st.rerun()


@st.fragment
def _render_learning_new_record_section(all_learning_logs: list[LearningLog]) -> None:
    """新規記録フォームをフラグメント化し、内容・キーワード等の入力による
    再実行をこのフラグメント内に留める(運動タブと同じ理由で動的な
    キーワード追加等に対応するためst.formが使えず、フラグメント化しないと
    1文字入力するたびに全タブ分のDB再読み込みが走り体感が重くなる)。
    """
    last_learning_log = most_recent_learning_log(all_learning_logs)

    if st.button(
        "前回と同じ内容を入力",
        key="learning_repeat_button",
        disabled=last_learning_log is None,
        width="stretch",
    ):
        assert last_learning_log is not None
        st.session_state["learning_category_input"] = last_learning_log.category
        st.session_state["learning_location_input"] = last_learning_log.location
        st.session_state["learning_content_input"] = last_learning_log.content or ""
        st.session_state["learning_breakdown_text"] = join_comma_list(last_learning_log.breakdown)
        prefill_hours, prefill_minutes = split_duration_minutes(last_learning_log.duration_minutes)
        st.session_state["learning_duration_hours"] = prefill_hours
        st.session_state["learning_duration_minutes_input"] = prefill_minutes
        st.session_state["learning_duration_hours_career"] = (
            last_learning_log.duration_minutes / 60
            if last_learning_log.duration_minutes is not None
            else 0.0
        )
        st.session_state["learning_keywords_text"] = join_slash_list(last_learning_log.keywords)
        st.session_state["learning_notes_text"] = join_lines_list(last_learning_log.notes)
        st.rerun(scope="fragment")

    learning_date = st.date_input("日付", value=date.today(), key="learning_date")
    learning_time = st.time_input("時刻", value=datetime.now().time(), key="learning_time")
    learning_location = st.selectbox(
        "場所",
        options=[None, *LearningLocation],
        format_func=lambda location: _LEARNING_LOCATION_LABELS[location],
        key="learning_location_input",
    )
    learning_category = st.selectbox(
        "カテゴリ",
        options=list(LearningCategory),
        format_func=lambda category: _LEARNING_CATEGORY_LABELS[category],
        key="learning_category_input",
    )

    if learning_category != LearningCategory.CAREER_STRATEGY:
        keyword_templates = frequent_learning_keywords(all_learning_logs)
        if keyword_templates:
            keyword_usage_counts = {t.keyword: t.usage_count for t in keyword_templates}
            selected_keywords = st.multiselect(
                "よく使うキーワードを追加",
                options=list(keyword_usage_counts),
                format_func=lambda k: f"{k}({keyword_usage_counts[k]}回)",
                key="learning_keyword_template_select",
                label_visibility="collapsed",
            )
            if st.button(
                "選択したキーワードを追加する",
                key="learning_keyword_template_apply_button",
            ):
                current_keywords = split_slash_list(
                    st.session_state.get("learning_keywords_text", "")
                )
                for keyword in selected_keywords:
                    if keyword not in current_keywords:
                        current_keywords.append(keyword)
                st.session_state["learning_keywords_text"] = join_slash_list(current_keywords)
                st.rerun(scope="fragment")
        else:
            st.caption("よく使うキーワードはまだありません。")

    learning_fields = _render_learning_category_fields(
        learning_category, key=lambda base: base, prefill=None
    )

    if st.button(
        "記録する",
        key="learning_submit_button",
        type="primary",
        width="stretch",
    ):
        learning_log = LearningLog(
            learning_log_id=uuid4(),
            user_id=user_id,
            started_at=combine_jst_to_utc(learning_date, learning_time),
            category=learning_category,
            location=learning_location,
            content=learning_fields["content"],
            breakdown=learning_fields["breakdown"],
            duration_minutes=learning_fields["duration_minutes"],
            keywords=learning_fields["keywords"],
            notes=learning_fields["notes"],
        )
        get_learning_service().record_learning_log(learning_log)
        for key_name in (
            "learning_category_input",
            "learning_location_input",
            "learning_content_input",
            "learning_breakdown_text",
            "learning_duration_hours",
            "learning_duration_minutes_input",
            "learning_duration_hours_career",
            "learning_keywords_text",
            "learning_notes_text",
        ):
            st.session_state.pop(key_name, None)
        st.success("学習記録を保存しました。")
        st.rerun()


with learning_tab:
    st.subheader("新規記録")

    all_learning_logs = get_learning_service().list_learning_logs(user_id)
    _render_learning_new_record_section(all_learning_logs)

    st.divider()
    st.subheader("過去の記録")
    learning_service = get_learning_service()
    learning_logs = sorted(
        all_learning_logs, key=lambda learning: learning.started_at, reverse=True
    )[:_MAX_HISTORY_ROWS]

    if not learning_logs:
        st.info("まだ記録がありません。")
    else:
        learning_table_event = st.dataframe(
            pd.DataFrame(
                {
                    "日時": [
                        format_datetime_jst(learning.started_at) for learning in learning_logs
                    ],
                    "カテゴリ": [
                        _LEARNING_CATEGORY_LABELS[learning.category] for learning in learning_logs
                    ],
                    "場所": [
                        _LEARNING_LOCATION_LABELS[learning.location] for learning in learning_logs
                    ],
                    "内容": [
                        learning.content or (", ".join(learning.keywords) or "-")
                        for learning in learning_logs
                    ],
                    "時間(分)": [
                        learning.duration_minutes if learning.duration_minutes is not None else "-"
                        for learning in learning_logs
                    ],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="learning_table",
        )
        learning_selected_rows = learning_table_event.selection.rows
        selected_learning = (
            learning_logs[learning_selected_rows[0]] if learning_selected_rows else None
        )

        if (
            st.button(
                "編集する", key="learning_edit_open_button", disabled=selected_learning is None
            )
            and selected_learning is not None
        ):
            _learning_edit_dialog(selected_learning)
