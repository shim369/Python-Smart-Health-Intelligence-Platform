"""長期目標管理画面(app/pages/goals.py)で使う、Streamlit非依存の
純粋関数・ラベル定義。

requirements.md 4.4節のカテゴリ・進捗表示に対応する。
"""

from __future__ import annotations

from i18n import t

from health_intelligence.domain.enums import GoalCategory, GoalStatus, TaskLogType
from health_intelligence.services.goal_service import TaskProgress


def goal_category_labels() -> dict[GoalCategory, str]:
    """呼び出し時点の言語設定でラベル辞書を組み立てる。

    モジュール読み込み時に1度だけ評価される定数辞書にすると、
    `components/`配下はStreamlitのプロセス内でimportキャッシュされる
    (ページ本体と異なり、rerunのたびには再実行されない)ため、
    最初にimportされた時点の言語に翻訳が固定されてしまう。それを
    避けるため、呼び出しごとに`t()`で組み立て直す関数にしている。
    """
    return {
        GoalCategory.STUDY: t("学習"),
        GoalCategory.PF_DEV: t("PF開発"),
        GoalCategory.WORK: t("仕事"),
        GoalCategory.DIET: t("食事方針"),
        GoalCategory.EXERCISE: t("運動目標"),
        GoalCategory.SLEEP: t("睡眠目標"),
        GoalCategory.CAREER: t("キャリア・プロダクト戦略"),
        GoalCategory.LIFE: t("その他生活全般"),
    }


def goal_status_labels() -> dict[GoalStatus, str]:
    """`goal_category_labels()`と同じ理由で、呼び出しごとに組み立てる。"""
    return {
        GoalStatus.IN_PROGRESS: t("進行中"),
        GoalStatus.ACHIEVED: t("達成"),
        GoalStatus.SUSPENDED: t("中断"),
    }


def task_log_type_labels() -> dict[TaskLogType, str]:
    """`goal_category_labels()`と同じ理由で、呼び出しごとに組み立てる。"""
    return {
        TaskLogType.COUNT_AND_DURATION: t("数量・時間を記録する"),
        TaskLogType.PLAN_ONLY: t("選ぶだけ(実績は既存タブに記録)"),
    }


DURATION_OPTIONS: list[int] = [15, 30, 45, 60, 90, 120]
"""15分刻みドロップダウンの選択肢(分)。120は「120分以上」を表す。"""


def format_duration_option(minutes: int) -> str:
    if minutes >= DURATION_OPTIONS[-1]:
        return t("{minutes}分以上", minutes=minutes)
    return t("{minutes}分", minutes=minutes)


def format_task_progress(progress: TaskProgress) -> str:
    """TaskProgressを「累計450問・累計12時間30分」のような表示文字列へ整形する。

    quantity/durationのどちらも記録が無い(0)場合は「まだ記録がありません」を返す。
    """
    parts: list[str] = []
    if progress.total_quantity:
        unit = progress.task.unit or ""
        quantity = progress.total_quantity
        quantity_text = str(int(quantity)) if quantity == int(quantity) else str(quantity)
        parts.append(t("累計{quantity}{unit}", quantity=quantity_text, unit=unit))
    if progress.total_duration_minutes:
        hours, minutes = divmod(progress.total_duration_minutes, 60)
        if hours and minutes:
            parts.append(t("累計{hours}時間{minutes}分", hours=hours, minutes=minutes))
        elif hours:
            parts.append(t("累計{hours}時間", hours=hours))
        else:
            parts.append(t("累計{minutes}分", minutes=minutes))
    return "・".join(parts) if parts else t("まだ記録がありません")
