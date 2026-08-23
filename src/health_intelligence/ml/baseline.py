"""Rule-based Baseline。

requirements.md 2.3 / 9.1: Rule-basedは初期Recommendation Engineの
ほか、ML評価時のBaselineとしても利用する。ここでは「訓練データの
目的変数の平均値を常に予測する」という平均値Baselineを実装する
(回帰タスクで一般的に使われる素朴なBaseline)。
"""

from __future__ import annotations

from dataclasses import dataclass

from health_intelligence.ml.dataset import WeightChangeSample


@dataclass(frozen=True, slots=True)
class MeanBaseline:
    """訓練データの目的変数の平均値を常に返すBaseline。"""

    mean_value: float

    @classmethod
    def fit(cls, train_samples: list[WeightChangeSample]) -> MeanBaseline:
        values = [s.next_day_weight_change_kg for s in train_samples]
        return cls(mean_value=sum(values) / len(values))

    def predict(self, samples: list[WeightChangeSample]) -> list[float]:
        return [self.mean_value] * len(samples)
