"""CSVインポートページ。

過去に手書き(Macのメモ・スプレッドシート等)で記録していたログを、
CSVとして書き出して一括で取り込む。ゼロから記録し直す必要をなくし、
MLパイプラインが要求する最低データ量(60日分、ml/dataset.py参照)へ
早く到達できるようにする。

ログ種別ごとにタブを分け、各タブで
1. テンプレートCSVのダウンロード
2. CSVファイルのアップロード・プレビュー(有効な行/エラー行の確認)
3. 有効な行のみを一括インポート
という流れにする。日付・時刻は日本時間(JST)で記入する
(log_entry.pyの手入力フォームと同じ規則)。
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from auth_guard import require_login  # noqa: E402
from components.csv_import import (  # noqa: E402
    ImportResult,
    parse_health_rows,
    parse_meal_rows,
    parse_sleep_rows,
    parse_weight_rows,
    parse_workout_rows,
)
from components.formatting import format_datetime_jst  # noqa: E402
from services import (  # noqa: E402
    get_health_service,
    get_meal_service,
    get_sleep_service,
    get_weight_service,
    get_workout_service,
)

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title("📥 CSVインポート")
st.caption(
    "スプレッドシートやメモに記録していた過去のログをCSVで書き出して、"
    "このアプリへまとめて取り込めます。各タブのテンプレートに沿って"
    "CSVを準備してください。"
)


def _read_csv_rows(uploaded_file: object) -> list[dict[str, str]]:
    """アップロードされたCSVファイルをdictの行リストへ変換する。"""
    raw_bytes = uploaded_file.getvalue()  # type: ignore[attr-defined]
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [{k: (v or "") for k, v in row.items()} for row in reader]


def _template_bytes(header: list[str], example_row: list[str]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerow(example_row)
    return buf.getvalue().encode("utf-8-sig")


def _render_import_tab(
    *,
    label: str,
    key_prefix: str,
    header: list[str],
    example_row: list[str],
    caption: str,
    parse_fn,
    record_fn,
    preview_columns: dict[str, object],
) -> None:
    """1タブ分のインポートUIを描画する共通処理。

    5種類のログでUIの流れ(テンプレート→アップロード→プレビュー→
    インポート)は共通なため、差分(列定義・パース関数・保存関数・
    プレビュー列)だけをパラメータ化する。
    """
    st.caption(caption)
    st.download_button(
        "テンプレートCSVをダウンロード",
        data=_template_bytes(header, example_row),
        file_name=f"{key_prefix}_template.csv",
        mime="text/csv",
        key=f"{key_prefix}_template_download",
    )

    uploaded = st.file_uploader(
        "CSVファイルを選択", type="csv", key=f"{key_prefix}_uploader"
    )
    if uploaded is None:
        return

    try:
        rows = _read_csv_rows(uploaded)
    except UnicodeDecodeError:
        st.error("文字コードを読み取れませんでした。UTF-8で保存し直してください。")
        return

    if not rows:
        st.warning("データ行がありません。")
        return

    result: ImportResult = parse_fn(rows, user_id=user_id)

    st.write(f"有効な行: {len(result.logs)}件 / エラー: {len(result.errors)}件")

    if result.errors:
        st.dataframe(
            pd.DataFrame(
                {
                    "行番号": [e.row_number for e in result.errors],
                    "エラー内容": [e.message for e in result.errors],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    if result.logs:
        st.dataframe(
            pd.DataFrame(
                {
                    name: [fn(log) for log in result.logs]
                    for name, fn in preview_columns.items()
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        if st.button(
            f"有効な{len(result.logs)}件をインポートする",
            key=f"{key_prefix}_import_button",
        ):
            for log in result.logs:
                record_fn(log)
            st.success(f"{len(result.logs)}件のログをインポートしました。")


(
    meal_tab,
    workout_tab,
    sleep_tab,
    weight_tab,
    health_tab,
) = st.tabs(["食事", "運動", "睡眠", "体重", "体調"])


with meal_tab:
    _render_import_tab(
        label="食事",
        key_prefix="meal",
        header=[
            "date",
            "time",
            "meal_type",
            "calories",
            "protein_g",
            "fat_g",
            "carbohydrate_g",
            "memo",
        ],
        example_row=[
            "2026-06-01",
            "08:00",
            "breakfast",
            "450",
            "20",
            "15",
            "55",
            "納豆ご飯",
        ],
        caption=(
            "meal_typeは breakfast / lunch / dinner / snack のいずれか。"
            "AIによる推定は行わず、CSVの数値をそのまま取り込みます。"
        ),
        parse_fn=parse_meal_rows,
        record_fn=lambda log: get_meal_service().record_meal_log(log),
        preview_columns={
            "日時": lambda m: format_datetime_jst(m.consumed_at),
            "区分": lambda m: m.meal_type.value,
            "kcal": lambda m: m.calories,
        },
    )

with workout_tab:
    _render_import_tab(
        label="運動",
        key_prefix="workout",
        header=[
            "date",
            "time",
            "exercise_name",
            "category",
            "duration_minutes",
            "reps",
            "weight_kg",
        ],
        example_row=["2026-06-01", "19:00", "レッグプレス", "strength", "", "10", "75"],
        caption=(
            "同じdate・timeの行は1回の運動セッションとしてまとめられます。"
            "categoryは cardio(duration_minutesを使用) / strength"
            "(reps・weight_kgを使用)。同じexercise_nameを複数行に分ければ"
            "複数セットとして取り込まれます。"
        ),
        parse_fn=parse_workout_rows,
        record_fn=lambda log: get_workout_service().record_workout_log(log),
        preview_columns={
            "日時": lambda w: format_datetime_jst(w.performed_at),
            "種目数": lambda w: len(w.exercises),
            "種目": lambda w: "、".join(e.exercise_name for e in w.exercises),
        },
    )

with sleep_tab:
    _render_import_tab(
        label="睡眠",
        key_prefix="sleep",
        header=["bedtime_date", "bedtime_time", "wake_date", "wake_time", "quality"],
        example_row=["2026-06-01", "23:30", "2026-06-02", "07:00", "good"],
        caption="qualityは任意。poor / fair / good / excellent のいずれか。",
        parse_fn=parse_sleep_rows,
        record_fn=lambda log: get_sleep_service().record_sleep_log(log),
        preview_columns={
            "就寝": lambda s: format_datetime_jst(s.bedtime),
            "起床": lambda s: format_datetime_jst(s.wake_time),
            "睡眠時間(分)": lambda s: s.duration_minutes,
        },
    )

with weight_tab:
    _render_import_tab(
        label="体重",
        key_prefix="weight",
        header=["date", "time", "weight_kg"],
        example_row=["2026-06-01", "07:00", "65.5"],
        caption="timeは任意(省略時は00:00として記録されます)。",
        parse_fn=parse_weight_rows,
        record_fn=lambda log: get_weight_service().record_weight_log(log),
        preview_columns={
            "日時": lambda w: format_datetime_jst(w.recorded_at),
            "体重(kg)": lambda w: w.weight_kg,
        },
    )

with health_tab:
    _render_import_tab(
        label="体調",
        key_prefix="health",
        header=["date", "time", "condition_score", "symptoms", "memo"],
        example_row=["2026-06-01", "08:00", "3", "頭痛;倦怠感", ""],
        caption=(
            "condition_scoreは任意(1〜5)。symptomsは任意で、"
            "複数ある場合はセミコロン(;)区切りで記入してください。"
        ),
        parse_fn=parse_health_rows,
        record_fn=lambda log: get_health_service().record_health_log(log),
        preview_columns={
            "日時": lambda h: format_datetime_jst(h.recorded_at),
            "スコア": lambda h: h.condition_score,
            "症状": lambda h: "、".join(h.symptoms),
        },
    )
