"""長期目標管理画面(app/pages/goals.py)で使う、Streamlit非依存の
純粋関数・ラベル定義。

daily-journal-design.md 3.2節のカテゴリ・4章の進捗表示に対応する。
"""

from __future__ import annotations

from health_intelligence.domain.enums import GoalCategory, GoalStatus, TaskLogType
from health_intelligence.services.goal_service import TaskProgress

GOAL_CATEGORY_LABELS: dict[GoalCategory, str] = {
    GoalCategory.STUDY: "学習",
    GoalCategory.PF_DEV: "PF開発",
    GoalCategory.WORK: "仕事",
    GoalCategory.DIET: "食事方針",
    GoalCategory.EXERCISE: "運動目標",
    GoalCategory.SLEEP: "睡眠目標",
    GoalCategory.CAREER: "キャリア・プロダクト戦略",
    GoalCategory.LIFE: "その他生活全般",
}

GOAL_STATUS_LABELS: dict[GoalStatus, str] = {
    GoalStatus.IN_PROGRESS: "進行中",
    GoalStatus.ACHIEVED: "達成",
    GoalStatus.SUSPENDED: "中断",
}

TASK_LOG_TYPE_LABELS: dict[TaskLogType, str] = {
    TaskLogType.COUNT_AND_DURATION: "数量・時間を記録する",
    TaskLogType.PLAN_ONLY: "選ぶだけ(実績は既存タブに記録)",
}

DURATION_OPTIONS: list[int] = [15, 30, 45, 60, 90, 120]
"""15分刻みドロップダウンの選択肢(分)。120は「120分以上」を表す。"""


def format_duration_option(minutes: int) -> str:
    if minutes >= DURATION_OPTIONS[-1]:
        return f"{minutes}分以上"
    return f"{minutes}分"


def format_task_progress(progress: TaskProgress) -> str:
    """TaskProgressを「累計450問・累計12時間30分」のような表示文字列へ整形する。

    quantity/durationのどちらも記録が無い(0)場合は「まだ記録がありません」を返す。
    """
    parts: list[str] = []
    if progress.total_quantity:
        unit = progress.task.unit or ""
        quantity = progress.total_quantity
        quantity_text = str(int(quantity)) if quantity == int(quantity) else str(quantity)
        parts.append(f"累計{quantity_text}{unit}")
    if progress.total_duration_minutes:
        hours, minutes = divmod(progress.total_duration_minutes, 60)
        if hours and minutes:
            parts.append(f"累計{hours}時間{minutes}分")
        elif hours:
            parts.append(f"累計{hours}時間")
        else:
            parts.append(f"累計{minutes}分")
    return "・".join(parts) if parts else "まだ記録がありません"
