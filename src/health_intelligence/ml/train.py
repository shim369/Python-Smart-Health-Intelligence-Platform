"""LightGBMによる学習・推論。

このモジュールのみが`lightgbm`ライブラリに依存する。評価ロジック
(ml/evaluation.py)自体はこのモジュールに依存しない設計にしている
(`TrainPredictFn`として注入されるだけなので、LightGBM以外のモデルに
差し替えることも容易)。
"""

from __future__ import annotations

import lightgbm as lgb


def train_and_predict(
    x_train: list[list[float]],
    y_train: list[float],
    x_predict: list[list[float]],
) -> list[float]:
    """LightGBMで学習し、`x_predict`に対する予測値を返す。

    `ml.evaluation.TrainPredictFn`のシグネチャを満たす。ハイパー
    パラメータは初期値であり、実データでの評価結果を見ながら
    Phase 8以降でチューニングする想定。
    """
    model = lgb.LGBMRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=4,
        random_state=42,
        verbosity=-1,
    )
    model.fit(x_train, y_train)
    return list(model.predict(x_predict))
