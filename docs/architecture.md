# Smart Health Intelligence Platform
# Architecture Design

## 1. Overview

本ドキュメントは、`Python-Smart-Health-Intelligence-Platform` のシステムアーキテクチャ、責務分離、データフロー、永続化、AI/ML連携、認証、マルチユーザー設計に関する基本方針を定義する。

本システムは、ユーザーの健康データを継続的に蓄積し、Feature Engineering、Analysis、Recommendation、AI、MLを段階的に組み合わせる健康管理プラットフォームである。ルールベースおよびAI/MLを利用して健康改善提案やレシピ生成を行うWebアプリケーションを目指す。

基本的な処理フロー：

```text
Health Data
    ↓
Persistence
    ↓
Feature Engineering
    ↓
Analysis
    ↓
Health Score
    ↓
Rule-based Recommendation
    ↓
AI / ML
    ↓
Recommendation
```

---

## 2. System Goals

本システムの主な目的は以下とする。

- 健康データを継続的に記録できる
- 食事・運動・睡眠・体重などを統合的に管理できる
- 記録データから特徴量を生成できる
- 健康状態を分析・スコアリングできる
- ルールベースで改善提案を生成できる
- Gemini等のAIを利用してレシピを生成できる
- 将来的にMLによる予測・推薦を導入できる
- 複数ユーザーが安全に利用できる
- PostgreSQLを利用してデータを永続化できる
- Streamlit Community Cloud上で公開可能な構成とする
- テスト・Lint・型チェックを自動化する

---

## 3. Technology Stack

### 3.1 Application

- Python 3.13+
- Streamlit
- Pydantic

### 3.2 Database

- PostgreSQL
- SQLAlchemy
- Alembic
- psycopg3

PostgreSQLのホスティングサービスはPhase 2で決定する。

候補：Neon / Supabase / Render / その他の無料または低コストPostgreSQLサービス

### 3.3 AI

- Google Gemini API
- `google-genai`
- Pydantic Structured Output

### 3.4 ML

- LightGBM
- MLflow
- pandas
- scikit-learn 等

MLライブラリの最終構成はPhase 8で決定する。

### 3.5 Development

- uv
- Ruff
- mypy
- pytest / pytest-cov
- GitHub Actions

---

## 4. Architecture Principles

以下を基本設計方針とする。

1. DomainとInfrastructureを分離する
2. Service層にユースケースおよびアプリケーションレベルのビジネスロジックを集約する
3. Repository Patternによって永続化処理を抽象化する
4. 外部サービスへの依存をInterface / Protocolによって抽象化する
5. ユーザー所有データを`user_id`によって分離する
6. Session Stateを永続データの保存場所として利用しない
7. Rule-based RecommendationをBaselineとして維持する
8. MLはRule-based Baselineとの比較によって採用判断する
9. MLを採用する場合でもRule-basedをFallbackとして保持する
10. PostgreSQLの具体的なクラウドサービスにアプリケーション層を直接依存させない
11. 複数Repositoryにまたがる更新処理はUnit of Workによって1トランザクションとして管理する
12. Domain ModelとDatabase ORM Modelを分離する
13. Database固有の情報をDomain Modelへ漏洩させない
14. ML Pipelineはまず1領域で確立し、その後必要に応じて他領域へ横展開する

---

## 5. High-Level Architecture

```text
┌───────────────────────────────────────────┐
│               Streamlit UI                 │
│                                             │
│ Dashboard / Logs / Recipe / Authentication │
└─────────────────────┬───────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────┐
│              Service Layer                 │
│                                             │
│ Health / Meal / Workout / Sleep / Recipe   │
│ Recommendation / Authentication            │
└──────────────┬──────────────┬───────────────┘
               │              │
               ▼              ▼
┌─────────────────────┐  ┌─────────────────────┐
│    Domain Layer      │  │   AI / ML Layer      │
│                       │  │                       │
│ Domain Models         │  │ Gemini Provider       │
│ Business Rules        │  │ FakeAIProvider        │
│                       │  │ ML Pipeline           │
└──────────┬────────────┘  └───────────┬───────────┘
           │                            │
           ▼                            ▼
┌───────────────────────────────────────────┐
│        Repository / Unit of Work           │
│                                             │
│ Repository Pattern                          │
│ Transaction Management (UoW)                │
└─────────────────────┬───────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────┐
│                PostgreSQL                   │
│                                             │
│ Users / Health Logs / Meals / Recipes etc   │
└───────────────────────────────────────────┘
```

Domain LayerとAI/ML Layerはいずれも永続化が必要な場合、Repository / Unit of Workを経由してPostgreSQLへアクセスする。AI/ML Layer自体はDomain Modelを利用してデータをやり取りし、SQLAlchemyやPostgreSQLへ直接依存しない。

---

## 6. Layer Responsibilities

### 6.1 Presentation Layer

対象：

```text
app/
├── streamlit_app.py
├── pages/
└── components/
```

責務：ユーザーインターフェース、ユーザー入力の受付、Service呼び出し、結果の表示、Streamlit Session State管理。

基本的な依存関係：

```text
UI → Service
```

`UI → Repository` のような直接依存は原則として避ける。

### 6.2 Service Layer

想定Service：

```text
services/
├── user_service.py
├── health_service.py
├── meal_service.py
├── workout_service.py
├── sleep_service.py
├── weight_service.py
├── recommendation_service.py
└── recipe_service.py
```

責務：Domain Modelの操作、Repositoryの呼び出し、複数Repositoryを跨ぐ処理、Transaction境界の調整、Recommendation処理、AI Providerの呼び出し、Feature / Analysisの実行。

Serviceは具体的なPostgreSQL実装へ直接依存しない。

### 6.3 Domain Layer

対象：`src/health_intelligence/domain/`

主なDomain Model：

```text
User / HealthLog / MealLog / WorkoutLog / SleepLog
WeightLog / Ingredient / Recipe / RecipeIngredient
```

データベース固有の仕様やStreamlit固有の処理を持たせない。

### 6.4 Pydanticとdataclassの使い分け

**dataclass** — Domain Model、Feature、Analysis Result、Recommendation Result、内部処理用データ構造。Domainを外部ライブラリから独立させ、内部モデルと外部入力を分離するため。

**Pydantic** — API Input/Output、AI Structured Output、RecipeInput、Configuration、外部入力Validation、AI Response Validation。

基本境界：

```text
External Input → Pydantic → Domain dataclass → Service
```

### 6.5 Repository Layer

対象：

```text
repositories/
├── user_repository.py
├── health_log_repository.py
├── meal_log_repository.py
├── workout_log_repository.py
├── sleep_log_repository.py
├── weight_log_repository.py
├── ingredient_repository.py
└── recipe_repository.py
```

責務：CRUD、Query、Persistence、Database Exceptionの適切な変換、Unit of Workが提供するSessionの利用。

Repositoryはビジネスルールを持たない。「条件付きでMealLogを取得する」はRepositoryの責務、「Proteinが不足しているので改善提案を生成する」はService / Analysis / Recommendationの責務。

---

## 7. Database Architecture

### 7.1 Database / ORM / Migration

- PostgreSQL(特定クラウドサービスに直接依存しない。候補: Neon / Supabase 等。Phase 2で比較・決定)
- SQLAlchemyを利用。Domain ModelとORM Modelは分離する
- MigrationはAlembicを利用し、GitでMigrationファイルを管理する

### 7.2 Cloud Architecture

```text
User Browser → Streamlit Community Cloud → Application → External PostgreSQL
```

永続データはStreamlit Community Cloudのローカルファイルシステムではなく、外部PostgreSQLへ保存する。

### 7.3 Database Connection / Environment Configuration

Database接続情報は環境変数またはStreamlit Secretsから取得する(ローカル: `.env`、本番: Streamlit Secrets)。`DATABASE_URL` をソースコードへ直接記述しない。

秘密情報(`DATABASE_URL`、`GEMINI_API_KEY` 等)はGit Repositoryへコミットしない。

---

## 8. user_id Architecture

### 8.1 基本方針

ユーザー所有データ(`HealthLog` / `MealLog` / `WorkoutLog` / `SleepLog` / `WeightLog` / `Recipe`)には原則として`user_id`を必須とする。

```text
User
 ├── HealthLog
 ├── MealLog
 ├── WorkoutLog
 ├── SleepLog
 ├── WeightLog
 └── Recipe
```

### 8.2 共通データ

`Ingredient` 等のシステム共通データは原則として`user_id`を持たない。

### 8.3 Repository Boundary

`get_meal_logs(user_id)` のようにユーザーコンテキストを明示し、ユーザーAからユーザーBのデータへアクセスできない構造を基本とする。

### 8.4 user_id Exception Rules

内部処理・バッチ処理などユーザーコンテキストを必要としない処理では`user_id`を使用しない場合があるが、その場合はSystem Contextとして明示する。ユーザー所有データを処理するBatchでは、原則として対象ユーザーを明示する。**「user_idがない場合は全ユーザーを対象とする」という暗黙的な仕様は採用しない。**

---

## 9. Session State Architecture

主な状態：`authenticated` / `user_id`(必要に応じてUI状態等を保持)。Session Stateを永続データ保存場所として利用しない。

```text
Session State → user_id → Service → Repository → PostgreSQL
```

### 9.1 Session Lifecycle

```text
Application Start → Session Initialization → Authentication
→ Authenticated User → user_id → Application Usage
→ Logout → Session State Reset
```

Logout時には、認証情報およびユーザー固有のSession Stateを適切にリセットする。

---

## 10. AI Architecture

AIサービスはProvider Patternによって抽象化する。

```text
AIProvider (Protocol)
    ↑
    ├── GeminiProvider
    └── FakeAIProvider
```

Service Layerは具体的なGemini APIに直接依存しない。

### 10.1 FakeAIProvider

API Key不要のテスト、APIコスト削減、API障害時のテスト、Deterministicなテスト、CIでのAI処理テストを目的とする。

### 10.2 AI Error Handling

Timeout / 429 Rate Limit / 503 Service Unavailable / Validation Error / その他API Errorを想定。429・503はRetry対象とし、指数バックオフを利用する。Timeoutを設定し無期限に待機しない。Validation ErrorはSchema Validationで検出する。

---

## 11. Recommendation & ML Architecture

### 11.1 Recommendation Architecture

```text
Features → Analysis → Recommendation Engine
                        ├── Rule-based
                        └── ML
```

Rule-based Recommendationは初期Recommendation Engineとして実装し、同時にML評価時のBaseline、MLが利用できない場合のFallbackとしても利用する。

### 11.2 ML Architecture

```text
Health Data → Dataset → Data Quality Check → Feature Dataset
→ Baseline → LightGBM → Training → Evaluation → Prediction → MLflow
```

### 11.3 ML Pipeline Development Strategy

全領域(Nutrition / Weight / Sleep / Workout)を同時に完成させるのではなく、まず1領域でPipeline全体を確立する。

```text
1領域を選択 → Dataset → Feature Dataset → Rule-based Baseline
→ LightGBM → Training → Evaluation → MLflow Tracking
→ 採用判断 → 他領域へ横展開
```

対象領域はPhase 8開始時点で、データ量・欠損率・Featureの品質・目的変数の定義可能性・予測可能性・Rule-based Baselineの性能・ML導入によるメリットを評価して決定する。

### 11.4 MLflow

Parameters / Metrics / Model / Experiment / Evaluation Resultsを記録し、実験の再現性・モデル比較・Baseline比較・採用判断に利用する。

### 11.5 ML Recommendation Strategy

- **ML採用**: MLがRule-based Baselineを十分に上回る場合
- **ML限定採用**: 領域ごとにMLの採否を判断(例: Nutrition→ML、Sleep→Rule)。すべての領域でMLを採用する必要はない
- **ML見送り**: MLがBaselineを上回らない場合はRule-basedを継続利用。ML Pipeline自体は構築・評価するが、製品Recommendationへの統合は見送ることができる

### 11.6 ML Fallback

MLを製品Recommendationへ統合する場合でも、Rule-based RecommendationをFallbackとして保持する。

Fallback条件：MLモデルが利用できない / ML推論エラー / 性能が基準未達 / データ不足 / モデル更新中 / 特定領域ではML非採用。

```text
Recommendation → ML Strategy
                   ├── OK → ML
                   └── NG → Rule-based
```

---

## 12. Feature Engineering / Analysis / Health Score

### 12.1 Feature Engineering

```text
features/
├── daily_features.py
├── weekly_features.py
├── nutrition_features.py
├── weight_features.py
├── sleep_features.py
└── workout_features.py
```

可能な限り副作用を持たない純粋な処理として実装し、Unit TestおよびML Dataset生成で再利用可能とする。

### 12.2 Analysis

```text
Features → [Weight / Nutrition / Sleep / Workout Analyzer] → Analysis Result → Health Score
```

Analyzerは可能な限り決定論的に実装する。

### 12.3 Health Score

Nutrition/Weight/Sleep/Workout各Scoreを統合してHealth Scoreとする。医療診断を目的とせず、本システム独自の健康管理支援指標として扱う。

---

## 13. Recipe Architecture

```text
Recipe Service → Recipe Input → Prompt Builder → AIProvider
→ Structured Output → Pydantic Validation → Recipe Domain Model
→ Recipe Repository → PostgreSQL
```

生成済みRecipeはCacheを利用し、不要なAI API呼び出しを抑制する。Recipe作成時など複数Repositoryにまたがる更新では、Unit of Workによって1つのトランザクションとして扱う。

---

## 14. Domain / ORM Separation & Mapping

Domain ModelとDatabase ORM Modelは同一モデルを必須とせず分離する。

```text
Domain Model ↕ Mapping ↕ SQLAlchemy ORM Model
```

`Mapped` / `mapped_column` / `ForeignKey` / Index / Database Constraint / Relationship / Cascade / Database-specific type / Persistence metadataはORM側の責務とし、Domain側では直接扱わない。

初期実装では明示的な変換関数(`to_domain` / `to_orm`)による単純なMappingを基本とする。共通Mapperインターフェースの導入は、実装時の重複量と可読性を確認したうえで判断する。**過度な抽象化は初期段階では避ける。**

---

## 15. Unit of Work / Transaction Architecture

複数Repositoryにまたがる更新処理では、1つのSQLAlchemy Sessionを共有し、1つのトランザクションとして扱う。

```text
Service → Unit of Work
            ├── Repository A
            ├── Repository B
            └── Repository C
              → SQLAlchemy Session → PostgreSQL
```

基本フロー：`Service → UoW begin → Repository operations → 成功時commit / 失敗時rollback`

Repositoryは原則として独自にSessionを生成・commit・rollbackしない。Transactionの基本的な責務はService / Unit of Work側に置く。

例：Recipe作成時、RecipeRepositoryとRecipeIngredientRepositoryは単一Sessionを共有し、片方の保存に失敗した場合は全体をRollbackすることで部分的更新を防止する。

具体的なUnit of Work実装方式、Sessionライフサイクル、RepositoryへのSession注入方式はPhase 2で確定する。

---

## 16. Dependency Direction

```text
Presentation → Service → Domain ← Repository → Infrastructure
```

より具体的には、`Service → Repository Interface ← Repository Implementation → SQLAlchemy → PostgreSQL`。ServiceからRepositoryの抽象へ依存し、具体的なDatabase実装への依存を分離する。

---

## 17. External Service Dependencies

PostgreSQL Provider / Gemini API / Streamlit Community Cloud / MLflow。これらの具体的な実装・接続情報をDomainへ持ち込まない。

---

## 18. Testing Architecture

```text
Domain      → Unit Test
Service     → Unit Test
Repository  → Repository Test
AI Provider → FakeAIProvider Test
Database    → Integration Test
Application → E2E Test
```

重要なテスト対象：user_id分離、Repository境界、Transaction境界、Unit of Work、Rollback、AI Retry/Timeout/Validation、ML / Rule-based切り替え、Fallback、Authentication、Session State。

---

## 19. Configuration & Logging

環境固有設定(`DATABASE_URL`、`GEMINI_API_KEY` 等)をコードへハードコードせず、環境変数等から取得する。

Application全体で適切なLoggingおよびException Handlingを実装する。対象：Database Error / Transaction Error / Validation Error / Authentication Error / AI API Error / Timeout / Rate Limit / ML Prediction Error。内部エラー情報とユーザー向けエラーメッセージは適切に分離する。

---

## 20. ディレクトリ構成

```text
Python-Smart-Health-Intelligence-Platform/
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── src/
│   └── health_intelligence/
│       ├── __init__.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── user.py
│       │   │   ├── health_log.py
│       │   │   ├── meal_log.py
│       │   │   ├── workout_log.py
│       │   │   ├── sleep_log.py
│       │   │   ├── weight_log.py
│       │   │   ├── ingredient.py
│       │   │   ├── recipe.py
│       │   │   └── recipe_ingredient.py
│       │   └── enums.py
│       ├── repositories/
│       │   ├── user_repository.py
│       │   ├── health_log_repository.py
│       │   ├── meal_log_repository.py
│       │   ├── workout_log_repository.py
│       │   ├── sleep_log_repository.py
│       │   ├── weight_log_repository.py
│       │   ├── ingredient_repository.py
│       │   └── recipe_repository.py
│       ├── database/
│       │   ├── connection.py
│       │   ├── schema.py
│       │   └── migrations/
│       ├── features/
│       ├── analysis/
│       ├── recommendation/
│       ├── recipe/
│       ├── ai/
│       ├── auth/
│       ├── ml/
│       └── config.py
│
├── app/
│   ├── streamlit_app.py
│   ├── pages/
│   └── components/
│
├── tests/
├── data/
├── docs/
│   ├── architecture.md
│   ├── requirements.md
│   ├── database.md
│   ├── authentication.md
│   ├── recipe-generation.md
│   └── ml-pipeline.md
│
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── uv.lock
└── LICENSE
```

ディレクトリ構成は実装フェーズで責務に応じて調整する。

---

## 21. アーキテクチャ上の重要な設計原則

1. Domainは外部サービスから独立させる
2. UIからRepositoryへ直接アクセスしない
3. Serviceにユースケースを集約する
4. Repositoryにビジネスロジックを持たせない
5. Domain ModelとORM Modelを分離する
6. Pydanticは外部境界、dataclassはDomain / 内部処理を基本とする
7. `user_id`をユーザーデータのアクセス境界とする
8. Session Stateに永続データを保存しない
9. AI Providerを抽象化する
10. FakeAIProviderによってAI処理をテスト可能にする
11. Rule-based RecommendationをBaselineとして維持する
12. ML Pipelineを構築・評価する
13. ML採用は評価結果に基づいて決定する
14. ML採用時もRule-based Fallbackを保持する
15. ML Pipelineはまず1領域で確立する
16. PostgreSQL Providerへの依存をInfrastructureに閉じ込める
17. Secretsをソースコードへ保存しない
18. CIで品質を継続的に検証する
19. 複数Repositoryにまたがる更新はUnit of Workで管理する
20. Repositoryが独自にcommit / rollbackを行わない
21. Database固有の情報をDomain Modelへ漏洩させない
22. DomainとORM間の変換責務を明確にする
23. 過度な抽象化を避け、必要になった段階で共通化する

---

## 22. 今後の設計課題(優先順位付き)

### 22.1 Phase 1中に確定させるべきもの

Phase 1(8/14〜8/17)の期間内に骨格レベルまで決めておくべき項目。ここが曖昧なままだとPhase 2以降の実装で手戻りが発生しやすい。

- Domain Modelの詳細設計(フィールド、型、Value Objectの導入判断)
- Domain Model間の関連設計
- Service Interfaceの骨格、ユースケース単位の設計方針
- Repository Interfaceの骨格
- Unit of Workの具体実装方式の方向性(Sessionライフサイクル、RepositoryへのSession注入方式の大枠)
- Domain Model ↔ ORM ModelのMapping方式(関数ベースで進める、という方針の確定)
- AIProvider Protocolの詳細(メソッドシグネチャ、Structured Outputのスキーマ形状)
- Retry / Timeoutの具体値
- Streamlit Session State Key設計
- ML採用判断基準(Baselineをどの程度上回れば採用するか等)

### 22.2 Phase 2以降で確定すればよいもの

実装を進めながら、または該当フェーズの直前に決定して問題ない項目。

- PostgreSQL Provider決定(Neon / Supabase 等の比較)
- ER設計、Index設計、Foreign Key、Cascade設定
- Migration運用方針
- Connection Pool、Transaction設定の詳細
- Mapper共通インターフェースの採用判断(重複量を見てから)
- 認証方式の最終決定、Cookie/ブラウザ更新/タブ共有の挙動確認
- API Cost / Rate Limitの具体的な運用ルール
- Recipe Cacheの実装方式
- ML対象領域の最終選定、Dataset設計、目的変数の定義、Evaluation指標、LightGBM設定
- MLflow Trackingの具体的なディレクトリ・命名規則
- UI/Service境界の細部、Error Handling/Loggingの実装詳細
