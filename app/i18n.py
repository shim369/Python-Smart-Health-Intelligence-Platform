"""UIテキストの日英切り替え(i18n)。

翻訳キーには日本語の原文をそのまま使う。既存コードは元々すべて日本語
文字列を直書きしていたため、意味付きキー(例: "goals.title")を新設
するより、原文をキーにする方が導入コストが低く、`t("...")`の呼び出し
箇所を見ればどの文言の翻訳かが一目で分かる利点もある。

`TRANSLATIONS`に無い文字列は日本語のまま返す(フォールバック)。
未翻訳の文字列があってもアプリが壊れないようにするための設計であり、
本来は全て`TRANSLATIONS`に登録されているべき。

言語設定はUser.locale(DB永続化)を、ログイン時にSession Stateへ
コピーして保持する(auth/session_state.py参照)。切り替えUIは
app/auth_guard.pyのサイドバーに置く。
"""

from __future__ import annotations

import streamlit as st

from health_intelligence.auth import AuthSessionState
from health_intelligence.domain.enums import Locale

LOCALE_LABELS: dict[Locale, str] = {
    Locale.JA: "日本語",
    Locale.EN: "English",
}


def current_locale() -> Locale:
    """現在のSession Stateに設定されている表示言語を返す。"""
    return AuthSessionState(st.session_state).locale


def detect_browser_locale() -> Locale:
    """ブラウザのAccept-Language(`st.context.locale`)からLocaleを推定する。

    新規User作成時の初期表示言語を決めるためだけに使う
    (`st.login()`によるOAuthリダイレクト後はSession Stateがリセット
    されるため、ログイン画面での手動切り替えをログイン後まで
    引き継ぐことはできない。代わりにブラウザの言語設定を使う)。
    判定できない場合は日本語を既定値とする。
    """
    browser_locale = st.context.locale
    if browser_locale and browser_locale.lower().startswith("en"):
        return Locale.EN
    return Locale.JA


def t(text: str, **kwargs: object) -> str:
    """`text`(日本語原文)を現在の言語設定に応じて翻訳する。

    `kwargs`を渡した場合、翻訳後の文字列に対して`str.format(**kwargs)`
    を適用する(値を埋め込むメッセージ用。例: `t("{n}件", n=3)`)。
    """
    if current_locale() == Locale.EN:
        result = TRANSLATIONS.get(text, text)
    else:
        result = text
    return result.format(**kwargs) if kwargs else result


TRANSLATIONS: dict[str, str] = {
    # --- streamlit_app.py / auth_guard.py (ナビゲーション・共通) ---
    "ダッシュボード": "Dashboard",
    "今日": "Today",
    "長期目標": "Goals",
    "CSVインポート": "CSV Import",
    "言語": "Language",
    "ログアウト": "Log out",
    "ログインしてください。": "Please log in.",
    # --- pages/login.py ---
    "このアプリは招待制です。": "This app is invite-only.",
    # --- pages/dashboard.py ---
    "表示期間": "Period",
    "直近{days}日間": "Last {days} days",
    "指標": "Metric",
    "睡眠・体調": "Sleep & Condition",
    "睡眠時間(h)": "Sleep duration (h)",
    "体調スコア(1〜5)": "Condition score (1-5)",
    "総合": "Overall",
    "朝": "Morning",
    "夜": "Evening",
    "メンタル": "Mental",
    "疲労": "Fatigue",
    "ストレス": "Stress",
    "スコア": "Score",
    "体重(kg)": "Weight (kg)",
    "直近{days}日間の体重記録がありません。": "No weight records in the past {days} days.",
    "食事": "Meals",
    "カロリー(kcal)": "Calories (kcal)",
    "PFC(g)": "PFC (g)",
    "タンパク質": "Protein",
    "脂質": "Fat",
    "炭水化物": "Carbs",
    "栄養素": "Nutrient",
    "学習": "Study",
    "学習時間(分) — 学習ログ + タスク実績": "Study time (min) — learning log + task records",
    "学習時間(分)": "Study time (min)",
    "PF開発・仕事": "Dev/Work",
    "作業時間(分) — 学習ログ + タスク実績": "Work time (min) — learning log + task records",
    "作業時間(分)": "Work time (min)",
    "運動": "Exercise",
    "有酸素運動時間(分)": "Cardio time (min)",
    "有酸素運動時間(分) — 種目別": "Cardio time (min) — by exercise",
    "種目別の最大重量(kg) — 記録日数の多い上位5種目": (
        "Max weight per exercise (kg) — top 5 most frequent"
    ),
    "直近{days}日間の筋トレ(重量あり)の記録がありません。": (
        "No weighted strength training records in the past {days} days."
    ),
    "総挙上量(kg)": "Total volume (kg)",
    "総挙上量(kg) — 重量×回数の合計、自重種目は除く": (
        "Total volume (kg) — weight × reps, excluding bodyweight exercises"
    ),
    "家計": "Household",
    "食費合計(円)": "Total food expense (JPY)",
    # --- pages/recipe.py ---
    "AIレシピ": "AI Recipes",
    "レシピを生成する": "Generate a recipe",
    "使いたい食材(改行またはカンマ区切り)": "Ingredients to use (one per line or comma-separated)",
    "鶏むね肉\nブロッコリー\n卵": "Chicken breast\nBroccoli\nEgg",
    "レシピを生成": "Generate recipe",
    "食材を1つ以上入力してください。": "Please enter at least one ingredient.",
    "レシピを生成しています(最大1分程度かかる場合があります)...": (
        "Generating recipe (may take up to about a minute)..."
    ),
    "レシピの生成に失敗しました: {error}": "Failed to generate recipe: {error}",
    "レシピを生成しました。": "Recipe generated.",
    "レシピ履歴": "Recipe history",
    "まだ生成されたレシピがありません。": "No recipes have been generated yet.",
    # --- components/recipe_card.py ---
    "材料": "Ingredients",
    "作り方": "Instructions",
    "(不明)": "(unknown)",
    # --- components/goal_task_labels.py ---
    "PF開発": "PF Dev",
    "仕事": "Work",
    "食事方針": "Diet policy",
    "運動目標": "Exercise goal",
    "睡眠目標": "Sleep goal",
    "キャリア・プロダクト戦略": "Career & product strategy",
    "その他生活全般": "Other / life",
    "進行中": "In progress",
    "達成": "Achieved",
    "中断": "Suspended",
    "数量・時間を記録する": "Log quantity & duration",
    "選ぶだけ(実績は既存タブに記録)": "Just select (recorded in the existing tab)",
    "{minutes}分以上": "{minutes}+ min",
    "{minutes}分": "{minutes} min",
    "累計{quantity}{unit}": "Total {quantity}{unit}",
    "累計{hours}時間{minutes}分": "Total {hours}h {minutes}m",
    "累計{hours}時間": "Total {hours}h",
    "累計{minutes}分": "Total {minutes}m",
    "まだ記録がありません": "No records yet",
    # --- pages/goals.py ---
    "タイトル": "Title",
    "カテゴリ": "Category",
    "期限を設定する": "Set a deadline",
    "期限": "Deadline",
    "追加する": "Add",
    "タイトルを入力してください。": "Please enter a title.",
    "長期目標を追加しました。": "Goal added.",
    "更新する": "Update",
    "更新しました。": "Updated.",
    "新しい長期目標を追加": "Add a new goal",
    "目標を編集": "Edit goal",
    "タスクを追加": "Add task",
    "記録方式": "Log type",
    "単位(例: 問)": "Unit (e.g. questions)",
    "タスクを追加しました。": "Task added.",
    "タスクを編集": "Edit task",
    "長期目標(未分類のまま残す場合は「未分類」)": (
        'Goal (choose "Unassigned" to leave it unassigned)'
    ),
    "未分類": "Unassigned",
    "アーカイブ解除": "Unarchive",
    "アーカイブする": "Archive",
    "編集": "Edit",
    "+ 新しい長期目標を追加": "+ Add a new goal",
    "まだ長期目標がありません。": "No goals yet.",
    "期限: {date}": "Deadline: {date}",
    "期限: なし": "Deadline: none",
    "タスク一覧": "Tasks",
    "まだタスクがありません。": "No tasks yet.",
    "+ タスクを追加": "+ Add task",
    "進行中にする": "Set to in progress",
    "達成にする": "Set to achieved",
    "中断する": "Suspend",
    "未分類タスク": "Unassigned tasks",
    (
        "「今日」ページでその場限りに追加したタスクが表示されます。"
        "編集から長期目標に紐付け直せます。"
    ): (
        "Tasks added on the fly from the Today page appear here. "
        "You can link them to a goal later via Edit."
    ),
    "未分類のタスクはありません。": "No unassigned tasks.",
    # --- pages/csv_import.py ---
    "睡眠": "Sleep",
    "体重": "Weight",
    "体調": "Condition",
    (
        "スプレッドシートやメモに記録していた過去のログをCSVで書き出して、"
        "このアプリへまとめて取り込めます。各タブのテンプレートに沿って"
        "CSVを準備してください。"
    ): (
        "Export past logs you kept in a spreadsheet or notes app as CSV and "
        "bulk-import them here. Prepare your CSV following each tab's template."
    ),
    "テンプレートCSVをダウンロード": "Download CSV template",
    "CSVファイルを選択": "Choose a CSV file",
    "文字コードを読み取れませんでした。UTF-8で保存し直してください。": (
        "Could not read the file encoding. Please re-save it as UTF-8."
    ),
    "データ行がありません。": "There are no data rows.",
    "有効な行: {valid}件 / エラー: {error}件": "Valid rows: {valid} / Errors: {error}",
    "行番号": "Row",
    "エラー内容": "Error",
    "有効な{count}件をインポートする": "Import {count} valid row(s)",
    "登録済みのログと同じ内容の{count}件は、重複を避けるため取り込みません。": (
        "{count} rows match existing logs and will be skipped to avoid duplicates."
    ),
    "{count}件のログをインポートしました。": "Imported {count} log(s).",
    "納豆ご飯": "Natto rice bowl",
    "日時": "Date/time",
    "区分": "Type",
    (
        "meal_typeは breakfast / lunch / dinner / snack のいずれか。"
        "AIによる推定は行わず、CSVの数値をそのまま取り込みます。"
    ): (
        "meal_type is one of breakfast / lunch / dinner / snack. "
        "No AI estimation is performed — the CSV values are imported as-is."
    ),
    "レッグプレス": "Leg press",
    "種目数": "Exercises",
    "種目": "Exercise",
    (
        "同じdate・timeの行は1回の運動セッションとしてまとめられます。"
        "categoryは cardio(duration_minutesを使用) / strength"
        "(reps・weight_kgを使用)。同じexercise_nameを複数行に分ければ"
        "複数セットとして取り込まれます。"
    ): (
        "Rows sharing the same date and time are grouped into one workout "
        "session. category is cardio (uses duration_minutes) or strength "
        "(uses reps/weight_kg). Repeat the same exercise_name on multiple "
        "rows to import multiple sets."
    ),
    "就寝": "Bedtime",
    "起床": "Wake time",
    "睡眠時間(分)": "Sleep duration (min)",
    "qualityは任意。poor / fair / good / excellent のいずれか。": (
        "quality is optional: one of poor / fair / good / excellent."
    ),
    "timeは任意(省略時は00:00として記録されます)。": (
        "time is optional (recorded as 00:00 if omitted)."
    ),
    "頭痛;倦怠感": "Headache;Fatigue",
    "症状": "Symptoms",
    (
        "condition_scoreは任意(1〜5)。symptomsは任意で、"
        "複数ある場合はセミコロン(;)区切りで記入してください。"
    ): (
        "condition_score is optional (1-5). symptoms is optional — "
        "separate multiple values with a semicolon (;)."
    ),
    "Chapter1 過去問": "Chapter 1 past exam",
    "内容": "Content",
    (
        "categoryは exam_study(試験勉強) / portfolio_dev(PF開発) / "
        "research(調べ物) / career_strategy(キャリア・プロダクト戦略設計)"
        "のいずれか。locationは任意で home/gym/coworking_space/cafeの"
        "いずれか。breakdown・keywords・notesは任意で、複数ある場合は"
        "セミコロン(;)区切りで記入してください。"
    ): (
        "category is one of exam_study, portfolio_dev, research, or "
        "career_strategy. location is optional: one of home/gym/"
        "coworking_space/cafe. breakdown, keywords, and notes are optional "
        "— separate multiple values with a semicolon (;)."
    ),
    # --- components/csv_import.py (validation errors) ---
    "{field}が空です": "{field} is empty",
    "{field}の形式が不正です(YYYY-MM-DD): {value!r}": (
        "{field} has an invalid format (YYYY-MM-DD): {value!r}"
    ),
    "{field}の形式が不正です(HH:MM): {value!r}": (
        "{field} has an invalid format (HH:MM): {value!r}"
    ),
    "{field}が数値ではありません: {value!r}": "{field} is not a number: {value!r}",
    "wake_timeはbedtimeより後である必要があります": "wake_time must be after bedtime",
    "meal_typeが空です": "meal_type is empty",
    "meal_typeが不正です({valid}のいずれか): {value!r}": (
        "meal_type is invalid (must be one of {valid}): {value!r}"
    ),
    "condition_scoreは1〜5である必要があります: {value}": (
        "condition_score must be between 1 and 5: {value}"
    ),
    "exercise_nameが空です": "exercise_name is empty",
    "categoryが不正です({valid}のいずれか): {value!r}": (
        "category is invalid (must be one of {valid}): {value!r}"
    ),
    "有効な種目がありません": "No valid exercises",
    "categoryが空です": "category is empty",
    "locationが不正です({valid}のいずれか): {value!r}": (
        "location is invalid (must be one of {valid}): {value!r}"
    ),
    # --- components/workout_form.py ---
    "{n}分": "{n} min",
    "{reps}回{weight_text} × {count}": "{reps} reps{weight_text} × {count}",
    # --- components/pdca_status.py ---
    "済": "Done",
    "一部": "Partial",
    "未": "Not yet",
    # --- pages/today.py ---
    "日付": "Date",
    "時刻": "Time",
    "メモ(任意)": "Memo (optional)",
    "本当に削除しますか?(元に戻せません)": "Are you sure you want to delete? (cannot be undone)",
    "削除する": "Delete",
    "削除しました。": "Deleted.",
    "削除するには「本当に削除しますか?」にチェックを入れてください。": (
        'Check "Are you sure you want to delete?" to delete.'
    ),
    "食事記録を編集": "Edit meal record",
    "食事区分": "Meal type",
    "タンパク質(g)": "Protein (g)",
    "脂質(g)": "Fat (g)",
    "炭水化物(g)": "Carbs (g)",
    "種目名": "Exercise name",
    "例: レッグプレス": "e.g. Leg press",
    "🗑削除": "🗑 Delete",
    "筋トレ": "Strength",
    "有酸素": "Cardio",
    "時間(分)": "Duration (min)",
    "**{n}セット目**": "**Set {n}**",
    "回数": "Reps",
    "重量(kg)": "Weight (kg)",
    "+ セット追加": "+ Add set",
    "運動記録を編集": "Edit workout",
    "+ 種目を追加": "+ Add exercise",
    "有効な種目が入力されていません。": "No valid exercises entered.",
    "前回と同じメニューを入力": "Use the same menu as last time",
    "よく使う種目を追加": "Add frequently used exercises",
    "{name}({category}・{count}回)": "{name} ({category}, {count}x)",
    "選択した種目を追加する": "Add selected exercises",
    "よく使う種目はまだありません。": "No frequently used exercises yet.",
    "運動記録({count}種目)を保存しました。": "Saved workout record ({count} exercises).",
    "運動記録を保存する": "Save workout record",
    "睡眠記録を編集": "Edit sleep record",
    "就寝日": "Bedtime date",
    "就寝時刻": "Bedtime",
    "起床日": "Wake date",
    "起床時刻": "Wake time",
    "起床時刻は就寝時刻より後にしてください。": "Wake time must be after bedtime.",
    "体重記録を編集": "Edit weight record",
    "総合スコア(1=不調 〜 5=良好)": "Overall score (1=poor - 5=great)",
    "朝の体調(1〜5)": "Morning condition (1-5)",
    "夜の体調(1〜5)": "Evening condition (1-5)",
    "メンタル(1〜5)": "Mental (1-5)",
    "疲労(1〜5)": "Fatigue (1-5)",
    "ストレス(1〜5)": "Stress (1-5)",
    "体調記録を編集": "Edit condition record",
    "症状(カンマ区切り、任意)": "Symptoms (comma-separated, optional)",
    "試験勉強": "Exam study",
    "調べ物": "Research",
    "キャリア・プロダクト戦略設計": "Career & product strategy",
    "未選択": "Not selected",
    "自宅": "Home",
    "ジム": "Gym",
    "コワーキングスペース": "Coworking space",
    "カフェ": "Cafe",
    "例: ○○問題集 過去問": "e.g. Past exam questions",
    "例: 個人ブログのSSR化": "e.g. Adding SSR to a personal blog",
    "勉強内容": "Study content",
    "PF開発内容": "PF dev content",
    "内訳(カンマ区切り)": "Breakdown (comma-separated)",
    "例: Chapter3, Chapter5": "e.g. Chapter 3, Chapter 5",
    "時間": "Hours",
    "分": "Minutes",
    "技術的成長キーワード(スラッシュ区切り)": "Growth keywords (slash-separated)",
    "例: Python / SQL": "e.g. Python / SQL",
    "時間(h)": "Hours (h)",
    "箇条書きメモ(1行1項目)": "Bullet notes (one item per line)",
    "例: ・案A: 新規事業\n・案B: 既存機能強化": (
        "e.g. - Option A: New business\n- Option B: Improve existing features"
    ),
    "学習記録を編集": "Edit learning record",
    "場所": "Location",
    "学習記録を保存しました。": "Learning record saved.",
    "学習記録を保存する": "Save learning record",
    "前回と同じ内容を入力": "Use the same content as last time",
    "よく使うキーワードを追加": "Add frequently used keywords",
    "{keyword}({count}回)": "{keyword} ({count}x)",
    "選択したキーワードを追加する": "Add selected keywords",
    "よく使うキーワードはまだありません。": "No frequently used keywords yet.",
    "前日の改善点(A): {point}": "Yesterday's improvement point (A): {point}",
    "▼ P: 今日の計画": "▼ P: Today's plan",
    "前日の計画を初期表示しています。内容を確認し「Pを保存する」で確定してください。": (
        'Showing yesterday\'s plan by default. Review it and click "Save P" to confirm.'
    ),
    "{category}: まだタスクがありません。": "{category}: No tasks yet.",
    "+ その場でタスクを追加(イレギュラー対応)": "+ Add a task on the fly (ad hoc)",
    "タスクを追加しました。上の一覧から選択して「Pを保存する」してください。": (
        'Task added. Select it from the list above and click "Save P".'
    ),
    "Pを保存する": "Save P",
    "Pを保存しました。": "P saved.",
    "▼ D: 実績": "▼ D: Records",
    "睡眠記録({minutes}分)を保存しました。": "Saved sleep record ({minutes} min).",
    "睡眠記録を保存する": "Save sleep record",
    "編集する": "Edit",
    "体重記録を保存しました。": "Weight record saved.",
    "体重記録を保存する": "Save weight record",
    "体調(5軸)": "Condition (5 axes)",
    "例: 頭痛, 倦怠感": "e.g. Headache, fatigue",
    "体調記録を保存しました。": "Condition record saved.",
    "体調記録を保存する": "Save condition record",
    "前回と同じ内容を入力する": "Use the same content as last time",
    "よく使う食事": "Frequently used meals",
    "{memo}({count}回)": "{memo} ({count}x)",
    "選んだ食事を入力": "Use the selected meal",
    "よく使う食事はまだありません(メモ付きで記録すると候補に出ます)。": (
        "No frequently used meals yet (log with a memo to see suggestions here)."
    ),
    (
        "食べたものを文章で入力すると、AIがカロリー・PFCを推定してフォームに"
        "反映します(あくまで目安です。記録前に下記フォームで確認・修正してください)。"
    ): (
        "Describe what you ate and AI will estimate calories/PFC and fill in the "
        "form (an estimate only — please check and adjust before saving)."
    ),
    "食べたもの": "What you ate",
    "例: 納豆1パック、ご飯茶碗1杯": "e.g. 1 pack of natto, 1 bowl of rice",
    "AIで栄養を推定": "Estimate nutrition with AI",
    "食べたものを入力してください。": "Please enter what you ate.",
    "栄養を推定しています...": "Estimating nutrition...",
    "栄養推定に失敗しました: {error}": "Failed to estimate nutrition: {error}",
    (
        "推定結果を下記フォームに反映しました。必要に応じて修正してから記録してください。"
    ): "Applied the estimate to the form below. Adjust it if needed before saving.",
    "食事記録を保存しました。": "Meal record saved.",
    "食事記録を保存する": "Save meal record",
    "Pで「数量・時間を記録する」タスクを選ぶと、ここに実績入力欄が表示されます。": (
        'Select a "log quantity & duration" task in P to see input fields here.'
    ),
    "数量": "Quantity",
    "未記録": "Not recorded",
    "保存": "Save",
    "保存しました。": "Saved.",
    "学習ログ(自由記述: 試験勉強・PF開発・調べ物・キャリア戦略)": (
        "Learning log (free-form: exam study, PF dev, research, career strategy)"
    ),
    "まだ記録がありません。": "No records yet.",
    "学習・PF開発・仕事": "Study/PF Dev/Work",
    "📋 レシピから材料を追加": "📋 Add ingredients from a recipe",
    "材料をメモに追加": "Add ingredients to memo",
    "まだ生成されたレシピがありません(「レシピ」ページで生成できます)。": (
        'No recipes generated yet (you can generate one on the "Recipe" page).'
    ),
    "買い物メモ": "Shopping memo",
    "家計を保存する": "Save household",
    "▼ C: 振り返り": "▼ C: Reflection",
    "振り返り": "Reflection",
    "Cを保存する": "Save C",
    "▼ A: 明日変えること": "▼ A: What to change tomorrow",
    "改善すること(1つ)": "One thing to improve",
    "料理・買い物メモ": "Cooking & shopping notes",
    "学習準備メモ": "Study prep notes",
    "Aを保存する": "Save A",
}
