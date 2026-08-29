"""学習ログ(学習タブ)のカテゴリ依存フィールドを支えるロジック。

「Chapter3, Chapter5」のようなカンマ区切りテキストや「Python / SQL」の
ようなスラッシュ区切りテキストと、Domain Modelの`list[str]`フィールド
(breakdown/keywords)を相互変換する。時間(h)/分の2入力と
`duration_minutes`(分の単一値)の相互変換も同様。

Streamlitに依存しない純粋関数として実装し、単体テストで検証できる
ようにする(workout_form.py / quick_entry.pyと同様のパターン)。
"""

from __future__ import annotations


def split_slash_list(text: str) -> list[str]:
    """ "Python / SQL" のようなスラッシュ区切りテキストをリストへ変換する。"""
    return [item.strip() for item in text.split("/") if item.strip()]


def join_slash_list(items: list[str]) -> str:
    """`split_slash_list`の逆変換。"""
    return " / ".join(items)


def split_comma_list(text: str) -> list[str]:
    """ "Chapter3, Chapter5" のようなカンマ区切りテキストをリストへ変換する。"""
    return [item.strip() for item in text.split(",") if item.strip()]


def join_comma_list(items: list[str]) -> str:
    """`split_comma_list`の逆変換。"""
    return ", ".join(items)


def split_lines_list(text: str) -> list[str]:
    """複数行テキスト(1行1項目)をリストへ変換する。空行は除外する。"""
    return [line.strip() for line in text.splitlines() if line.strip()]


def join_lines_list(items: list[str]) -> str:
    """`split_lines_list`の逆変換。"""
    return "\n".join(items)


def combine_duration_minutes(
    hours: float | int | None, minutes: int | None
) -> int | None:
    """時間(h)・分の2入力を、`duration_minutes`(分の単一値)へ結合する。

    合計が0の場合は未入力とみなしNoneを返す(他ドメインの
    "0 or None"パターンに合わせる。workout_form.py参照)。
    """
    total = round((hours or 0) * 60) + (minutes or 0)
    return total or None


def split_duration_minutes(duration_minutes: int | None) -> tuple[int, int]:
    """`duration_minutes`を時間(h)・分の2値へ分解する(`combine_duration_minutes`の逆)。"""
    if duration_minutes is None:
        return (0, 0)
    return divmod(duration_minutes, 60)
