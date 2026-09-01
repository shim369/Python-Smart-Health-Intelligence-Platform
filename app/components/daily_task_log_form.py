"""「今日」ページD(学習・PF開発・仕事の実績)関連の、Streamlit非依存の
純粋関数。requirements.md 4.4節。
"""

from __future__ import annotations

from components.goal_task_labels import DURATION_OPTIONS


def nearest_duration_option(duration_minutes: int | None) -> int | None:
    """DBに保存された実際の分数(任意の整数)を、15分刻みドロップダウンの
    選択肢のうち最も近いものへ丸める(編集時の初期選択値を決めるため)。
    """
    if duration_minutes is None:
        return None
    return min(DURATION_OPTIONS, key=lambda option: abs(option - duration_minutes))
