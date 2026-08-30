"""dashboard_charts.pyの純粋関数のテスト。"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.dashboard_charts import (  # noqa: E402
    group_average_by_date,
    group_sum_by_date,
    last_n_days,
)


@dataclass
class _Item:
    day: date
    value: float | None


def test_last_n_days_returns_ascending_range_including_reference() -> None:
    result = last_n_days(date(2026, 8, 30), 7)

    assert result == [
        date(2026, 8, 24),
        date(2026, 8, 25),
        date(2026, 8, 26),
        date(2026, 8, 27),
        date(2026, 8, 28),
        date(2026, 8, 29),
        date(2026, 8, 30),
    ]


def test_group_sum_by_date_sums_matching_dates_and_ignores_others() -> None:
    dates = last_n_days(date(2026, 8, 30), 3)
    items = [
        _Item(date(2026, 8, 29), 10),
        _Item(date(2026, 8, 29), 5),
        _Item(date(2026, 8, 30), 3),
        _Item(date(2026, 8, 1), 999),  # 範囲外なので無視される
    ]

    result = group_sum_by_date(items, lambda i: i.day, lambda i: i.value, dates)

    assert result == [0.0, 15.0, 3.0]


def test_group_sum_by_date_returns_zero_for_empty_days() -> None:
    dates = last_n_days(date(2026, 8, 30), 3)

    result = group_sum_by_date([], lambda i: i.day, lambda i: i.value, dates)

    assert result == [0.0, 0.0, 0.0]


def test_group_average_by_date_averages_and_skips_none_values() -> None:
    dates = last_n_days(date(2026, 8, 30), 2)
    items = [
        _Item(date(2026, 8, 30), 4),
        _Item(date(2026, 8, 30), 2),
        _Item(date(2026, 8, 30), None),
    ]

    result = group_average_by_date(items, lambda i: i.day, lambda i: i.value, dates)

    assert result == [None, 3.0]
