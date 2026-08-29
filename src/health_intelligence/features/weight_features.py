"""体重特徴量(7日移動平均・変化量・変化率)。"""

from __future__ import annotations

from dataclasses import dataclass

from health_intelligence.domain.models import WeightLog

_MOVING_AVERAGE_WINDOW = 7


@dataclass(frozen=True, kw_only=True, slots=True)
class WeightFeatures:
    moving_average_kg: float | None
    """直近`_MOVING_AVERAGE_WINDOW`件の単純移動平均。"""
    change_kg: float | None
    """期間内で最も古い記録と最新記録の差分。"""
    change_rate: float | None
    """`change_kg`を最も古い記録の値で割った変化率。"""


def compute_weight_features(weight_logs: list[WeightLog]) -> WeightFeatures:
    """WeightFeaturesを計算する。

    引数の並び順は問わない(関数内で`recorded_at`昇順に並べ替える)。
    """
    if not weight_logs:
        return WeightFeatures(moving_average_kg=None, change_kg=None, change_rate=None)

    ordered = sorted(weight_logs, key=lambda w: w.recorded_at)
    recent = ordered[-_MOVING_AVERAGE_WINDOW:]
    moving_average_kg = sum(w.weight_kg for w in recent) / len(recent)

    if len(ordered) < 2:
        return WeightFeatures(moving_average_kg=moving_average_kg, change_kg=None, change_rate=None)

    first_weight = ordered[0].weight_kg
    last_weight = ordered[-1].weight_kg
    change_kg = last_weight - first_weight
    change_rate = change_kg / first_weight if first_weight != 0 else None

    return WeightFeatures(
        moving_average_kg=moving_average_kg,
        change_kg=change_kg,
        change_rate=change_rate,
    )
