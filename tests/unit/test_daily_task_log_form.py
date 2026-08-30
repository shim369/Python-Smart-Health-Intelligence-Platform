"""daily_task_log_form.pyの純粋関数のテスト。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.daily_task_log_form import nearest_duration_option  # noqa: E402


def test_nearest_duration_option_rounds_to_closest() -> None:
    assert nearest_duration_option(50) == 45
    assert nearest_duration_option(100) == 90
    assert nearest_duration_option(200) == 120


def test_nearest_duration_option_returns_none_when_none() -> None:
    assert nearest_duration_option(None) is None


def test_nearest_duration_option_matches_exact_value() -> None:
    assert nearest_duration_option(60) == 60
