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
(today.pyの手入力フォームと同じ規則)。
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
    parse_learning_rows,
    parse_meal_rows,
    parse_sleep_rows,
    parse_weight_rows,
    parse_workout_rows,
)
from components.formatting import format_datetime_jst  # noqa: E402
from components.workout_form import format_exercise_line  # noqa: E402
from i18n import t  # noqa: E402
from services import (  # noqa: E402
    get_health_service,
    get_learning_service,
    get_meal_service,
    get_sleep_service,
    get_weight_service,
    get_workout_service,
)

auth_state = require_login()
user_id = auth_state.require_user_id()

st.title(":material/upload_file: " + t("CSVインポート"))
st.caption(
    t(
        "スプレッドシートやメモに記録していた過去のログをCSVで書き出して、"
        "このアプリへまとめて取り込めます。各タブのテンプレートに沿って"
        "CSVを準備してください。"
    )
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
        t("テンプレートCSVをダウンロード"),
        data=_template_bytes(header, example_row),
        file_name=f"{key_prefix}_template.csv",
        mime="text/csv",
        key=f"{key_prefix}_template_download",
    )

    uploader_version_key = f"{key_prefix}_uploader_version"
    uploader_version = st.session_state.get(uploader_version_key, 0)

    uploaded = st.file_uploader(
        t("CSVファイルを選択"), type="csv", key=f"{key_prefix}_uploader_{uploader_version}"
    )
    if uploaded is None:
        return

    try:
        rows = _read_csv_rows(uploaded)
    except UnicodeDecodeError:
        st.error(t("文字コードを読み取れませんでした。UTF-8で保存し直してください。"))
        return

    if not rows:
        st.warning(t("データ行がありません。"))
        return

    result: ImportResult = parse_fn(rows, user_id=user_id)

    st.write(
        t(
            "有効な行: {valid}件 / エラー: {error}件",
            valid=len(result.logs),
            error=len(result.errors),
        )
    )

    if result.errors:
        st.dataframe(
            pd.DataFrame(
                {
                    t("行番号"): [e.row_number for e in result.errors],
                    t("エラー内容"): [e.message for e in result.errors],
                }
            ),
            hide_index=True,
            width="stretch",
        )

    if result.logs:
        st.dataframe(
            pd.DataFrame(
                {name: [fn(log) for log in result.logs] for name, fn in preview_columns.items()}
            ),
            hide_index=True,
            width="stretch",
        )

        if st.button(
            t("有効な{count}件をインポートする", count=len(result.logs)),
            key=f"{key_prefix}_import_button",
            type="primary",
        ):
            for log in result.logs:
                record_fn(log)
            st.session_state[uploader_version_key] = uploader_version + 1
            st.success(t("{count}件のログをインポートしました。", count=len(result.logs)))
            st.rerun()


(
    meal_tab,
    workout_tab,
    sleep_tab,
    weight_tab,
    health_tab,
    learning_tab,
) = st.tabs([t("食事"), t("運動"), t("睡眠"), t("体重"), t("体調"), t("学習")])


with meal_tab:
    _render_import_tab(
        label=t("食事"),
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
            t("納豆ご飯"),
        ],
        caption=t(
            "meal_typeは breakfast / lunch / dinner / snack のいずれか。"
            "AIによる推定は行わず、CSVの数値をそのまま取り込みます。"
        ),
        parse_fn=parse_meal_rows,
        record_fn=lambda log: get_meal_service().record_meal_log(log),
        preview_columns={
            t("日時"): lambda m: format_datetime_jst(m.consumed_at),
            t("区分"): lambda m: m.meal_type.value,
            "kcal": lambda m: m.calories,
        },
    )

with workout_tab:
    _render_import_tab(
        label=t("運動"),
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
        example_row=["2026-06-01", "19:00", t("レッグプレス"), "strength", "", "10", "75"],
        caption=t(
            "同じdate・timeの行は1回の運動セッションとしてまとめられます。"
            "categoryは cardio(duration_minutesを使用) / strength"
            "(reps・weight_kgを使用)。同じexercise_nameを複数行に分ければ"
            "複数セットとして取り込まれます。"
        ),
        parse_fn=parse_workout_rows,
        record_fn=lambda log: get_workout_service().record_workout_log(log),
        preview_columns={
            t("日時"): lambda w: format_datetime_jst(w.performed_at),
            t("種目数"): lambda w: len(w.exercises),
            t("種目"): lambda w: " / ".join(format_exercise_line(e) for e in w.exercises),
        },
    )

with sleep_tab:
    _render_import_tab(
        label=t("睡眠"),
        key_prefix="sleep",
        header=["bedtime_date", "bedtime_time", "wake_date", "wake_time", "quality"],
        example_row=["2026-06-01", "23:30", "2026-06-02", "07:00", "good"],
        caption=t("qualityは任意。poor / fair / good / excellent のいずれか。"),
        parse_fn=parse_sleep_rows,
        record_fn=lambda log: get_sleep_service().record_sleep_log(log),
        preview_columns={
            t("就寝"): lambda s: format_datetime_jst(s.bedtime),
            t("起床"): lambda s: format_datetime_jst(s.wake_time),
            t("睡眠時間(分)"): lambda s: s.duration_minutes,
        },
    )

with weight_tab:
    _render_import_tab(
        label=t("体重"),
        key_prefix="weight",
        header=["date", "time", "weight_kg"],
        example_row=["2026-06-01", "07:00", "65.5"],
        caption=t("timeは任意(省略時は00:00として記録されます)。"),
        parse_fn=parse_weight_rows,
        record_fn=lambda log: get_weight_service().record_weight_log(log),
        preview_columns={
            t("日時"): lambda w: format_datetime_jst(w.recorded_at),
            t("体重(kg)"): lambda w: w.weight_kg,
        },
    )

with health_tab:
    _render_import_tab(
        label=t("体調"),
        key_prefix="health",
        header=["date", "time", "condition_score", "symptoms", "memo"],
        example_row=["2026-06-01", "08:00", "3", t("頭痛;倦怠感"), ""],
        caption=t(
            "condition_scoreは任意(1〜5)。symptomsは任意で、"
            "複数ある場合はセミコロン(;)区切りで記入してください。"
        ),
        parse_fn=parse_health_rows,
        record_fn=lambda log: get_health_service().record_health_log(log),
        preview_columns={
            t("日時"): lambda h: format_datetime_jst(h.recorded_at),
            t("スコア"): lambda h: h.condition_score,
            t("症状"): lambda h: "、".join(h.symptoms),
        },
    )

with learning_tab:
    _render_import_tab(
        label=t("学習"),
        key_prefix="learning",
        header=[
            "date",
            "time",
            "category",
            "location",
            "content",
            "breakdown",
            "duration_minutes",
            "keywords",
            "notes",
        ],
        example_row=[
            "2026-06-01",
            "20:00",
            "exam_study",
            "home",
            t("Chapter1 過去問"),
            "Chapter1;Chapter2",
            "60",
            "Python;SQL",
            "",
        ],
        caption=t(
            "categoryは exam_study(試験勉強) / portfolio_dev(PF開発) / "
            "research(調べ物) / career_strategy(キャリア・プロダクト戦略設計)"
            "のいずれか。locationは任意で home/gym/coworking_space/cafeの"
            "いずれか。breakdown・keywords・notesは任意で、複数ある場合は"
            "セミコロン(;)区切りで記入してください。"
        ),
        parse_fn=parse_learning_rows,
        record_fn=lambda log: get_learning_service().record_learning_log(log),
        preview_columns={
            t("日時"): lambda learning: format_datetime_jst(learning.started_at),
            t("カテゴリ"): lambda learning: learning.category.value,
            t("内容"): lambda learning: learning.content or "、".join(learning.keywords) or "-",
        },
    )
