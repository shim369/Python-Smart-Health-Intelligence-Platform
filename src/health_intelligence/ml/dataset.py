"""ML Dataset生成とデータ品質チェック。

requirements.md 9.3.1で定めた「対象領域につき60日分以上のログ、
欠損率30%未満」という基準を機械的にチェックする。
"""

from __future__ import annotations

from dataclasses import dataclass

from health_intelligence.features.daily_features import DailyFeatures

MIN_DAYS = 60
"""requirements.md 9.3.1: 学習・評価に進むための最低データ量(日数)。"""
MAX_MISSING_RATE = 0.30
"""requirements.md 9.3.1: 許容する最大欠損率。"""

_REQUIRED_FIELDS = (
    "calories",
    "protein_g",
    "fat_g",
    "carbohydrate_g",
    "sleep_duration_minutes",
    "weight_kg",
)
"""欠損チェック対象のフィールド。`workout_duration_minutes`は含めない
(Noneは「その日は運動していない」ことを意味し、データ欠損ではない
ため。daily_features.py参照)。"""


@dataclass(frozen=True, kw_only=True, slots=True)
class DataQualityReport:
    """ML学習に進んでよいかどうかの判定結果。"""

    total_days: int
    missing_rate: float
    """説明変数のいずれかが欠損している日の割合。"""
    is_sufficient: bool
    """MIN_DAYS以上 かつ MAX_MISSING_RATE未満を満たすか。"""
    reason: str


def check_data_quality(daily_features: list[DailyFeatures]) -> DataQualityReport:
    """データ量・欠損率がML学習に進める基準を満たすか判定する。"""
    total_days = len(daily_features)

    if total_days == 0:
        return DataQualityReport(
            total_days=0,
            missing_rate=1.0,
            is_sufficient=False,
            reason="データが0件です",
        )

    missing_count = sum(
        1 for d in daily_features if any(getattr(d, field) is None for field in _REQUIRED_FIELDS)
    )
    missing_rate = missing_count / total_days

    if total_days < MIN_DAYS:
        return DataQualityReport(
            total_days=total_days,
            missing_rate=missing_rate,
            is_sufficient=False,
            reason=f"データ量が不足しています({total_days}日 < 最低{MIN_DAYS}日)",
        )

    if missing_rate >= MAX_MISSING_RATE:
        return DataQualityReport(
            total_days=total_days,
            missing_rate=missing_rate,
            is_sufficient=False,
            reason=f"欠損率が高すぎます({missing_rate:.0%} >= {MAX_MISSING_RATE:.0%})",
        )

    return DataQualityReport(
        total_days=total_days,
        missing_rate=missing_rate,
        is_sufficient=True,
        reason="データ量・欠損率は基準を満たしています",
    )


@dataclass(frozen=True, kw_only=True, slots=True)
class WeightChangeSample:
    """体重変化予測モデルの1サンプル(説明変数+目的変数)。"""

    calories: float
    protein_g: float
    fat_g: float
    carbohydrate_g: float
    sleep_duration_minutes: float
    workout_duration_minutes: float
    weight_kg: float
    next_day_weight_change_kg: float
    """目的変数: 翌日の体重 - 当日の体重。"""


def build_weight_change_dataset(
    daily_features: list[DailyFeatures],
) -> list[WeightChangeSample]:
    """日次特徴量の時系列からWeight変化予測用のDatasetを組み立てる。

    `daily_features`は日付昇順に並んでいる前提。いずれかの説明変数が
    欠損している日、および最終日(翌日のweightが存在せず目的変数を
    計算できない)はスキップする。
    """
    samples: list[WeightChangeSample] = []

    for today, tomorrow in zip(daily_features, daily_features[1:], strict=False):
        if (
            today.calories is None
            or today.protein_g is None
            or today.fat_g is None
            or today.carbohydrate_g is None
            or today.sleep_duration_minutes is None
            or today.weight_kg is None
            or tomorrow.weight_kg is None
        ):
            continue

        samples.append(
            WeightChangeSample(
                calories=today.calories,
                protein_g=today.protein_g,
                fat_g=today.fat_g,
                carbohydrate_g=today.carbohydrate_g,
                sleep_duration_minutes=float(today.sleep_duration_minutes),
                # workout_duration_minutesがNoneなのは「運動していない日」を
                # 意味し、データ欠損ではないため0として扱う。
                workout_duration_minutes=float(today.workout_duration_minutes or 0),
                weight_kg=today.weight_kg,
                next_day_weight_change_kg=tomorrow.weight_kg - today.weight_kg,
            )
        )

    return samples
