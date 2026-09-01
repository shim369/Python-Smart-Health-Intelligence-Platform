"""「今日」ページ。

1日分のP(計画)/D(実績)/C(振り返り)/A(改善)を1画面にまとめて記録する
(requirements.md 4.4節・4.5節)。旧「ログ入力」ページにあった食事・運動・
睡眠・体重・体調・学習の各タブはこのページへ統合した。学習ログ
(既存LearningLog)は新設計のGoal/Task方式とデータモデルとしては
当面併存させるが、UI上は他ドメインと同様にD:実績の
「学習・PF開発・仕事」タブ内にまとめて表示する。

日付・時刻の入力は日本時間(JST)で行い、保存時にUTCへ変換する
(components/formatting.py参照)。DB上は一貫してUTCで保持する。
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

app_dir = Path(__file__).resolve().parents[1]
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.daily_plan_form import resolve_initial_plan_task_ids  # noqa: E402
from components.daily_task_log_form import nearest_duration_option  # noqa: E402
from components.formatting import (  # noqa: E402
    combine_jst_to_utc,
    format_datetime_jst,
    jst_date_of,
    jst_time_of,
)
from components.goal_task_labels import (  # noqa: E402
    DURATION_OPTIONS,
    format_duration_option,
    goal_category_labels,
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
from components.pdca_status import compute_pdca_status  # noqa: E402
from components.quick_entry import (  # noqa: E402
    exercise_template_to_entry,
    frequent_exercise_templates,
    frequent_learning_keywords,
    frequent_meal_templates,
    most_recent_learning_log,
    most_recent_meal,
)
from components.shopping_memo import append_recipe_ingredients  # noqa: E402
from components.workout_form import (  # noqa: E402
    build_workout_log,
    entries_to_rows,
    format_exercise_line,
    rows_to_entries,
    workout_log_to_rows,
)
from i18n import t  # noqa: E402
from services import (  # noqa: E402
    get_daily_journal_service,
    get_health_service,
    get_learning_service,
    get_meal_service,
    get_recipe_service,
    get_sleep_service,
    get_task_service,
    get_weight_service,
    get_workout_service,
)

from health_intelligence.ai.errors import AIProviderError  # noqa: E402
from health_intelligence.domain.enums import (  # noqa: E402
    GoalCategory,
    LearningCategory,
    LearningLocation,
    MealType,
    TaskLogType,
)
from health_intelligence.domain.models import (  # noqa: E402
    DailyTaskLog,
    HealthLog,
    LearningLog,
    MealLog,
    SleepLog,
    Task,
    WeightLog,
    WorkoutLog,
)

auth_state = require_login()
user_id = auth_state.require_user_id()

_MAX_HISTORY_ROWS = 30

daily_journal_service = get_daily_journal_service()
task_service = get_task_service()
meal_service = get_meal_service()
workout_service = get_workout_service()
sleep_service = get_sleep_service()
weight_service = get_weight_service()
health_service = get_health_service()
recipe_service = get_recipe_service()
learning_service = get_learning_service()

_LEARNING_CATEGORY_LABELS: dict[LearningCategory, str] = {
    LearningCategory.EXAM_STUDY: t("試験勉強"),
    LearningCategory.PORTFOLIO_DEV: t("PF開発"),
    LearningCategory.RESEARCH: t("調べ物"),
    LearningCategory.CAREER_STRATEGY: t("キャリア・プロダクト戦略設計"),
}

_LEARNING_LOCATION_LABELS: dict[LearningLocation | None, str] = {
    None: t("未選択"),
    LearningLocation.HOME: t("自宅"),
    LearningLocation.GYM: t("ジム"),
    LearningLocation.COWORKING_SPACE: t("コワーキングスペース"),
    LearningLocation.CAFE: t("カフェ"),
}


# ============================================================
# 食事: 編集ダイアログ
# ============================================================
@st.dialog(t("食事記録を編集"))
def _meal_edit_dialog(log: MealLog) -> None:
    edit_date = st.date_input(t("日付"), value=jst_date_of(log.consumed_at))
    edit_time = st.time_input(t("時刻"), value=jst_time_of(log.consumed_at))
    edit_meal_type = st.selectbox(
        t("食事区分"),
        options=list(MealType),
        index=list(MealType).index(log.meal_type),
        format_func=lambda m: m.value,
    )
    edit_calories = st.number_input(
        t("カロリー(kcal)"), min_value=0.0, step=10.0, value=log.calories
    )
    edit_protein_g = st.number_input(
        t("タンパク質(g)"), min_value=0.0, step=1.0, value=log.protein_g
    )
    edit_fat_g = st.number_input(t("脂質(g)"), min_value=0.0, step=1.0, value=log.fat_g)
    edit_carbohydrate_g = st.number_input(
        t("炭水化物(g)"), min_value=0.0, step=1.0, value=log.carbohydrate_g
    )
    edit_memo = st.text_input(t("メモ(任意)"), value=log.memo or "")
    delete_confirmed = st.checkbox(
        t("本当に削除しますか?(元に戻せません)"), key=f"today_meal_delete_confirm_{log.meal_log_id}"
    )
    col1, col2 = st.columns(2)
    if col1.button(
        t("更新する"), type="primary", key=f"today_meal_update_{log.meal_log_id}", width="stretch"
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
        st.success(t("更新しました。"))
        st.rerun()
    if col2.button(t("削除する"), key=f"today_meal_delete_{log.meal_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning(t("削除するには「本当に削除しますか?」にチェックを入れてください。"))
        else:
            meal_service.delete_meal_log(user_id, log.meal_log_id)
            st.success(t("削除しました。"))
            st.rerun()


# ============================================================
# 運動: 種目カードUI・編集ダイアログ
# ============================================================
def _new_workout_entry(category: str = "strength") -> dict[str, object]:
    return {
        "_id": uuid4().hex,
        "exercise_name": "",
        "category": category,
        "duration_minutes": None,
        "sets": [{"reps": None, "weight_kg": None}],
    }


def _render_workout_entries(entries: list[dict[str, object]], *, key_prefix: str) -> None:
    remove_entry_id: str | None = None

    for entry in entries:
        eid = entry["_id"]
        with st.container(border=True):
            name_col, del_col = st.columns([4, 1])
            entry["exercise_name"] = name_col.text_input(
                t("種目名"),
                value=entry.get("exercise_name") or "",
                placeholder=t("例: レッグプレス"),
                key=f"{key_prefix}_wo_name_{eid}",
            )
            if del_col.button(t("🗑削除"), key=f"{key_prefix}_wo_del_{eid}", width="stretch"):
                remove_entry_id = eid

            entry["category"] = st.radio(
                t("カテゴリ"),
                options=["strength", "cardio"],
                format_func=lambda c: t("筋トレ") if c == "strength" else t("有酸素"),
                horizontal=True,
                index=0 if entry.get("category", "strength") == "strength" else 1,
                key=f"{key_prefix}_wo_cat_{eid}",
            )

            if entry["category"] == "cardio":
                entry["duration_minutes"] = st.number_input(
                    t("時間(分)"),
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
                    label_col.markdown(t("**{n}セット目**", n=i + 1))
                    workout_set["reps"] = reps_col.number_input(
                        t("回数"),
                        min_value=0,
                        step=1,
                        value=workout_set.get("reps"),
                        key=f"{key_prefix}_wo_reps_{eid}_{i}",
                        label_visibility="collapsed",
                    )
                    workout_set["weight_kg"] = weight_col.number_input(
                        t("重量(kg)"),
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
                    t("+ セット追加"),
                    key=f"{key_prefix}_wo_addset_{eid}",
                    width="stretch",
                ):
                    sets.append({"reps": None, "weight_kg": None})
                    st.rerun(scope="fragment")

    if remove_entry_id is not None:
        entries[:] = [e for e in entries if e["_id"] != remove_entry_id]
        st.rerun(scope="fragment")


@st.dialog(t("運動記録を編集"), width="large")
def _workout_edit_dialog(log: WorkoutLog) -> None:
    edit_workout_date = st.date_input(
        t("日付"),
        value=jst_date_of(log.performed_at),
        key=f"today_workout_edit_date_{log.workout_log_id}",
    )
    edit_workout_time = st.time_input(
        t("時刻"),
        value=jst_time_of(log.performed_at),
        key=f"today_workout_edit_time_{log.workout_log_id}",
    )
    edit_state_key = f"today_workout_edit_entries_{log.workout_log_id}"
    if edit_state_key not in st.session_state:
        edit_entries = rows_to_entries(workout_log_to_rows(log))
        for e in edit_entries:
            e["_id"] = uuid4().hex
        st.session_state[edit_state_key] = edit_entries or [_new_workout_entry()]

    _render_workout_entries(
        st.session_state[edit_state_key], key_prefix=f"today_edit_{log.workout_log_id}"
    )

    if st.button(
        t("+ 種目を追加"),
        key=f"today_workout_edit_add_entry_{log.workout_log_id}",
        width="stretch",
    ):
        st.session_state[edit_state_key].append(_new_workout_entry())
        st.rerun(scope="fragment")

    workout_delete_confirmed = st.checkbox(
        t("本当に削除しますか?(元に戻せません)"),
        key=f"today_workout_delete_confirm_{log.workout_log_id}",
    )
    col1, col2 = st.columns(2)
    if col1.button(t("更新する"), key=f"today_workout_update_{log.workout_log_id}", type="primary"):
        updated_rows = entries_to_rows(st.session_state[edit_state_key])
        updated_workout = build_workout_log(
            updated_rows,
            user_id=user_id,
            performed_at=combine_jst_to_utc(edit_workout_date, edit_workout_time),
            workout_log_id=log.workout_log_id,
        )
        if not updated_workout.exercises:
            st.error(t("有効な種目が入力されていません。"))
        else:
            workout_service.update_workout_log(updated_workout)
            st.session_state.pop(edit_state_key, None)
            st.success(t("更新しました。"))
            st.rerun()

    if col2.button(t("削除する"), key=f"today_workout_delete_{log.workout_log_id}"):
        if not workout_delete_confirmed:
            st.warning(t("削除するには「本当に削除しますか?」にチェックを入れてください。"))
        else:
            workout_service.delete_workout_log(user_id, log.workout_log_id)
            st.session_state.pop(edit_state_key, None)
            st.success(t("削除しました。"))
            st.rerun()


@st.fragment
def _render_workout_new_record_section(
    all_workout_logs: list[WorkoutLog], journal_date_value: date
) -> None:
    if "today_workout_entries" not in st.session_state:
        st.session_state["today_workout_entries"] = [_new_workout_entry()]

    exercise_templates = frequent_exercise_templates(all_workout_logs)

    workout_date = st.date_input(t("日付"), value=journal_date_value, key="today_workout_date")
    workout_time = st.time_input(t("時刻"), value=datetime.now().time(), key="today_workout_time")

    quick_workout_col1, quick_workout_col2 = st.columns([1, 2])
    with quick_workout_col1:
        if st.button(
            t("前回と同じメニューを入力"),
            key="today_workout_repeat_button",
            disabled=not all_workout_logs,
            width="stretch",
        ):
            last_workout = max(all_workout_logs, key=lambda w: w.performed_at)
            new_entries = rows_to_entries(workout_log_to_rows(last_workout))
            for e in new_entries:
                e["_id"] = uuid4().hex
            st.session_state["today_workout_entries"] = new_entries or [_new_workout_entry()]
            st.rerun(scope="fragment")
    with quick_workout_col2:
        if exercise_templates:
            selected_exercise_templates = st.multiselect(
                t("よく使う種目を追加"),
                options=exercise_templates,
                format_func=lambda et: t(
                    "{name}({category}・{count}回)",
                    name=et.exercise_name,
                    category=et.category.value,
                    count=et.usage_count,
                ),
                key="today_workout_template_select",
                label_visibility="collapsed",
            )
            if st.button(t("選択した種目を追加する"), key="today_workout_template_apply_button"):
                current_entries = [
                    e
                    for e in st.session_state["today_workout_entries"]
                    if str(e.get("exercise_name") or "").strip()
                ]
                for template in selected_exercise_templates:
                    new_entry = exercise_template_to_entry(template)
                    new_entry["_id"] = uuid4().hex
                    current_entries.append(new_entry)
                st.session_state["today_workout_entries"] = current_entries or [
                    _new_workout_entry()
                ]
                st.rerun(scope="fragment")
        else:
            st.caption(t("よく使う種目はまだありません。"))

    _render_workout_entries(st.session_state["today_workout_entries"], key_prefix="today_new")

    if st.button(t("+ 種目を追加"), key="today_workout_add_entry", width="stretch"):
        st.session_state["today_workout_entries"].append(_new_workout_entry())
        st.rerun(scope="fragment")

    if st.button(t("運動記録を保存する"), type="primary", width="stretch"):
        rows = entries_to_rows(st.session_state["today_workout_entries"])
        workout_log = build_workout_log(
            rows,
            user_id=user_id,
            performed_at=combine_jst_to_utc(workout_date, workout_time),
        )
        if not workout_log.exercises:
            st.error(t("有効な種目が入力されていません。"))
        else:
            workout_service.record_workout_log(workout_log)
            st.session_state["today_workout_entries"] = [_new_workout_entry()]
            st.success(t("運動記録({count}種目)を保存しました。", count=len(workout_log.exercises)))
            st.rerun()


# ============================================================
# 睡眠: 編集ダイアログ
# ============================================================
@st.dialog(t("睡眠記録を編集"))
def _sleep_edit_dialog(log: SleepLog) -> None:
    edit_bedtime_date = st.date_input(t("就寝日"), value=jst_date_of(log.bedtime))
    edit_bedtime_time = st.time_input(t("就寝時刻"), value=jst_time_of(log.bedtime))
    edit_wake_date = st.date_input(t("起床日"), value=jst_date_of(log.wake_time))
    edit_wake_time = st.time_input(t("起床時刻"), value=jst_time_of(log.wake_time))
    delete_confirmed = st.checkbox(
        t("本当に削除しますか?(元に戻せません)"),
        key=f"today_sleep_delete_confirm_{log.sleep_log_id}",
    )
    col1, col2 = st.columns(2)
    if col1.button(
        t("更新する"), type="primary", key=f"today_sleep_update_{log.sleep_log_id}", width="stretch"
    ):
        new_bedtime = combine_jst_to_utc(edit_bedtime_date, edit_bedtime_time)
        new_wake_time = combine_jst_to_utc(edit_wake_date, edit_wake_time)
        if new_wake_time <= new_bedtime:
            st.error(t("起床時刻は就寝時刻より後にしてください。"))
        else:
            updated_sleep = SleepLog(
                sleep_log_id=log.sleep_log_id,
                user_id=user_id,
                bedtime=new_bedtime,
                wake_time=new_wake_time,
                quality=log.quality,
            )
            sleep_service.update_sleep_log(updated_sleep)
            st.success(t("更新しました。"))
            st.rerun()
    if col2.button(t("削除する"), key=f"today_sleep_delete_{log.sleep_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning(t("削除するには「本当に削除しますか?」にチェックを入れてください。"))
        else:
            sleep_service.delete_sleep_log(user_id, log.sleep_log_id)
            st.success(t("削除しました。"))
            st.rerun()


# ============================================================
# 体重: 編集ダイアログ
# ============================================================
@st.dialog(t("体重記録を編集"))
def _weight_edit_dialog(log: WeightLog) -> None:
    edit_weight_date = st.date_input(t("日付"), value=jst_date_of(log.recorded_at))
    edit_weight_time = st.time_input(t("時刻"), value=jst_time_of(log.recorded_at))
    edit_weight_kg = st.number_input(t("体重(kg)"), min_value=0.0, step=0.1, value=log.weight_kg)
    delete_confirmed = st.checkbox(
        t("本当に削除しますか?(元に戻せません)"),
        key=f"today_weight_delete_confirm_{log.weight_log_id}",
    )
    col1, col2 = st.columns(2)
    if col1.button(
        t("更新する"),
        type="primary",
        key=f"today_weight_update_{log.weight_log_id}",
        width="stretch",
    ):
        updated_weight = WeightLog(
            weight_log_id=log.weight_log_id,
            user_id=user_id,
            recorded_at=combine_jst_to_utc(edit_weight_date, edit_weight_time),
            weight_kg=edit_weight_kg,
        )
        weight_service.update_weight_log(updated_weight)
        st.success(t("更新しました。"))
        st.rerun()
    if col2.button(t("削除する"), key=f"today_weight_delete_{log.weight_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning(t("削除するには「本当に削除しますか?」にチェックを入れてください。"))
        else:
            weight_service.delete_weight_log(user_id, log.weight_log_id)
            st.success(t("削除しました。"))
            st.rerun()


# ============================================================
# 体調: 編集ダイアログ(5軸拡張、design.md 7章)
# ============================================================
def _condition_axis_sliders(*, key_prefix: str, initial: HealthLog | None) -> dict[str, int]:
    return {
        "condition_score": st.slider(
            t("総合スコア(1=不調 〜 5=良好)"),
            min_value=1,
            max_value=5,
            value=(initial.condition_score if initial else 3) or 3,
            key=f"{key_prefix}_condition_score",
        ),
        "morning_condition": st.slider(
            t("朝の体調(1〜5)"),
            min_value=1,
            max_value=5,
            value=(initial.morning_condition if initial else 3) or 3,
            key=f"{key_prefix}_morning_condition",
        ),
        "evening_condition": st.slider(
            t("夜の体調(1〜5)"),
            min_value=1,
            max_value=5,
            value=(initial.evening_condition if initial else 3) or 3,
            key=f"{key_prefix}_evening_condition",
        ),
        "mental_score": st.slider(
            t("メンタル(1〜5)"),
            min_value=1,
            max_value=5,
            value=(initial.mental_score if initial else 3) or 3,
            key=f"{key_prefix}_mental_score",
        ),
        "fatigue_score": st.slider(
            t("疲労(1〜5)"),
            min_value=1,
            max_value=5,
            value=(initial.fatigue_score if initial else 3) or 3,
            key=f"{key_prefix}_fatigue_score",
        ),
        "stress_score": st.slider(
            t("ストレス(1〜5)"),
            min_value=1,
            max_value=5,
            value=(initial.stress_score if initial else 3) or 3,
            key=f"{key_prefix}_stress_score",
        ),
    }


@st.dialog(t("体調記録を編集"), width="large")
def _health_edit_dialog(log: HealthLog) -> None:
    edit_health_date = st.date_input(t("日付"), value=jst_date_of(log.recorded_at))
    edit_health_time = st.time_input(t("時刻"), value=jst_time_of(log.recorded_at))
    axes = _condition_axis_sliders(key_prefix=f"today_health_edit_{log.health_log_id}", initial=log)
    edit_symptoms_text = st.text_input(t("症状(カンマ区切り、任意)"), value=", ".join(log.symptoms))
    edit_health_memo = st.text_input(t("メモ(任意)"), value=log.memo or "")
    delete_confirmed = st.checkbox(
        t("本当に削除しますか?(元に戻せません)"),
        key=f"today_health_delete_confirm_{log.health_log_id}",
    )
    col1, col2 = st.columns(2)
    if col1.button(
        t("更新する"),
        type="primary",
        key=f"today_health_update_{log.health_log_id}",
        width="stretch",
    ):
        edit_symptoms = [s.strip() for s in edit_symptoms_text.split(",") if s.strip()]
        updated_health = HealthLog(
            health_log_id=log.health_log_id,
            user_id=user_id,
            recorded_at=combine_jst_to_utc(edit_health_date, edit_health_time),
            symptoms=edit_symptoms,
            memo=edit_health_memo or None,
            **axes,
        )
        health_service.update_health_log(updated_health)
        st.success(t("更新しました。"))
        st.rerun()
    if col2.button(t("削除する"), key=f"today_health_delete_{log.health_log_id}", width="stretch"):
        if not delete_confirmed:
            st.warning(t("削除するには「本当に削除しますか?」にチェックを入れてください。"))
        else:
            health_service.delete_health_log(user_id, log.health_log_id)
            st.success(t("削除しました。"))
            st.rerun()


# ============================================================
# 学習(自由記述ログ): 入力欄・編集ダイアログ
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
        content_placeholder = t("例: ○○問題集 過去問") if is_exam else t("例: 個人ブログのSSR化")
        content = (
            st.text_input(
                t("勉強内容") if is_exam else t("PF開発内容"),
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
                t("内訳(カンマ区切り)"),
                placeholder=t("例: Chapter3, Chapter5"),
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
            t("時間"),
            min_value=0,
            step=1,
            key=key("learning_duration_hours"),
            **duration_hours_kwargs,
        )
        duration_minutes_kwargs = {} if prefill is None else {"value": prefill_minutes}
        duration_minutes_input = duration_minutes_col.number_input(
            t("分"),
            min_value=0,
            max_value=59,
            step=5,
            key=key("learning_duration_minutes_input"),
            **duration_minutes_kwargs,
        )
        duration_minutes = combine_duration_minutes(duration_hours, duration_minutes_input)

        keywords_kwargs = {} if prefill is None else {"value": join_slash_list(prefill.keywords)}
        keywords_text = st.text_input(
            t("技術的成長キーワード(スラッシュ区切り)"),
            placeholder=t("例: Python / SQL"),
            key=key("learning_keywords_text"),
            **keywords_kwargs,
        )
        keywords = split_slash_list(keywords_text)

    elif category == LearningCategory.RESEARCH:
        keywords_kwargs = {} if prefill is None else {"value": join_slash_list(prefill.keywords)}
        keywords_text = st.text_input(
            t("技術的成長キーワード(スラッシュ区切り)"),
            placeholder=t("例: Python / SQL"),
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
            t("時間(h)"),
            min_value=0.0,
            step=0.5,
            key=key("learning_duration_hours_career"),
            **duration_hours_career_kwargs,
        )
        duration_minutes = combine_duration_minutes(duration_hours_career, None)

        notes_kwargs = {} if prefill is None else {"value": join_lines_list(prefill.notes)}
        notes_text = st.text_area(
            t("箇条書きメモ(1行1項目)"),
            placeholder=t("例: ・案A: 新規事業\n・案B: 既存機能強化"),
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


@st.dialog(t("学習記録を編集"), width="large")
def _learning_edit_dialog(log: LearningLog) -> None:
    edit_learning_date = st.date_input(
        t("日付"),
        value=jst_date_of(log.started_at),
        key=f"today_learning_edit_date_{log.learning_log_id}",
    )
    edit_learning_time = st.time_input(
        t("時刻"),
        value=jst_time_of(log.started_at),
        key=f"today_learning_edit_time_{log.learning_log_id}",
    )
    edit_learning_location = st.selectbox(
        t("場所"),
        options=[None, *LearningLocation],
        index=[None, *LearningLocation].index(log.location),
        format_func=lambda location: _LEARNING_LOCATION_LABELS[location],
        key=f"today_learning_edit_location_{log.learning_log_id}",
    )
    edit_learning_category = st.selectbox(
        t("カテゴリ"),
        options=list(LearningCategory),
        index=list(LearningCategory).index(log.category),
        format_func=lambda category: _LEARNING_CATEGORY_LABELS[category],
        key=f"today_learning_edit_category_{log.learning_log_id}",
    )

    edit_learning_fields = _render_learning_category_fields(
        edit_learning_category,
        key=(lambda base, _id=log.learning_log_id: f"today_{base}_{_id}"),
        prefill=log,
    )

    delete_confirmed = st.checkbox(
        t("本当に削除しますか?(元に戻せません)"),
        key=f"today_learning_delete_confirm_{log.learning_log_id}",
    )
    col1, col2 = st.columns(2)
    if col1.button(
        t("更新する"),
        key=f"today_learning_update_{log.learning_log_id}",
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
        st.success(t("更新しました。"))
        st.rerun()
    if col2.button(
        t("削除する"), key=f"today_learning_delete_{log.learning_log_id}", width="stretch"
    ):
        if not delete_confirmed:
            st.warning(t("削除するには「本当に削除しますか?」にチェックを入れてください。"))
        else:
            learning_service.delete_learning_log(user_id, log.learning_log_id)
            st.success(t("削除しました。"))
            st.rerun()


@st.fragment
def _render_learning_new_record_section(
    all_learning_logs: list[LearningLog], journal_date_value: date
) -> None:
    """新規記録フォームをフラグメント化し、内容・キーワード等の入力による
    再実行をこのフラグメント内に留める(運動タブと同じ理由で動的な
    キーワード追加等に対応するためst.formが使えず、フラグメント化しないと
    1文字入力するたびにページ全体のDB再読み込みが走り体感が重くなる)。
    """
    last_learning_log = most_recent_learning_log(all_learning_logs)

    if st.button(
        t("前回と同じ内容を入力"),
        key="today_learning_repeat_button",
        disabled=last_learning_log is None,
        width="stretch",
    ):
        assert last_learning_log is not None
        st.session_state["today_learning_category_input"] = last_learning_log.category
        st.session_state["today_learning_location_input"] = last_learning_log.location
        st.session_state["today_learning_content_input"] = last_learning_log.content or ""
        st.session_state["today_learning_breakdown_text"] = join_comma_list(
            last_learning_log.breakdown
        )
        prefill_hours, prefill_minutes = split_duration_minutes(last_learning_log.duration_minutes)
        st.session_state["today_learning_duration_hours"] = prefill_hours
        st.session_state["today_learning_duration_minutes_input"] = prefill_minutes
        st.session_state["today_learning_duration_hours_career"] = (
            last_learning_log.duration_minutes / 60
            if last_learning_log.duration_minutes is not None
            else 0.0
        )
        st.session_state["today_learning_keywords_text"] = join_slash_list(
            last_learning_log.keywords
        )
        st.session_state["today_learning_notes_text"] = join_lines_list(last_learning_log.notes)
        st.rerun(scope="fragment")

    learning_date = st.date_input(t("日付"), value=journal_date_value, key="today_learning_date")
    learning_time = st.time_input(t("時刻"), value=datetime.now().time(), key="today_learning_time")
    learning_location = st.selectbox(
        t("場所"),
        options=[None, *LearningLocation],
        format_func=lambda location: _LEARNING_LOCATION_LABELS[location],
        key="today_learning_location_input",
    )
    learning_category = st.selectbox(
        t("カテゴリ"),
        options=list(LearningCategory),
        format_func=lambda category: _LEARNING_CATEGORY_LABELS[category],
        key="today_learning_category_input",
    )

    if learning_category != LearningCategory.CAREER_STRATEGY:
        keyword_templates = frequent_learning_keywords(all_learning_logs)
        if keyword_templates:
            keyword_usage_counts = {kt.keyword: kt.usage_count for kt in keyword_templates}
            selected_keywords = st.multiselect(
                t("よく使うキーワードを追加"),
                options=list(keyword_usage_counts),
                format_func=lambda k: t(
                    "{keyword}({count}回)", keyword=k, count=keyword_usage_counts[k]
                ),
                key="today_learning_keyword_template_select",
                label_visibility="collapsed",
            )
            if st.button(
                t("選択したキーワードを追加する"),
                key="today_learning_keyword_template_apply_button",
            ):
                current_keywords = split_slash_list(
                    st.session_state.get("today_learning_keywords_text", "")
                )
                for keyword in selected_keywords:
                    if keyword not in current_keywords:
                        current_keywords.append(keyword)
                st.session_state["today_learning_keywords_text"] = join_slash_list(current_keywords)
                st.rerun(scope="fragment")
        else:
            st.caption(t("よく使うキーワードはまだありません。"))

    learning_fields = _render_learning_category_fields(
        learning_category, key=lambda base: f"today_{base}", prefill=None
    )

    if st.button(
        t("学習記録を保存する"),
        key="today_learning_submit_button",
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
        learning_service.record_learning_log(learning_log)
        for key_name in (
            "today_learning_category_input",
            "today_learning_location_input",
            "today_learning_content_input",
            "today_learning_breakdown_text",
            "today_learning_duration_hours",
            "today_learning_duration_minutes_input",
            "today_learning_duration_hours_career",
            "today_learning_keywords_text",
            "today_learning_notes_text",
        ):
            st.session_state.pop(key_name, None)
        st.success(t("学習記録を保存しました。"))
        st.rerun()


# ============================================================
# ページ本体
# ============================================================
st.title(":material/today: " + t("今日"))

if "today_journal_date" not in st.session_state:
    st.session_state["today_journal_date"] = date.today()

nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
if nav_col1.button("◀", key="today_prev_date", width="stretch"):
    st.session_state["today_journal_date"] -= timedelta(days=1)
    st.rerun()
if nav_col3.button("▶", key="today_next_date", width="stretch"):
    st.session_state["today_journal_date"] += timedelta(days=1)
    st.rerun()
journal_date: date = st.session_state["today_journal_date"]
nav_col2.markdown(f"### {journal_date.isoformat()}")
date_suffix = journal_date.isoformat()

plan_items = daily_journal_service.list_plan(user_id, journal_date)
task_logs_today = daily_journal_service.list_task_logs(user_id, journal_date)
journal = daily_journal_service.get_journal(user_id, journal_date)

all_meal_logs = meal_service.list_meal_logs(user_id)
all_workout_logs = workout_service.list_workout_logs(user_id)
all_sleep_logs = sleep_service.list_sleep_logs(user_id)
all_weight_logs = weight_service.list_weight_logs(user_id)
all_health_logs = health_service.list_health_logs(user_id)
all_learning_logs = learning_service.list_learning_logs(user_id)

meal_logs_today = [m for m in all_meal_logs if jst_date_of(m.consumed_at) == journal_date]
workout_logs_today = [w for w in all_workout_logs if jst_date_of(w.performed_at) == journal_date]
sleep_logs_today = [s for s in all_sleep_logs if jst_date_of(s.bedtime) == journal_date]
weight_logs_today = [w for w in all_weight_logs if jst_date_of(w.recorded_at) == journal_date]
health_logs_today = [h for h in all_health_logs if jst_date_of(h.recorded_at) == journal_date]
learning_logs_today = [
    log for log in all_learning_logs if jst_date_of(log.started_at) == journal_date
]

pdca_status = compute_pdca_status(
    has_plan=bool(plan_items),
    do_section_counts={
        "meal": len(meal_logs_today),
        "workout": len(workout_logs_today),
        "sleep": len(sleep_logs_today),
        "weight": len(weight_logs_today),
        "health": len(health_logs_today),
        "task_logs": len(task_logs_today) + len(learning_logs_today),
        "household": (
            1 if journal is not None and (journal.shopping_memo or journal.food_expense_yen) else 0
        ),
    },
    has_reflection=bool(journal is not None and journal.reflection_memo),
    has_improvement=bool(journal is not None and journal.improvement_point),
)
st.caption(f"P:{pdca_status.plan}　D:{pdca_status.do}　C:{pdca_status.check}　A:{pdca_status.act}")

yesterday = journal_date - timedelta(days=1)
yesterday_journal = daily_journal_service.get_journal(user_id, yesterday)
if yesterday_journal is not None and yesterday_journal.improvement_point:
    st.info(t("前日の改善点(A): {point}", point=yesterday_journal.improvement_point))

st.divider()

# ------------------------------------------------------------
# ▼ P: 今日の計画
# ------------------------------------------------------------
with st.expander(t("▼ P: 今日の計画"), expanded=True):
    all_tasks = task_service.list_tasks(user_id, include_archived=False)
    tasks_by_category: dict[GoalCategory, list[Task]] = {c: [] for c in GoalCategory}
    for task in all_tasks:
        tasks_by_category[task.category].append(task)

    yesterday_plan_items = daily_journal_service.list_plan(user_id, yesterday)
    today_task_ids = {item.task_id for item in plan_items}
    yesterday_task_ids = {item.task_id for item in yesterday_plan_items}
    initial_task_ids, copied_from_yesterday = resolve_initial_plan_task_ids(
        today_task_ids, yesterday_task_ids
    )
    if copied_from_yesterday and yesterday_task_ids:
        st.caption(
            t("前日の計画を初期表示しています。内容を確認し「Pを保存する」で確定してください。")
        )

    category_labels = goal_category_labels()
    selected_task_ids: set = set()
    for category in GoalCategory:
        category_tasks = tasks_by_category[category]
        task_by_id = {ct.task_id: ct for ct in category_tasks}
        if not task_by_id:
            st.caption(
                t("{category}: まだタスクがありません。", category=category_labels[category])
            )
            continue
        selected = st.multiselect(
            category_labels[category],
            options=list(task_by_id),
            default=[tid for tid in task_by_id if tid in initial_task_ids],
            format_func=lambda tid, m=task_by_id: m[tid].title,
            key=f"today_plan_select_{category.value}_{date_suffix}",
        )
        selected_task_ids.update(selected)

    with st.expander(t("+ その場でタスクを追加(イレギュラー対応)")):
        quick_task_title = st.text_input(t("タイトル"), key=f"today_quick_task_title_{date_suffix}")
        quick_task_category = st.selectbox(
            t("カテゴリ"),
            options=list(GoalCategory),
            format_func=lambda c: category_labels[c],
            key=f"today_quick_task_category_{date_suffix}",
        )
        if st.button(t("追加する"), key=f"today_quick_task_add_{date_suffix}"):
            if not quick_task_title.strip():
                st.warning(t("タイトルを入力してください。"))
            else:
                log_type = (
                    TaskLogType.COUNT_AND_DURATION
                    if quick_task_category
                    in (
                        GoalCategory.STUDY,
                        GoalCategory.PF_DEV,
                        GoalCategory.WORK,
                        GoalCategory.CAREER,
                    )
                    else TaskLogType.PLAN_ONLY
                )
                task_service.create_task(
                    Task(
                        task_id=uuid4(),
                        user_id=user_id,
                        category=quick_task_category,
                        title=quick_task_title.strip(),
                        log_type=log_type,
                        created_at=datetime.now(UTC),
                    )
                )
                st.success(
                    t("タスクを追加しました。上の一覧から選択して「Pを保存する」してください。")
                )
                st.rerun()

    if st.button(t("Pを保存する"), type="primary", key=f"today_plan_save_{date_suffix}"):
        daily_journal_service.save_plan(user_id, journal_date, list(selected_task_ids))
        st.success(t("Pを保存しました。"))
        st.rerun()

st.divider()

# ------------------------------------------------------------
# ▼ D: 実績
# ------------------------------------------------------------
st.subheader(t("▼ D: 実績"))
sleep_condition_tab, meal_tab, task_log_tab, workout_tab, household_tab = st.tabs(
    [t("睡眠・体調"), t("食事"), t("学習・PF開発・仕事"), t("運動"), t("家計")]
)

with sleep_condition_tab:
    st.markdown(f"**{t('睡眠')}**")
    with st.form("today_sleep_form"):
        bedtime_date = st.date_input(
            t("就寝日"), value=journal_date, key="today_sleep_bedtime_date"
        )
        bedtime_time = st.time_input(t("就寝時刻"), key="today_sleep_bedtime_time")
        wake_date = st.date_input(t("起床日"), value=journal_date, key="today_sleep_wake_date")
        wake_time_value = st.time_input(t("起床時刻"), key="today_sleep_wake_time")
        submitted_sleep = st.form_submit_button(t("睡眠記録を保存する"), type="primary")

    if submitted_sleep:
        bedtime = combine_jst_to_utc(bedtime_date, bedtime_time)
        wake_time = combine_jst_to_utc(wake_date, wake_time_value)
        if wake_time <= bedtime:
            st.error(t("起床時刻は就寝時刻より後にしてください。"))
        else:
            sleep_log = SleepLog(
                sleep_log_id=uuid4(), user_id=user_id, bedtime=bedtime, wake_time=wake_time
            )
            sleep_service.record_sleep_log(sleep_log)
            st.success(
                t("睡眠記録({minutes}分)を保存しました。", minutes=sleep_log.duration_minutes)
            )
            st.rerun()

    if sleep_logs_today:
        sleep_table_event = st.dataframe(
            pd.DataFrame(
                {
                    t("就寝"): [format_datetime_jst(s.bedtime) for s in sleep_logs_today],
                    t("起床"): [format_datetime_jst(s.wake_time) for s in sleep_logs_today],
                    t("睡眠時間(分)"): [s.duration_minutes for s in sleep_logs_today],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="today_sleep_table",
        )
        sleep_selected_rows = sleep_table_event.selection.rows
        selected_sleep = sleep_logs_today[sleep_selected_rows[0]] if sleep_selected_rows else None
        if (
            st.button(
                t("編集する"), key="today_sleep_edit_open_button", disabled=selected_sleep is None
            )
            and selected_sleep is not None
        ):
            _sleep_edit_dialog(selected_sleep)

    st.divider()
    st.markdown(f"**{t('体重')}**")
    with st.form("today_weight_form"):
        weight_date = st.date_input(t("日付"), value=journal_date, key="today_weight_date")
        weight_time = st.time_input(t("時刻"), value=datetime.now().time(), key="today_weight_time")
        weight_kg = st.number_input(t("体重(kg)"), min_value=0.0, step=0.1)
        submitted_weight = st.form_submit_button(t("体重記録を保存する"), type="primary")

    if submitted_weight:
        weight_log = WeightLog(
            weight_log_id=uuid4(),
            user_id=user_id,
            recorded_at=combine_jst_to_utc(weight_date, weight_time),
            weight_kg=weight_kg,
        )
        weight_service.record_weight_log(weight_log)
        st.success(t("体重記録を保存しました。"))
        st.rerun()

    if weight_logs_today:
        weight_table_event = st.dataframe(
            pd.DataFrame(
                {
                    t("日時"): [format_datetime_jst(w.recorded_at) for w in weight_logs_today],
                    t("体重(kg)"): [w.weight_kg for w in weight_logs_today],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="today_weight_table",
        )
        weight_selected_rows = weight_table_event.selection.rows
        selected_weight = (
            weight_logs_today[weight_selected_rows[0]] if weight_selected_rows else None
        )
        if (
            st.button(
                t("編集する"), key="today_weight_edit_open_button", disabled=selected_weight is None
            )
            and selected_weight is not None
        ):
            _weight_edit_dialog(selected_weight)

    st.divider()
    st.markdown(f"**{t('体調(5軸)')}**")
    with st.form("today_health_form"):
        health_date = st.date_input(t("日付"), value=journal_date, key="today_health_date")
        health_time = st.time_input(t("時刻"), value=datetime.now().time(), key="today_health_time")
        axes = _condition_axis_sliders(key_prefix="today_health_new", initial=None)
        symptoms_text = st.text_input(
            t("症状(カンマ区切り、任意)"), placeholder=t("例: 頭痛, 倦怠感")
        )
        health_memo = st.text_input(t("メモ(任意)"), key="today_health_memo")
        submitted_health = st.form_submit_button(t("体調記録を保存する"), type="primary")

    if submitted_health:
        symptoms = [s.strip() for s in symptoms_text.split(",") if s.strip()]
        health_log = HealthLog(
            health_log_id=uuid4(),
            user_id=user_id,
            recorded_at=combine_jst_to_utc(health_date, health_time),
            symptoms=symptoms,
            memo=health_memo or None,
            **axes,
        )
        health_service.record_health_log(health_log)
        st.success(t("体調記録を保存しました。"))
        st.rerun()

    if health_logs_today:
        health_table_event = st.dataframe(
            pd.DataFrame(
                {
                    t("日時"): [format_datetime_jst(h.recorded_at) for h in health_logs_today],
                    t("総合"): [h.condition_score for h in health_logs_today],
                    t("朝"): [h.morning_condition for h in health_logs_today],
                    t("夜"): [h.evening_condition for h in health_logs_today],
                    t("メンタル"): [h.mental_score for h in health_logs_today],
                    t("疲労"): [h.fatigue_score for h in health_logs_today],
                    t("ストレス"): [h.stress_score for h in health_logs_today],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="today_health_table",
        )
        health_selected_rows = health_table_event.selection.rows
        selected_health = (
            health_logs_today[health_selected_rows[0]] if health_selected_rows else None
        )
        if (
            st.button(
                t("編集する"), key="today_health_edit_open_button", disabled=selected_health is None
            )
            and selected_health is not None
        ):
            _health_edit_dialog(selected_health)

with meal_tab:
    last_meal = most_recent_meal(all_meal_logs)
    meal_templates = frequent_meal_templates(all_meal_logs)

    quick_meal_col1, quick_meal_col2 = st.columns(2)
    with quick_meal_col1:
        if st.button(
            t("前回と同じ内容を入力"),
            key="today_meal_repeat_button",
            disabled=last_meal is None,
            width="stretch",
        ):
            assert last_meal is not None
            st.session_state["today_meal_type_input"] = last_meal.meal_type
            st.session_state["today_meal_calories_input"] = last_meal.calories
            st.session_state["today_meal_protein_input"] = last_meal.protein_g
            st.session_state["today_meal_fat_input"] = last_meal.fat_g
            st.session_state["today_meal_carb_input"] = last_meal.carbohydrate_g
            st.session_state["today_meal_memo"] = last_meal.memo or ""
            st.rerun()
    with quick_meal_col2:
        if meal_templates:
            selected_meal_template = st.selectbox(
                t("よく使う食事"),
                options=meal_templates,
                format_func=lambda mt: t("{memo}({count}回)", memo=mt.memo, count=mt.usage_count),
                key="today_meal_template_select",
                label_visibility="collapsed",
            )
            if (
                st.button(t("選んだ食事を入力"), key="today_meal_template_apply_button")
                and selected_meal_template is not None
            ):
                st.session_state["today_meal_type_input"] = selected_meal_template.meal_type
                st.session_state["today_meal_calories_input"] = selected_meal_template.calories
                st.session_state["today_meal_protein_input"] = selected_meal_template.protein_g
                st.session_state["today_meal_fat_input"] = selected_meal_template.fat_g
                st.session_state["today_meal_carb_input"] = selected_meal_template.carbohydrate_g
                st.session_state["today_meal_memo"] = selected_meal_template.memo
                st.rerun()
        else:
            st.caption(t("よく使う食事はまだありません(メモ付きで記録すると候補に出ます)。"))

    st.caption(
        t(
            "食べたものを文章で入力すると、AIがカロリー・PFCを推定してフォームに"
            "反映します(あくまで目安です。記録前に下記フォームで確認・修正してください)。"
        )
    )
    meal_description = st.text_input(
        t("食べたもの"),
        placeholder=t("例: 納豆1パック、ご飯茶碗1杯"),
        key="today_meal_description",
    )
    if st.button(t("AIで栄養を推定"), key="today_meal_estimate_button"):
        if not meal_description.strip():
            st.warning(t("食べたものを入力してください。"))
        else:
            with st.spinner(t("栄養を推定しています...")):
                try:
                    estimated = meal_service.estimate_nutrition(meal_description)
                except AIProviderError as e:
                    st.error(t("栄養推定に失敗しました: {error}", error=e))
                else:
                    st.session_state["today_meal_calories_input"] = estimated.calories
                    st.session_state["today_meal_protein_input"] = estimated.protein_g
                    st.session_state["today_meal_fat_input"] = estimated.fat_g
                    st.session_state["today_meal_carb_input"] = estimated.carbohydrate_g
                    st.success(
                        t(
                            "推定結果を下記フォームに反映しました。"
                            "必要に応じて修正してから記録してください。"
                        )
                    )
                    st.rerun()

    with st.form("today_meal_form"):
        meal_date = st.date_input(t("日付"), value=journal_date, key="today_meal_date")
        meal_time = st.time_input(t("時刻"), value=datetime.now().time(), key="today_meal_time")
        meal_type = st.selectbox(
            t("食事区分"),
            options=list(MealType),
            format_func=lambda m: m.value,
            key="today_meal_type_input",
        )
        calories = st.number_input(
            t("カロリー(kcal)"), min_value=0.0, step=10.0, key="today_meal_calories_input"
        )
        protein_g = st.number_input(
            t("タンパク質(g)"), min_value=0.0, step=1.0, key="today_meal_protein_input"
        )
        fat_g = st.number_input(t("脂質(g)"), min_value=0.0, step=1.0, key="today_meal_fat_input")
        carbohydrate_g = st.number_input(
            t("炭水化物(g)"), min_value=0.0, step=1.0, key="today_meal_carb_input"
        )
        memo = st.text_input(t("メモ(任意)"), key="today_meal_memo")
        submitted_meal = st.form_submit_button(t("食事記録を保存する"), type="primary")

    if submitted_meal:
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
        meal_service.record_meal_log(meal_log)
        for key in (
            "today_meal_description",
            "today_meal_type_input",
            "today_meal_calories_input",
            "today_meal_protein_input",
            "today_meal_fat_input",
            "today_meal_carb_input",
            "today_meal_memo",
        ):
            st.session_state.pop(key, None)
        st.success(t("食事記録を保存しました。"))
        st.rerun()

    if meal_logs_today:
        meal_table_event = st.dataframe(
            pd.DataFrame(
                {
                    t("日時"): [format_datetime_jst(m.consumed_at) for m in meal_logs_today],
                    t("区分"): [m.meal_type.value for m in meal_logs_today],
                    "kcal": [m.calories for m in meal_logs_today],
                    "P(g)": [m.protein_g for m in meal_logs_today],
                    "F(g)": [m.fat_g for m in meal_logs_today],
                    "C(g)": [m.carbohydrate_g for m in meal_logs_today],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="today_meal_table",
        )
        meal_selected_rows = meal_table_event.selection.rows
        selected_meal = meal_logs_today[meal_selected_rows[0]] if meal_selected_rows else None
        if (
            st.button(
                t("編集する"), key="today_meal_edit_open_button", disabled=selected_meal is None
            )
            and selected_meal is not None
        ):
            _meal_edit_dialog(selected_meal)

with task_log_tab:
    plan_task_ids = {item.task_id for item in plan_items}
    count_tasks = [
        ct
        for ct in all_tasks
        if ct.task_id in plan_task_ids and ct.log_type == TaskLogType.COUNT_AND_DURATION
    ]
    if not count_tasks:
        st.caption(t("Pで「数量・時間を記録する」タスクを選ぶと、ここに実績入力欄が表示されます。"))
    task_log_by_task_id = {log.task_id: log for log in task_logs_today}
    duration_choices: list[int | None] = [None, *DURATION_OPTIONS]
    for task in count_tasks:
        existing_log = task_log_by_task_id.get(task.task_id)
        st.markdown(f"**{task.title}**")
        col1, col2, col3 = st.columns(3)
        quantity = col1.number_input(
            t("数量") + (f"({task.unit})" if task.unit else ""),
            min_value=0.0,
            step=1.0,
            value=float(existing_log.quantity) if existing_log and existing_log.quantity else 0.0,
            key=f"today_tasklog_qty_{task.task_id}_{date_suffix}",
        )
        default_duration = (
            nearest_duration_option(existing_log.duration_minutes) if existing_log else None
        )
        duration = col2.selectbox(
            t("時間"),
            options=duration_choices,
            index=duration_choices.index(default_duration)
            if default_duration in duration_choices
            else 0,
            format_func=lambda v: t("未記録") if v is None else format_duration_option(v),
            key=f"today_tasklog_dur_{task.task_id}_{date_suffix}",
        )
        memo = col3.text_input(
            t("メモ(任意)"),
            value=(existing_log.memo or "") if existing_log else "",
            key=f"today_tasklog_memo_{task.task_id}_{date_suffix}",
        )
        if st.button(t("保存"), key=f"today_tasklog_save_{task.task_id}_{date_suffix}"):
            daily_journal_service.save_task_log(
                DailyTaskLog(
                    daily_task_log_id=(existing_log.daily_task_log_id if existing_log else uuid4()),
                    user_id=user_id,
                    journal_date=journal_date,
                    task_id=task.task_id,
                    quantity=quantity or None,
                    duration_minutes=duration,
                    memo=memo or None,
                )
            )
            st.success(t("保存しました。"))
            st.rerun()
        st.divider()

    st.markdown(f"**{t('学習ログ(自由記述: 試験勉強・PF開発・調べ物・キャリア戦略)')}**")
    _render_learning_new_record_section(all_learning_logs, journal_date)

    if not learning_logs_today:
        st.info(t("まだ記録がありません。"))
    else:
        learning_table_event = st.dataframe(
            pd.DataFrame(
                {
                    t("日時"): [format_datetime_jst(log.started_at) for log in learning_logs_today],
                    t("カテゴリ"): [
                        _LEARNING_CATEGORY_LABELS[log.category] for log in learning_logs_today
                    ],
                    t("場所"): [
                        _LEARNING_LOCATION_LABELS[log.location] for log in learning_logs_today
                    ],
                    t("内容"): [
                        log.content or (", ".join(log.keywords) or "-")
                        for log in learning_logs_today
                    ],
                    t("時間(分)"): [
                        log.duration_minutes if log.duration_minutes is not None else "-"
                        for log in learning_logs_today
                    ],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="today_learning_table",
        )
        learning_selected_rows = learning_table_event.selection.rows
        selected_learning = (
            learning_logs_today[learning_selected_rows[0]] if learning_selected_rows else None
        )
        if (
            st.button(
                t("編集する"),
                key="today_learning_edit_open_button",
                disabled=selected_learning is None,
            )
            and selected_learning is not None
        ):
            _learning_edit_dialog(selected_learning)


with workout_tab:
    _render_workout_new_record_section(all_workout_logs, journal_date)

    if workout_logs_today:
        workout_table_event = st.dataframe(
            pd.DataFrame(
                {
                    t("日時"): [format_datetime_jst(w.performed_at) for w in workout_logs_today],
                    t("種目数"): [len(w.exercises) for w in workout_logs_today],
                    t("種目"): [
                        " / ".join(format_exercise_line(e) for e in w.exercises)
                        for w in workout_logs_today
                    ],
                }
            ),
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="today_workout_table",
        )
        workout_selected_rows = workout_table_event.selection.rows
        selected_workout = (
            workout_logs_today[workout_selected_rows[0]] if workout_selected_rows else None
        )
        if (
            st.button(
                t("編集する"),
                key="today_workout_edit_open_button",
                disabled=selected_workout is None,
            )
            and selected_workout is not None
        ):
            _workout_edit_dialog(selected_workout)

with household_tab:
    household_draft = daily_journal_service.get_or_create_draft(user_id, journal_date)
    shopping_memo_key = f"today_shopping_memo_{date_suffix}"

    # 買い物メモ(st.text_area)へのsession_state書き込みは、そのウィジェットが
    # 一度でも生成された後は許可されない(StreamlitAPIException)。そのため
    # レシピからの材料追加(session_stateへの書き込みを伴う)は、必ず
    # text_areaより前に配置する。
    recipe_history = sorted(
        recipe_service.list_recipe_history(user_id), key=lambda r: r.created_at, reverse=True
    )
    if recipe_history:
        selected_recipe = st.selectbox(
            t("📋 レシピから材料を追加"),
            options=recipe_history,
            format_func=lambda r: r.title,
            key=f"today_shopping_recipe_select_{date_suffix}",
        )
        if st.button(t("材料をメモに追加"), key=f"today_shopping_recipe_add_{date_suffix}"):
            recipe_ingredients = recipe_service.get_recipe_ingredients(selected_recipe.recipe_id)
            ingredient_names_map = recipe_service.get_ingredient_names(recipe_ingredients)
            ingredient_names = [
                ingredient_names_map[ri.ingredient_id]
                for ri in recipe_ingredients
                if ri.ingredient_id in ingredient_names_map
            ]
            current_memo = st.session_state.get(
                shopping_memo_key, household_draft.shopping_memo or ""
            )
            st.session_state[shopping_memo_key] = append_recipe_ingredients(
                current_memo, selected_recipe, ingredient_names
            )
            st.rerun()
    else:
        st.caption(t("まだ生成されたレシピがありません(「レシピ」ページで生成できます)。"))

    shopping_memo = st.text_area(
        t("買い物メモ"),
        value=household_draft.shopping_memo or "",
        key=shopping_memo_key,
    )

    food_expense_yen = st.number_input(
        t("食費合計(円)"),
        min_value=0,
        step=100,
        value=household_draft.food_expense_yen or 0,
        key=f"today_food_expense_{date_suffix}",
    )
    if st.button(t("家計を保存する"), type="primary", key=f"today_household_save_{date_suffix}"):
        latest = daily_journal_service.get_or_create_draft(user_id, journal_date)
        daily_journal_service.save_journal(
            replace(
                latest,
                shopping_memo=shopping_memo or None,
                food_expense_yen=int(food_expense_yen) or None,
            )
        )
        st.success(t("保存しました。"))
        st.rerun()

st.divider()

# ------------------------------------------------------------
# ▼ C: 振り返り
# ------------------------------------------------------------
with st.expander(t("▼ C: 振り返り"), expanded=True):
    c_draft = daily_journal_service.get_or_create_draft(user_id, journal_date)
    reflection_memo = st.text_area(
        t("振り返り"), value=c_draft.reflection_memo or "", key=f"today_reflection_{date_suffix}"
    )
    if st.button(t("Cを保存する"), type="primary", key=f"today_c_save_{date_suffix}"):
        latest = daily_journal_service.get_or_create_draft(user_id, journal_date)
        daily_journal_service.save_journal(replace(latest, reflection_memo=reflection_memo or None))
        st.success(t("保存しました。"))
        st.rerun()

# ------------------------------------------------------------
# ▼ A: 明日変えること
# ------------------------------------------------------------
with st.expander(t("▼ A: 明日変えること"), expanded=True):
    a_draft = daily_journal_service.get_or_create_draft(user_id, journal_date)
    improvement_point = st.text_input(
        t("改善すること(1つ)"),
        value=a_draft.improvement_point or "",
        key=f"today_improvement_{date_suffix}",
    )
    cooking_shopping_note = st.text_area(
        t("料理・買い物メモ"),
        value=a_draft.cooking_shopping_note or "",
        key=f"today_cooking_note_{date_suffix}",
    )
    study_prep_note = st.text_area(
        t("学習準備メモ"),
        value=a_draft.study_prep_note or "",
        key=f"today_study_prep_{date_suffix}",
    )
    if st.button(t("Aを保存する"), type="primary", key=f"today_a_save_{date_suffix}"):
        latest = daily_journal_service.get_or_create_draft(user_id, journal_date)
        daily_journal_service.save_journal(
            replace(
                latest,
                improvement_point=improvement_point or None,
                cooking_shopping_note=cooking_shopping_note or None,
                study_prep_note=study_prep_note or None,
            )
        )
        st.success(t("保存しました。"))
        st.rerun()
