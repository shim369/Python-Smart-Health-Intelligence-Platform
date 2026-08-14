うん。ここまで決めた内容なら、もう `docs/requirements.md` に落としていい段階。

特に今回は、**MLを必ず開発する／ただし最終製品での採用は評価結果で決める／採用しない場合はRule-basedをFallbackとして残す**、この3点を明文化しておく。

`requirements.md` は、まず以下の内容で初版を作るのがいい。

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

健康状態に関する基本的な記録を管理する。

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

運動記録を管理する。

主な情報：

* 実施日時
* 運動種別
* 運動時間
* 運動強度
* 消費カロリー等

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

MLモデルの実装自体は必須とする。

ただし、最終的なRecommendation EngineへのML統合は評価結果に基づいて判断する。

以下の3つの判断を許容する。

### ML採用

MLがRule-based Baselineを十分に上回り、汎化性能・安定性等の観点から製品利用に適すると判断した場合。

### ML限定採用

Recommendationの一部領域のみMLが有効な場合。

例：

```text
Nutrition → ML
Weight    → ML
Sleep     → Rule-based
Workout   → Rule-based
```

### ML見送り

MLがRule-based Baselineを上回らない、データ量が不足している、汎化性能が不十分などの理由により、製品Recommendationへの統合を見送る場合。

---

## 9.4 Fallback

MLを製品Recommendationへ統合する場合でも、Rule-based RecommendationをFallbackとして保持する。

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

ログイン・ログアウト機能を実装する。

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
* Recipe

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

* Database Transactionを適切に管理する
* Exceptionを適切に処理する
* AI APIのTimeoutを設定する
* Retry対象を明確にする
* AI障害時のFallbackを用意する
* Loggingを実装する

---

# 18. Streamlit Dashboard

最終的にStreamlitによるWebアプリケーションとして提供する。

主な画面：

* Dashboard
* Health Logs
* Meal Logs
* Workout Logs
* Sleep Logs
* Weight Logs
* AI Recipe Generator

Dashboardでは以下を表示する。

* Health Score
* 週間サマリー
* 体重推移
* PFC推移
* 睡眠状況
* 運動状況
* Recommendation

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

# 21. V1.0におけるMLの扱い

ML Pipelineの構築は必須とする。

一方、MLモデルを最終的な製品Recommendationへ統合するかどうかは、ML評価結果に基づいて決定する。

最終的な構成は以下のいずれかとする。

```text
ML採用

Recommendation
      ↓
     ML
```

または、

```text
ML限定採用

Nutrition → ML
Weight    → ML
Sleep     → Rule
Workout   → Rule
```

または、

```text
ML見送り / Fallback

Recommendation
      ↓
Rule-based
```

MLを採用する場合でも、Rule-based RecommendationをFallbackとして保持する。

---

# 22. 将来拡張

V1.0完成後の拡張候補として以下を想定する。

* より高度なMLモデル
* 個人最適化
* 推薦精度向上
* モデル再学習
* Model Monitoring
* AIによる高度な健康分析
* より高度なレシピ最適化
* 外部健康データとの連携
* モバイル対応
* API化
* 複数AI Provider対応

ただし、これらはV1.0の必須要件には含めない。

---

# 23. 設計上の重要原則

本プロジェクトでは以下を基本原則とする。

1. **データを正しく蓄積することを最優先する**
2. **Deterministicな処理とAI/MLを分離する**
3. **Rule-based RecommendationをBaselineとして維持する**
4. **AI Providerを抽象化する**
5. **MLは実装・評価し、性能に基づいて採用判断する**
6. **MLを採用する場合でもFallbackを用意する**
7. **ユーザーデータを`user_id`によって明確に分離する**
8. **DomainとInfrastructureを分離する**
9. **テスト可能な設計を優先する**
10. **CIを常にGreenに維持する**
