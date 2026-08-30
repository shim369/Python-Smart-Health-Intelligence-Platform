"""「今日」ページP(計画)関連の、Streamlit非依存の純粋関数。
daily-journal-design.md 5.1節(前日Pの自動コピー・引き継ぎ)。
"""

from __future__ import annotations

from uuid import UUID


def resolve_initial_plan_task_ids(
    today_task_ids: set[UUID], yesterday_task_ids: set[UUID]
) -> tuple[set[UUID], bool]:
    """(初期選択task_id集合, 前日から複製したか) を返す。

    今日のPが既に保存されていればそのまま使い(自由に再編集・再保存可能)、
    無ければ前日のPをそのまま複製して初期表示する。保存ボタンを押すまでは
    DBへ書き込まない(design.md 5.1節: 自動で差し込むことはしない)。
    """
    if today_task_ids:
        return today_task_ids, False
    return yesterday_task_ids, True
