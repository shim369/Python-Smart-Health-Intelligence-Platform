# Smart Health Intelligence Platform 要件定義書

## 1. 文書概要

### 1.1 プロジェクト名

**Python Smart Health Intelligence Platform**

### 1.2 目的

本システムは、ユーザーの健康データを継続的に収集・蓄積し、Feature Engineering、ルールベース分析、健康スコアリング、Recommendation、AI、機械学習を組み合わせることで、ユーザーの健康状態の把握および健康改善を支援する。

単純な健康記録アプリではなく、

```text
健康データ記録
    ↓
データ蓄積
    ↓
Feature Engineering
    ↓
Analysis
    ↓
Health Score
    ↓
Rule-based Recommendation
    ↓
AI
    ↓
ML
    ↓
評価・比較
    ↓
製品機能への統合
```

という段階的なデータ活用基盤を構築する。

---

# 2. システムの基本方針

## 2.1 データ駆動型健康管理

ユーザーが入力した健康データを蓄積し、単なる記録として終わらせず、分析可能な特徴量へ変換する。

## 2.2 Deterministic Analysisを基本とする

健康データの集計、Feature Engineering、基本的な分析、Health Scoreなど、再現性が必要な処理は原則としてプログラムによる決定論的処理として実装する。

AIに健康データ処理そのものを全面的に依存しない。

## 2.3 Rule-basedをBaselineとして構築する

Recommendation機能は、まずRule-based方式で実装する。

Rule-based Recommendationは以下の役割を持つ。

* 初期Recommendation Engine
* ML評価時のBaseline
* ML利用不能時のFallback
* データ不足時のFallback
* MLがRule-basedを上回らない場合の代替方式

## 2.4 AIとMLの役割を分離する

AIは主として生成・説明・レシピ生成などに利用する。

MLは健康データから予測・推薦を行うためのモデルとして検証する。

AIとMLを同一の仕組みとして扱わない。

---

# 3. 想定ユーザー

## 3.1 対象ユーザー

一般ユーザーを対象とする。

## 3.2 マルチユーザー

システムは複数ユーザーによる利用を前提として設計する。

ユーザーごとに一意な `user_id` を持ち、ユーザー所有データは原則として `user_id` によって識別・分離する。

シングルユーザー環境で開発・テストする場合でも、ドメインおよびRepository設計はマルチユーザーを前提とする。

---

# 4. 機能要件

## 4.1 ユーザー管理

システムはユーザーを管理する。

### 必須要件

* Userを一意に識別できること
* `user_id` を持つこと
* 認証済みユーザーを取得できること
* ユーザーごとにデータを分離できること

---

## 4.2 健康データ管理

以下の健康データを管理する。

### HealthLog

MealLog / WorkoutLog / SleepLog / WeightLogでカバーしない、体調・症状・気分など汎用的な健康記録の受け皿として管理する。

主な情報：

* 記録日時
* 総合体調スコア(自己申告、1〜5)
* 体調5軸(いずれも任意、1〜5): 朝の体調・夜の体調・メンタル・疲労・ストレス
* 症状(自由記述タグ、複数可、任意)
* メモ(任意)

用途が広いドメインのため、フィールド構成は意図的に最小限にとどめており、実運用しながら見直す前提とする(5軸化は実運用を経て行った見直しの一例)。

### MealLog

食事記録を管理する。

主な情報：

* 摂取日時
* 食事区分
* Calories
* Protein
* Fat
* Carbohydrate
* その他必要な栄養情報

### WorkoutLog

運動記録を管理する。1回の運動セッションは複数の種目からなり、種目ごとに以下のいずれかの形式で記録する。

* **有酸素運動**: 種目名、実施時間(分)
* **筋力トレーニング**: 種目名、セットごとの回数・重さ(セットごとに回数・重さが異なる場合も表現できること。例: 同一種目内で1セット目30kg、2セット目20kg)

主な情報(セッション単位)：

* 実施日時
* 種目一覧(種目名・カテゴリ・時間 または セット一覧)
* 消費カロリー(任意、ウェアラブル端末等から取得した場合)
* メモ

### SleepLog

睡眠記録を管理する。

主な情報：

* 睡眠日時
* 就寝時刻
* 起床時刻
* 睡眠時間
* 睡眠品質等

### WeightLog

体重記録を管理する。

主な情報：

* 記録日時
* 体重

---

## 4.3 学習ログ管理

### LearningLog

試験勉強・PF開発・調べ物・キャリア/プロダクト戦略設計といった、健康データ以外の日々の学習・自己投資活動の記録を管理する。`category`によって使用するフィールドが異なる点はWorkoutLogのカテゴリ依存設計と同様とする。

* **試験勉強**: 勉強内容、内訳(章立て等)、勉強時間、技術的成長キーワード
* **PF開発**: 開発内容、開発時間、技術的成長キーワード
* **調べ物**: 技術的成長キーワードのみ
* **キャリア/プロダクト戦略設計**: 取り組み時間、箇条書きメモ

主な情報(共通)：

* 開始日時
* カテゴリ
* 場所(自宅/ジム/コワーキングスペース/カフェ、任意)

過去の記録から頻出する技術的成長キーワードを候補として提示し、入力の手間を減らすクイック入力機能を持つ。

---

## 4.4 目標・タスク管理(Goal / Task)

Macメモでの手動運用(1日をP(計画)→D(実績)→C(振り返り)→A(改善)の形式で記録し、最後にAIへ手動でプロンプトを渡して採点・評価させる運用)をアプリに統合するための機能。

学習・PF開発・仕事は当初「自由記述メモ1本」で検討したが、以下の理由から選択式のGoal(長期目標)/Task(関連タスク)構造を採用した。

* 「習慣を継続すること」を最優先すると、自由記述より選ぶだけの方が記録の摩擦が少ない
* 選択式にすることで、長期目標ごとの進捗集計(例: 「Python試験の演習、累計450問」)が自然に可能になる
* 時間は15分刻みのドロップダウンから選ぶだけにすることで、数値記録でも面倒さを増やさない

このデータはHealth Score/MLの入力にはしない(既存5ドメインほどの厳密な正規化を課さない)。

### Goal

長期目標を管理する。主な情報：タイトル、カテゴリ、期限(任意)、ステータス(進行中/達成/中断)。ステータス変更・アーカイブは長期目標管理画面から行う。

### Task

Goalに紐づく、またはGoalを持たない単発のタスクを管理する。カテゴリは学習/PF開発/仕事/食事方針/運動目標/睡眠目標/キャリア・プロダクト戦略/その他生活全般の8区分。`log_type`により以下2方式のいずれかで実績を記録する。

* **数量・時間記録方式(COUNT_AND_DURATION)**: 学習/PF開発/仕事のタスクが対象。日々の実績として数量(任意)・時間(15分刻み: 15/30/45/60/90/120分。120分は「120分以上」を表す)・一言メモ(任意)を記録する
* **選択のみ方式(PLAN_ONLY)**: 食事方針/運動目標/睡眠目標のタスクが対象。その日の計画として選ぶのみで、実績は既存のMealLog/WorkoutLog/SleepLogが担う

Taskは以下2つの経路で作成できる。

* **経路A(主)**: 長期目標管理画面で、Goalの下にまとめて登録する。`goal_id`が埋まり、進捗集計の対象になる
* **経路B(副)**: 「今日」ページのP(計画)画面から、その場で単発追加する(イレギュラー対応)。タイトルとカテゴリのみで追加でき、`goal_id`は空のまま(後から長期目標管理画面で目標に紐付け直すことも可能)

使わなくなったTaskは`is_archived`で一覧から隠す(削除はしない)。

> 検討の結果、Taskの時間集計とは別に「その日の総勤務時間」のような1日単位の集計値は持たない方針とした(初期検討ではDailyJournalへの追加を候補としたが、見送った)。

### DailyPlanItem / DailyTaskLog

「今日」ページのP(計画)・D(実績)に対応する日次記録。それぞれ`(user_id, journal_date, task_id)`の組み合わせで1レコード。

P画面を開いた際の挙動：

* その日のPが既に保存済みであれば、そのまま表示する(自由に再編集・再保存可能)
* 未保存であれば、前日のP(選択していたTask一式)をそのまま複製して初期表示する。あわせて前日のA「改善すること」を読み取り専用で画面上部に表示する(Pの各項目への自動反映はせず、ユーザーが見て手動で反映するかどうかを判断する)
* 「保存」操作で確定する

---

## 4.5 Daily Journal(P/C/A・家計)

1日をP(計画)→D(実績)→C(振り返り)→A(改善)の形式で記録する。学習・PF開発・仕事はGoal/Task方式(4.4節)に切り出されているため、DailyJournalはそれ以外のP/C/A項目と家計の入口のみを持つ。食事方針・運動目標・起床/就寝目標は4.4節のTask選択(PLAN_ONLY)が主であり、DailyJournal側のフィールドはあくまで補足メモの位置づけとする。

主な情報：

* [P] 食事方針の補足メモ、起床目標時刻、就寝目標時刻(いずれも任意)
* [D] 買い物メモ(自由記述)、食費合計(円、任意。本格的な家計簿機能ではなく入口の位置づけ)
* [C] 振り返りメモ(自由記述)
* [A] 明日変えること(1つ、自由記述)、料理・買い物メモ、学習準備メモ

1ユーザー・1日につき1レコードとする。Goal/Task/DailyJournalのデータはHealth Score/MLの入力にはしない。

### 買い物メモとレシピ機能の連動

買い物メモは自由記述だが、直近生成したレシピの材料をワンタップで差し込める(新しいテーブルは追加せず、既存のRecipe/RecipeIngredientから材料名を取得してテキストへ追記するだけの軽量な機能)。

```text
[買い物メモ]欄(自由記述)
[📋 レシピから材料を追加 ▼]
  → 直近のレシピ履歴から選択
  → 選んだレシピの材料名を "レシピ名: 材料1, 材料2, ..." の形式でメモ欄に追記
  → 追記後は自由に編集可能(家にある食材を消す等)
```

### 既存ドメインとの関係

| 既存ドメイン | Daily Journal機能との関係 |
|---|---|
| MealLog | 変更なし。食事方針(DIETカテゴリのPLAN_ONLY Task)を選び、実績は引き続きMealLogに記録する |
| WorkoutLog | 変更なし。運動目標(EXERCISEカテゴリのPLAN_ONLY Task)を選び、実績は引き続きWorkoutLogに記録する |
| SleepLog | 変更なし。起床/就寝目標(SLEEPカテゴリのPLAN_ONLY Task)を選び、実績は引き続きSleepLogに記録する |
| WeightLog | 変更なし |
| HealthLog | 4.2節の体調5軸拡張はこの機能に伴う見直し |
| Recipe / RecipeIngredient | 上記の通り、買い物メモへの材料差し込みに利用(読み取りのみ、新規書き込みはしない) |
| RecommendationService / Health Score | 変更なし。Goal/Task/DailyJournalのデータはHealth Score/MLの入力にしない |

---

## 4.6 多言語対応(i18n)

UI表示言語として日本語(既定)と英語を切り替えられること。表示言語はユーザーごとにDBへ永続化し、ログイン時にSession Stateへ復元する。未翻訳の文言があってもアプリの動作を妨げないこと(該当文言は日本語のままフォールバック表示する)。

---

# 5. 食材・レシピ管理

## 5.1 Ingredient

食材マスタを管理する。

Ingredientはシステム共通データとして扱うことを基本とし、原則として `user_id` を持たない。

## 5.2 Recipe

レシピを管理する。

AIによって生成されたレシピも保存対象とする。

ユーザーが生成・保存したRecipeは原則として `user_id` によって所有者を識別する。

## 5.3 RecipeIngredient

RecipeとIngredientの関連を管理する。

---

# 6. Feature Engineering

蓄積された健康データを分析可能な特徴量へ変換する。

### 対象例

#### 日次特徴量

* Daily Calories
* Daily Protein
* Daily Fat
* Daily Carbohydrate
* Daily Sleep Duration
* Daily Workout Duration
* Daily Weight

#### 週間特徴量

* 週間平均Calories
* 週間平均PFC
* 週間平均睡眠時間
* 週間運動回数
* 週間運動時間

#### Weight Features

* 7日移動平均
* 体重変化量
* 体重変化率

#### Nutrition Features

* PFC
* PFCバランス
* Caloriesの目標値との差分

#### Sleep Features

* 平均睡眠時間
* 睡眠不足日数
* 睡眠時間の変動

#### Workout Features

* 運動頻度
* 運動時間
* 運動強度

---

# 7. Analysis

Feature Engineeringされたデータを利用して健康状態を分析する。

以下のAnalyzerを実装する。

* Weight Analyzer
* Nutrition Analyzer
* Sleep Analyzer
* Workout Analyzer

各Analyzerは、可能な限り決定論的・再現可能な処理として実装する。

---

# 8. Health Score

複数の健康指標を統合し、システム独自のHealth Scoreを算出する。

対象例：

* Nutrition Score
* Weight Score
* Sleep Score
* Workout Score

これらを統合して総合的なHealth Scoreを算出する。

Health Scoreは医療診断、疾病予測、医学的な健康判定を目的とするものではなく、本システムにおける健康管理支援のための指標として扱う。

---

# 9. Recommendation

## 9.1 Rule-based Recommendation

初期Recommendation EngineはRule-based方式で実装する。

例：

```text
睡眠時間 < 基準値
    ↓
睡眠改善Recommendation

Protein < 目標値
    ↓
Protein摂取改善Recommendation
```

Rule-based RecommendationはML導入前のBaselineとして利用する。

---

## 9.2 ML Recommendation

ML Pipelineでは、健康データから生成したFeature Datasetを利用し、RecommendationへのML適用可能性を検証する。

ML Pipelineには以下を含む。

* Dataset生成
* データ量確認
* 欠損値確認
* Feature Dataset生成
* Baseline構築
* LightGBMによる学習
* 評価
* 推論
* MLflowによる実験管理
* 実験比較

---

## 9.3 ML採用判断

**MLモデルの実装自体は必須とする。** ただし、最終的なRecommendation EngineへのML統合は評価結果に基づいて判断する。

以下の3つの判断を許容する。

### ML採用

MLがRule-based Baselineを十分に上回り、汎化性能・安定性等の観点から製品利用に適すると判断した場合。

```text
Recommendation
      ↓
     ML
```

### ML限定採用

Recommendationの一部領域のみMLが有効な場合。

例：

```text
Nutrition → ML
Weight    → ML
Sleep     → Rule-based
Workout   → Rule-based
```

すべての領域でMLを採用する必要はない。

### ML見送り

MLがRule-based Baselineを上回らない、データ量が不足している、汎化性能が不十分などの理由により、製品Recommendationへの統合を見送る場合。

```text
Recommendation
      ↓
Rule-based
```

ML Pipeline自体は構築・評価するが、製品Recommendationへの統合は見送ることができる。

### 9.3.1 判断基準(数値)

上記3判断(採用/限定採用/見送り)は、以下の数値基準に基づいて行う。**Nutrition/Weight/Sleep/Workoutの各領域ごとに独立して判定する**(ML限定採用に対応するため)。

| 項目 | 基準 |
|---|---|
| 評価指標 | 目的変数が連続値(回帰)の場合はMAE(平均絶対誤差)、カテゴリ(分類)の場合はF1スコア。目的変数そのものの定義はPhase 8(ML Pipeline)で確定する |
| 改善率閾値 | Rule-based Baselineに対し、評価指標が相対**10%以上**改善していること |
| 過学習チェック | train誤差とvalidation誤差の差が相対**20%以内**であること。これを超える場合は改善率閾値を満たしていても不採用とする |
| 最低データ量 | 対象領域につき**60日分以上**のログが存在し、かつ欠損率が**30%未満**であること。満たさない場合は評価を待たずに当該領域を見送りとする |
| 評価方法 | ランダムなtrain/test分割ではなく、時系列の未来データがリークしないよう**forward-chaining(時系列考慮)のK分割交差検証**を用いる |

判定手順の概要：

```text
領域を1つ選択
    ↓
データ量・欠損率が基準を満たすか？
    NO → 見送り(Rule-based継続)
    YES ↓
forward-chaining CVでMLとBaselineを評価
    ↓
改善率 ≥ 10% かつ 過学習チェックOK？
    NO → 見送り(Rule-based継続)
    YES → 採用
    ↓
全領域で判定 → 採用領域と見送り領域の組み合わせが
              「ML採用」「ML限定採用」「ML見送り」のいずれかを構成する
```

---

## 9.4 Fallback

MLを製品Recommendationへ統合する場合でも、Rule-based RecommendationをFallbackとして保持することを要件とする。

以下の場合にはRule-based RecommendationへFallbackできることを要件とする。

* MLモデルが利用できない
* ML推論でエラーが発生した
* 学習データが不足している
* MLモデルの評価結果が基準を満たさない
* 特定Recommendation領域ではMLを採用しない
* MLモデルの更新・運用に問題がある

---

# 10. AI機能

## 10.1 AI Provider

AIサービスへの依存を抽象化するため、AI Provider Interfaceを定義する。

実装例：

```text
AIProvider
├── GeminiProvider
└── FakeAIProvider
```

Service層は具体的なAIサービスに直接依存しない。

---

## 10.2 Gemini

Gemini APIを利用したAI機能を実装する。

主な用途：

* AIレシピ生成
* レシピ内容の構造化
* 健康改善提案の補助
* 自然言語による説明

---

## 10.3 Structured Output

AIからのレスポンスは可能な限りStructured Outputを利用する。

Pydantic SchemaによってレスポンスをValidationする。

Validation Error発生時には適切にエラー処理する。

---

## 10.4 AI Retry / Timeout

AI APIでは以下の障害を想定する。

* Timeout
* 429 Rate Limit
* 503 Service Unavailable
* Validation Error
* その他APIエラー

429および503についてはRetry対象とし、指数バックオフを利用する。

Validation ErrorおよびRetry対象外のエラーは無条件に再試行しない。

### 10.4.1 数値基準

| 項目 | 値 |
|---|---|
| 最大試行回数 | 3回(初回+リトライ2回) |
| バックオフ基準秒数 | 1秒(2倍の指数バックオフ、Jitter ±20%) |
| 1回あたりのTimeout | 20秒 |
| 最悪ケース総待ち時間 | 約63秒 |

これを超えて待ち続けることはなく、最終的に失敗した場合はエラーとしてユーザーへ通知する(UI側の表示方法はPhase 6で確定)。

---

# 11. AI Recipe Engine

AIを利用してユーザーが指定した食材等からレシピを生成する。

処理フロー：

```text
ユーザー食材入力
    ↓
RecipeInput
    ↓
Prompt Builder
    ↓
AI Provider
    ↓
Structured Output
    ↓
Pydantic Validation
    ↓
Recipe
    ↓
保存
    ↓
履歴
```

生成されたRecipeはユーザーごとに管理する。

Recipe Cacheを導入し、不要なAI API呼び出しを抑制する。

---

# 12. 認証・Session

## 12.1 Authentication

ログイン・ログアウト機能を実装する。認証方式はGoogle OAuth(OpenID Connect)とし、
Streamlit標準の`st.login()` / `st.user` / `st.logout()`(Authlibベース)を利用する。
自前のパスワード管理は行わない。許可リスト(`ALLOWED_EMAILS`)は任意機能とし、
未設定時は誰でもログイン可能とする。

## 12.2 Session State

StreamlitのSession Stateを利用して認証状態等を管理する。

Session Stateには必要最小限の状態のみ保持し、永続データの保存場所として利用しない。

## 12.3 Session Lifecycle

基本的なライフサイクル：

```text
Login
 ↓
Authenticated User
 ↓
user_id取得
 ↓
Session State
 ↓
Service
 ↓
Repository
 ↓
Database
```

Logout時や認証状態が無効になった場合には、ユーザー固有のSession Stateを適切にリセットする。

---

# 13. user_id・データ分離要件

## 13.1 ユーザー所有データ

以下のデータは原則として `user_id` を必須とする。

* HealthLog
* MealLog
* WorkoutLog
* SleepLog
* WeightLog
* LearningLog
* Recipe
* Goal
* Task
* DailyPlanItem
* DailyTaskLog
* DailyJournal

## 13.2 共通データ

以下のようなシステム共通マスタは、原則として `user_id` を持たない。

* Ingredient

## 13.3 Repository境界

ユーザー所有データを取得・更新・削除するRepositoryは、原則として `user_id` を境界条件として扱う。

ユーザーAがユーザーBのデータへアクセスできないことをIntegration Testで検証する。

## 13.4 内部処理・バッチ

システム内部のバッチ処理等で `user_id` が存在しない場合は、ユーザーコンテキストを必要としないSystem Contextとして明示的に扱う。

ユーザー所有データを処理する内部処理では、原則として対象ユーザーを明示的に指定する。

---

# 14. データ永続化

PostgreSQLを主要な永続化データベースとして利用する。

以下を利用する。

* SQLAlchemy
* Alembic
* psycopg3

Repository Patternを採用し、Domain層およびService層からデータベース実装詳細を分離する。

複数テーブル・複数Repositoryにまたがる更新処理は、単一トランザクションとして扱い、一部のみが更新される状態(部分的更新)を防止することを要件とする。トランザクション境界はService/Unit of Work側で管理し、Repositoryが独自にcommit/rollbackを行わないこととする。

---

# 15. アーキテクチャ要件

基本的な依存方向は以下とする。

```text
Streamlit UI
     ↓
Service
     ↓
Domain
     ↓
Repository Interface
     ↓
Repository Implementation
     ↓
PostgreSQL
```

外部サービスについては、Provider等のInterfaceを介して依存を抽象化する。

```text
Recipe Service
     ↓
AIProvider
     ↑
 ┌───┴────┐
 │        │
Gemini   Fake
```

Domain層はInfrastructureの具体的な実装へ直接依存しない。

---

# 16. テスト要件

## 16.1 Unit Test

以下をUnit Test対象とする。

* Domain Model
* Feature Engineering
* Analyzer
* Health Score
* Recommendation
* Recipe
* Prompt Builder
* Nutrition Calculator
* AI Provider
* ML関連ロジック

## 16.2 Repository Test

RepositoryのCRUDおよびuser_id境界を検証する。

## 16.3 Integration Test

以下の処理を検証する。

* Health Data Flow
* Recipe Flow
* Authentication Flow
* user_idによるデータ分離
* AI Error / Retry
* Repository → Database
* トランザクション境界・Rollback(複数Repositoryにまたがる更新の部分的失敗時)

## 16.4 E2E Test

主要なユーザー操作を通したシステム全体の動作を検証する。

---

# 17. 非機能要件

## 17.1 開発環境

* Python 3.13
* uv
* Ruff
* mypy
* pytest
* pytest-cov
* GitHub Actions

## 17.2 コード品質

* 型安全性を重視する
* RuffによるLint / Formatを実施する
* mypyによる型チェックを実施する
* pytestによる自動テストを実施する

## 17.3 CI

Pull RequestおよびPush時に以下を自動実行する。

```text
Ruff
 ↓
Ruff Format Check
 ↓
mypy
 ↓
pytest
```

## 17.4 セキュリティ

* API Keyをソースコードへ直接記述しない
* SecretsをGit管理しない
* `.env`をGit管理しない
* ユーザー間のデータアクセスを分離する
* AI APIへの入力データを適切に制御する

## 17.5 信頼性

* Database Transactionを適切に管理し、複数テーブルにまたがる更新の部分的失敗を防止する(Unit of Workによるトランザクション境界の一元管理)
* Exceptionを適切に処理する
* AI APIのTimeoutを設定する
* Retry対象を明確にする
* AI障害時のFallbackを用意する
* Loggingを実装する

---

# 18. Streamlit Dashboard

最終的にStreamlitによるWebアプリケーションとして提供する。

主な画面：

* ログイン(Google OAuth。初回ログイン時にUserを自動作成するため、別画面での新規登録は不要)
* Dashboard(ダッシュボード)
* 今日(1日分のP/D/C/Aを1画面で完結させるカード型UI。睡眠・体調・食事・運動・学習/PF開発/仕事・家計の実績入力と、長期目標管理画面で登録したTaskの選択をここで行う。詳細は4.4節・4.5節参照)
* 長期目標(Goal/Taskの一覧・追加・編集・ステータス変更・アーカイブ)
* CSVインポート(食事・運動・睡眠・体重・体調・学習ログの一括登録)
* AI Recipe Generator(レシピ)

サイドバーから表示言語(日本語/英語)を切り替えられる(4.6節)。

Dashboardでは過去7日間について以下をグラフで表示する。

* 睡眠時間・体調スコア(総合/朝/夜/メンタル/疲労/ストレス)
* カロリー・PFC
* 学習時間・作業時間(学習ログ + Task実績)
* 運動セッション数・有酸素運動時間
* 食費合計

> Health ScoreおよびRule-based Recommendationは8章・9章の通りバックエンドでは実装済みだが、現在のUIでは表示していない(過去にダッシュボードへ表示していたが、週間グラフ中心の構成へ変更した際に外した)。再度UIへ統合する場合は別途設計する。

---

# 19. ML Pipeline

ML Pipelineは本プロジェクトの正式な開発対象とする。

以下を実装する。

```text
Dataset
 ↓
Data Quality Check
 ↓
Feature Dataset
 ↓
Baseline
 ↓
LightGBM
 ↓
Training
 ↓
Evaluation
 ↓
Prediction
 ↓
MLflow Tracking
 ↓
Experiment Comparison
```

ML Pipelineの開発後、Rule-based Baselineとの比較を行う。

MLモデルの製品採用については、以下を評価する。

* 予測性能
* Recommendation性能
* 汎化性能
* 過学習
* 実データでの性能
* 安定性
* 運用コスト
* Rule-basedとの比較

---

# 20. V1.0スコープ

V1.0では以下を開発対象とする。

* User Management
* Authentication
* Multi-user Data Isolation
* Health Data Management
* PostgreSQL Persistence
* Repository Pattern
* Feature Engineering
* Analysis
* Health Score
* Rule-based Recommendation
* AI Provider
* Gemini Integration
* AI Recipe Engine
* Recipe History / Cache
* Streamlit Dashboard
* ML Pipeline
* LightGBM
* MLflow
* ML Evaluation
* Rule-based Baseline Comparison
* ML採用 / 限定採用 / 見送り判断
* ML Recommendation IntegrationまたはRule-based Fallback
* Unit / Integration / E2E Test
* CI
* Logging / Exception Handling

---

# 21. 将来拡張

V1.0完成後の拡張候補として以下を想定する。

* より高度なMLモデル
* 個人最適化
* 推薦精度向上
* モデル再学習
* Model Monitoring
* AIによる高度な健康分析
* より高度なレシピ最適化
* 外部健康データとの連携
* モバイル体験のさらなる改善(ログ入力画面はカード型UIへ移行済みだが、ダッシュボード等は未対応)
* API化
* 複数AI Provider対応
* 本格的な家計簿機能(収支管理、カテゴリ別支出等)。DailyJournalの`food_expense_yen`はあくまで入口であり、詳細な家計管理は将来設計する
* 学習・PF開発・仕事の時間からのAI推定(記録の代わりにAIに時間を推定させる等)
* AI評価・採点機能(PDCA評価、100点満点採点等。「今日」ページのC/A記録を素材にAIへ評価させる運用)

ただし、これらはV1.0の必須要件には含めない。

---

# 22. 設計上の重要原則

本プロジェクトでは以下を基本原則とする。

1. **データを正しく蓄積することを最優先する**
2. **Deterministicな処理とAI/MLを分離する**
3. **Rule-based RecommendationをBaselineとして維持する**
4. **AI Providerを抽象化する**
5. **MLは実装・評価し、性能に基づいて採用判断する**
6. **MLを採用する場合でもFallbackを用意する**
7. **ユーザーデータを`user_id`によって明確に分離する**
8. **DomainとInfrastructureを分離する**
9. **複数Repositoryにまたがる更新はUnit of Workで一貫性を保証する**
10. **テスト可能な設計を優先する**
11. **CIを常にGreenに維持する**
