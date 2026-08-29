"""forward-chaining(時系列考慮)K分割交差検証。

requirements.md 9.3.1: ランダム分割ではなく、未来データがリークしない
よう時系列順を保ったforward-chaining CVを用いる。
"""

from __future__ import annotations


def forward_chaining_splits(n_samples: int, *, n_splits: int = 5) -> list[tuple[range, range]]:
    """`n_samples`件のサンプル(時系列順)をtrain/validationのindex
    範囲のペアに分割する。

    各分割で、trainは常にvalidationより時間的に前のデータのみを含む
    (未来のデータでtrainしないようにするため)。

    例: n_samples=100, n_splits=5 の場合、validation側は概ね等分の
    ブロックに分かれ、train側はそのブロックより前の全データとなる。
    """
    if n_splits < 2:
        raise ValueError("n_splitsは2以上である必要があります")
    if n_samples < n_splits + 1:
        raise ValueError("n_samplesがn_splitsに対して少なすぎます")

    fold_size = n_samples // (n_splits + 1)
    splits: list[tuple[range, range]] = []
    for i in range(1, n_splits + 1):
        train_end = fold_size * i
        val_end = min(fold_size * (i + 1), n_samples)
        splits.append((range(0, train_end), range(train_end, val_end)))
    return splits
