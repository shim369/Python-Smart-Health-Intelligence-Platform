"""pdca_status.pyの純粋関数のテスト。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.pdca_status import DONE, NOT_DONE, PARTIAL, compute_pdca_status  # noqa: E402


def test_plan_done_when_has_plan_true() -> None:
    status = compute_pdca_status(
        has_plan=True, do_section_counts={}, has_reflection=False, has_improvement=False
    )
    assert status.plan == DONE


def test_plan_not_done_when_has_plan_false() -> None:
    status = compute_pdca_status(
        has_plan=False, do_section_counts={}, has_reflection=False, has_improvement=False
    )
    assert status.plan == NOT_DONE


def test_do_partial_when_some_sections_filled() -> None:
    status = compute_pdca_status(
        has_plan=True,
        do_section_counts={"meal": 2, "workout": 0, "sleep": 1},
        has_reflection=False,
        has_improvement=False,
    )
    assert status.do == PARTIAL


def test_do_done_when_all_sections_filled() -> None:
    status = compute_pdca_status(
        has_plan=True,
        do_section_counts={"meal": 2, "workout": 1},
        has_reflection=False,
        has_improvement=False,
    )
    assert status.do == DONE


def test_do_not_done_when_no_sections_filled() -> None:
    status = compute_pdca_status(
        has_plan=True,
        do_section_counts={"meal": 0, "workout": 0},
        has_reflection=False,
        has_improvement=False,
    )
    assert status.do == NOT_DONE


def test_check_and_act_reflect_flags() -> None:
    status = compute_pdca_status(
        has_plan=False, do_section_counts={}, has_reflection=True, has_improvement=True
    )
    assert status.check == DONE
    assert status.act == DONE
