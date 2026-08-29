"""`app/components/learning_form`のテスト。

app/はsrc/health_intelligenceとは別のトップレベルディレクトリのため、
importできるようsys.pathへ明示的に追加する(test_workout_form.pyと
同じパターン)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

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


def test_split_slash_list_strips_and_drops_empty() -> None:
    assert split_slash_list("Python / SQL /  ") == ["Python", "SQL"]
    assert split_slash_list("") == []


def test_join_slash_list_is_inverse_of_split() -> None:
    items = ["Python", "SQL"]
    assert split_slash_list(join_slash_list(items)) == items


def test_split_comma_list_strips_and_drops_empty() -> None:
    assert split_comma_list("Chapter3, Chapter5,  ") == ["Chapter3", "Chapter5"]
    assert split_comma_list("") == []


def test_join_comma_list_is_inverse_of_split() -> None:
    items = ["Chapter3", "Chapter5"]
    assert split_comma_list(join_comma_list(items)) == items


def test_split_lines_list_strips_and_drops_empty_lines() -> None:
    text = "・案A: 新規事業\n\n  ・案B: 既存強化  \n"
    assert split_lines_list(text) == ["・案A: 新規事業", "・案B: 既存強化"]
    assert split_lines_list("") == []


def test_join_lines_list_is_inverse_of_split() -> None:
    items = ["・案A", "・案B"]
    assert split_lines_list(join_lines_list(items)) == items


def test_combine_duration_minutes_combines_hours_and_minutes() -> None:
    assert combine_duration_minutes(1, 30) == 90
    assert combine_duration_minutes(1.5, 0) == 90
    assert combine_duration_minutes(0, 45) == 45


def test_combine_duration_minutes_returns_none_when_total_is_zero() -> None:
    assert combine_duration_minutes(None, None) is None
    assert combine_duration_minutes(0, 0) is None
    assert combine_duration_minutes(None, 0) is None


def test_split_duration_minutes_is_inverse_of_combine() -> None:
    assert split_duration_minutes(90) == (1, 30)
    assert split_duration_minutes(45) == (0, 45)


def test_split_duration_minutes_handles_none() -> None:
    assert split_duration_minutes(None) == (0, 0)
