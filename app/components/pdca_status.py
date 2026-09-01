"""「今日」ページのPDCA進捗インジケーター(例: 「P:済 D:一部 C:未 A:未」)を
判定する、Streamlit非依存の純粋関数。requirements.md 4.4節・4.5節。
"""

from __future__ import annotations

from dataclasses import dataclass

from i18n import t

DONE = "済"
PARTIAL = "一部"
NOT_DONE = "未"
"""日本語の原文定数(テスト・内部ロジック用)。実際に表示する値は
`compute_pdca_status`内で`t()`により翻訳してから`PdcaStatus`へ詰める。"""


@dataclass(frozen=True, kw_only=True, slots=True)
class PdcaStatus:
    plan: str
    do: str
    check: str
    act: str


def compute_pdca_status(
    *,
    has_plan: bool,
    do_section_counts: dict[str, int],
    has_reflection: bool,
    has_improvement: bool,
) -> PdcaStatus:
    """呼び出し側が各セクションの有無をbool/件数へ集計した上で渡す。

    `do_section_counts`はD(実績)の各サブセクション(食事・運動・睡眠・
    体調・学習等・家計)ごとの件数。1件以上あるサブセクションの割合で
    「済/一部/未」を判定する。
    """
    plan = DONE if has_plan else NOT_DONE

    filled_sections = sum(1 for count in do_section_counts.values() if count > 0)
    total_sections = len(do_section_counts)
    if total_sections == 0 or filled_sections == 0:
        do = NOT_DONE
    elif filled_sections == total_sections:
        do = DONE
    else:
        do = PARTIAL

    check = DONE if has_reflection else NOT_DONE
    act = DONE if has_improvement else NOT_DONE

    return PdcaStatus(plan=t(plan), do=t(do), check=t(check), act=t(act))
