"""ML Pipelineの動作確認用ダミーデータ生成。

requirements.md 9.3.1: 実データが最低データ量(60日分)に満たない
場合は、ダミーデータでPipeline自体の配線を確認する方針とした。
ここではWeight領域(体重変化予測)向けのダミーDailyFeatures列を生成する。

生成されるデータは、カロリー収支と体重変化におおまかな因果関係
(体脂肪1kgあたり約7700kcalという一般的な近似値)を持たせた合成データ
であり、実際のユーザー行動やエネルギー代謝を正確に表すものではない。
あくまでPipelineが「学習可能なシグナルがあるデータ」で正しく動作する
ことを確認するためのものである。
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from health_intelligence.features.daily_features import DailyFeatures

_KCAL_PER_KG = 7700.0


def generate_dummy_daily_features(
    *, num_days: int = 90, seed: int = 42
) -> list[DailyFeatures]:
    """`num_days`日分のダミーDailyFeaturesを日付昇順で生成する。"""
    rng = random.Random(seed)
    start_date = date(2026, 1, 1)
    weight = 70.0
    rows: list[DailyFeatures] = []

    for i in range(num_days):
        target_date = start_date + timedelta(days=i)
        calories = max(0.0, rng.gauss(2000, 300))
        protein_g = max(0.0, rng.gauss(90, 15))
        fat_g = max(0.0, rng.gauss(60, 15))
        carbohydrate_g = max(0.0, rng.gauss(250, 40))
        sleep_duration_minutes = max(0, int(rng.gauss(420, 45)))
        workout_duration_minutes = max(0, int(rng.gauss(20, 20)))

        calorie_balance = calories - 2000 - workout_duration_minutes * 5
        weight += calorie_balance / _KCAL_PER_KG + rng.gauss(0, 0.15)

        rows.append(
            DailyFeatures(
                target_date=target_date,
                calories=calories,
                protein_g=protein_g,
                fat_g=fat_g,
                carbohydrate_g=carbohydrate_g,
                sleep_duration_minutes=sleep_duration_minutes,
                workout_duration_minutes=workout_duration_minutes,
                weight_kg=round(weight, 2),
            )
        )

    return rows
