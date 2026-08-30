"""ダッシュボードの週間グラフ用、Streamlit非依存の集計関数。

各グラフは「過去7日間、日付ごとの合計/平均」という同じ形の集計を
繰り返し使うため、`group_sum_by_date`/`group_average_by_date`という
2つの汎用関数に集約する。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date, timedelta


def last_n_days(reference: date, n: int) -> list[date]:
    """`reference`を含む直近n日間を、古い→新しい順で返す。"""
    return [reference - timedelta(days=offset) for offset in range(n - 1, -1, -1)]


def group_sum_by_date[T](
    items: Iterable[T],
    date_of: Callable[[T], date],
    value_of: Callable[[T], float],
    dates: list[date],
) -> list[float]:
    """`items`を`date_of`で日付ごとにグルーピングし、`value_of`の合計を
    `dates`の並び順で返す。`dates`に含まれない日付のitemは無視する。
    """
    totals = dict.fromkeys(dates, 0.0)
    for item in items:
        d = date_of(item)
        if d in totals:
            totals[d] += value_of(item)
    return [totals[d] for d in dates]


def group_average_by_date[T](
    items: Iterable[T],
    date_of: Callable[[T], date],
    value_of: Callable[[T], float | None],
    dates: list[date],
) -> list[float | None]:
    """`group_sum_by_date`の平均版。値がNoneのitemは分母に含めない。
    その日の集計対象が1件もない場合はNoneを返す(0と区別するため)。
    """
    sums = dict.fromkeys(dates, 0.0)
    counts = dict.fromkeys(dates, 0)
    for item in items:
        d = date_of(item)
        if d not in sums:
            continue
        v = value_of(item)
        if v is not None:
            sums[d] += v
            counts[d] += 1
    return [sums[d] / counts[d] if counts[d] else None for d in dates]
