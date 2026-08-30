"""学習ログページ。

学習・PF開発・調べ物・キャリア戦略設計の記録を入力する。新規記録フォームと、
既存記録を選んで編集・削除できる「過去の記録」セクションを設ける。

食事・運動・睡眠・体重・体調の記録は「今日」ページ(pages/today.py)へ
移設した(daily-journal-design.md参照)。学習ログは新設計のGoal/Task方式
との重複整理が未了のため、当面このページに残す。

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
    frequent_learning_keywords,
    most_recent_learning_log,
)
from services import get_learning_service  # noqa: E402

from health_intelligence.domain.enums import (  # noqa: E402
    LearningCategory,
    LearningLocation,
)
from health_intelligence.domain.models import LearningLog  # noqa: E402

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title("📝 学習ログ")

(learning_tab,) = st.tabs(["学習"])

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
