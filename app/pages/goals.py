"""長期目標管理画面。

「今日」ページとは別に、腰を据えてGoal(長期目標)/Task(関連タスク)を
整理するための画面(daily-journal-design.md 4章)。Goalの新規作成は
この画面からのみ行う。
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

app_dir = Path(__file__).resolve().parents[1]
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.goal_task_labels import (  # noqa: E402
    GOAL_CATEGORY_LABELS,
    GOAL_STATUS_LABELS,
    TASK_LOG_TYPE_LABELS,
    format_task_progress,
)
from services import get_goal_service, get_task_service  # noqa: E402

from health_intelligence.domain.enums import GoalCategory, GoalStatus, TaskLogType  # noqa: E402
from health_intelligence.domain.models import Goal, Task  # noqa: E402

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title(":material/track_changes: 長期目標")

goal_service = get_goal_service()
task_service = get_task_service()


@st.dialog("新しい長期目標を追加")
def _goal_create_dialog() -> None:
    title = st.text_input("タイトル", key="goal_create_title")
    category = st.selectbox(
        "カテゴリ",
        options=list(GoalCategory),
        format_func=lambda c: GOAL_CATEGORY_LABELS[c],
        key="goal_create_category",
    )
    has_deadline = st.checkbox("期限を設定する", key="goal_create_has_deadline")
    deadline = st.date_input("期限", key="goal_create_deadline") if has_deadline else None
    if st.button("追加する", type="primary", key="goal_create_submit"):
        if not title.strip():
            st.warning("タイトルを入力してください。")
        else:
            goal_service.create_goal(
                Goal(
                    goal_id=uuid4(),
                    user_id=user_id,
                    title=title.strip(),
                    category=category,
                    deadline=deadline,
                    created_at=datetime.now(UTC),
                )
            )
            st.success("長期目標を追加しました。")
            st.rerun()


@st.dialog("目標を編集")
def _goal_edit_dialog(goal: Goal) -> None:
    title = st.text_input("タイトル", value=goal.title, key=f"goal_edit_title_{goal.goal_id}")
    category = st.selectbox(
        "カテゴリ",
        options=list(GoalCategory),
        index=list(GoalCategory).index(goal.category),
        format_func=lambda c: GOAL_CATEGORY_LABELS[c],
        key=f"goal_edit_category_{goal.goal_id}",
    )
    has_deadline = st.checkbox(
        "期限を設定する",
        value=goal.deadline is not None,
        key=f"goal_edit_has_deadline_{goal.goal_id}",
    )
    deadline = (
        st.date_input("期限", value=goal.deadline, key=f"goal_edit_deadline_{goal.goal_id}")
        if has_deadline
        else None
    )
    if st.button("更新する", type="primary", key=f"goal_edit_submit_{goal.goal_id}"):
        if not title.strip():
            st.warning("タイトルを入力してください。")
        else:
            goal_service.update_goal(
                Goal(
                    goal_id=goal.goal_id,
                    user_id=goal.user_id,
                    title=title.strip(),
                    category=category,
                    deadline=deadline,
                    status=goal.status,
                    created_at=goal.created_at,
                )
            )
            st.success("更新しました。")
            st.rerun()


@st.dialog("タスクを追加")
def _task_create_dialog(goal: Goal) -> None:
    title = st.text_input("タイトル", key=f"task_create_title_{goal.goal_id}")
    log_type = st.selectbox(
        "記録方式",
        options=list(TaskLogType),
        format_func=lambda t: TASK_LOG_TYPE_LABELS[t],
        key=f"task_create_log_type_{goal.goal_id}",
    )
    unit = (
        st.text_input("単位(例: 問)", key=f"task_create_unit_{goal.goal_id}")
        if log_type == TaskLogType.COUNT_AND_DURATION
        else None
    )
    if st.button("追加する", type="primary", key=f"task_create_submit_{goal.goal_id}"):
        if not title.strip():
            st.warning("タイトルを入力してください。")
        else:
            task_service.create_task(
                Task(
                    task_id=uuid4(),
                    user_id=user_id,
                    goal_id=goal.goal_id,
                    category=goal.category,
                    title=title.strip(),
                    log_type=log_type,
                    unit=(unit.strip() or None) if unit else None,
                    created_at=datetime.now(UTC),
                )
            )
            st.success("タスクを追加しました。")
            st.rerun()


@st.dialog("タスクを編集")
def _task_edit_dialog(task: Task, goals: list[Goal]) -> None:
    title = st.text_input("タイトル", value=task.title, key=f"task_edit_title_{task.task_id}")
    category = st.selectbox(
        "カテゴリ",
        options=list(GoalCategory),
        index=list(GoalCategory).index(task.category),
        format_func=lambda c: GOAL_CATEGORY_LABELS[c],
        key=f"task_edit_category_{task.task_id}",
    )
    log_type = st.selectbox(
        "記録方式",
        options=list(TaskLogType),
        index=list(TaskLogType).index(task.log_type),
        format_func=lambda t: TASK_LOG_TYPE_LABELS[t],
        key=f"task_edit_log_type_{task.task_id}",
    )
    unit = (
        st.text_input("単位(例: 問)", value=task.unit or "", key=f"task_edit_unit_{task.task_id}")
        if log_type == TaskLogType.COUNT_AND_DURATION
        else None
    )
    goal_options: list[Goal | None] = [None, *goals]
    selected_goal = st.selectbox(
        "長期目標(未分類のまま残す場合は「未分類」)",
        options=goal_options,
        index=(
            0
            if task.goal_id is None
            else next(
                (
                    i
                    for i, g in enumerate(goal_options)
                    if g is not None and g.goal_id == task.goal_id
                ),
                0,
            )
        ),
        format_func=lambda g: "未分類" if g is None else g.title,
        key=f"task_edit_goal_{task.task_id}",
    )
    col1, col2 = st.columns(2)
    if col1.button(
        "更新する", type="primary", key=f"task_edit_submit_{task.task_id}", width="stretch"
    ):
        if not title.strip():
            st.warning("タイトルを入力してください。")
        else:
            task_service.update_task(
                Task(
                    task_id=task.task_id,
                    user_id=task.user_id,
                    goal_id=selected_goal.goal_id if selected_goal is not None else None,
                    category=category,
                    title=title.strip(),
                    log_type=log_type,
                    unit=(unit.strip() or None) if unit else None,
                    is_archived=task.is_archived,
                    created_at=task.created_at,
                )
            )
            st.success("更新しました。")
            st.rerun()
    archive_label = "アーカイブ解除" if task.is_archived else "アーカイブする"
    if col2.button(archive_label, key=f"task_edit_archive_{task.task_id}", width="stretch"):
        if task.is_archived:
            task_service.unarchive_task(user_id, task.task_id)
        else:
            task_service.archive_task(user_id, task.task_id)
        st.success("更新しました。")
        st.rerun()


def _render_task_row(task: Task, *, goal: Goal | None) -> None:
    progress_text = ""
    if task.log_type == TaskLogType.COUNT_AND_DURATION and goal is not None:
        progresses = goal_service.compute_task_progress(user_id, goal.goal_id)
        matched = next((p for p in progresses if p.task.task_id == task.task_id), None)
        if matched is not None:
            progress_text = f" — {format_task_progress(matched)}"
    col1, col2 = st.columns([4, 1])
    col1.write(f"・{task.title}{progress_text}")
    if col2.button("編集", key=f"task_row_edit_{task.task_id}", width="stretch"):
        _task_edit_dialog(task, goals_all)


all_tasks = task_service.list_tasks(user_id)
goals_all = sorted(
    goal_service.list_goals(user_id),
    key=lambda g: (
        g.status != GoalStatus.IN_PROGRESS,
        g.deadline is None,
        g.deadline or datetime.max.date(),
    ),
)

if st.button("+ 新しい長期目標を追加", type="primary"):
    _goal_create_dialog()

st.divider()

if not goals_all:
    st.info("まだ長期目標がありません。")

for goal in goals_all:
    deadline_text = f"期限: {goal.deadline.isoformat()}" if goal.deadline else "期限: なし"
    header = (
        f"{goal.title} [{GOAL_CATEGORY_LABELS[goal.category]}] "
        f"{deadline_text}  {GOAL_STATUS_LABELS[goal.status]}"
    )
    with st.expander(header, expanded=goal.status == GoalStatus.IN_PROGRESS):
        goal_tasks = [t for t in all_tasks if t.goal_id == goal.goal_id and not t.is_archived]
        st.write("**タスク一覧**")
        if not goal_tasks:
            st.caption("まだタスクがありません。")
        for task in goal_tasks:
            _render_task_row(task, goal=goal)

        if st.button("+ タスクを追加", key=f"goal_add_task_button_{goal.goal_id}"):
            _task_create_dialog(goal)

        st.divider()
        button_col1, button_col2, button_col3, button_col4 = st.columns(4)
        if button_col1.button(
            "目標を編集", key=f"goal_edit_button_{goal.goal_id}", width="stretch"
        ):
            _goal_edit_dialog(goal)
        if goal.status != GoalStatus.IN_PROGRESS and button_col2.button(
            "進行中にする", key=f"goal_status_in_progress_{goal.goal_id}", width="stretch"
        ):
            goal_service.change_status(user_id, goal.goal_id, GoalStatus.IN_PROGRESS)
            st.rerun()
        if goal.status != GoalStatus.ACHIEVED and button_col3.button(
            "達成にする", key=f"goal_status_achieved_{goal.goal_id}", width="stretch"
        ):
            goal_service.change_status(user_id, goal.goal_id, GoalStatus.ACHIEVED)
            st.rerun()
        if goal.status != GoalStatus.SUSPENDED and button_col4.button(
            "中断する", key=f"goal_status_suspended_{goal.goal_id}", width="stretch"
        ):
            goal_service.change_status(user_id, goal.goal_id, GoalStatus.SUSPENDED)
            st.rerun()

st.divider()
st.subheader("未分類タスク")
st.caption(
    "「今日」ページでその場限りに追加したタスクが表示されます。編集から長期目標に紐付け直せます。"
)
unclassified_tasks = [t for t in all_tasks if t.goal_id is None and not t.is_archived]
if not unclassified_tasks:
    st.caption("未分類のタスクはありません。")
for task in unclassified_tasks:
    _render_task_row(task, goal=None)
