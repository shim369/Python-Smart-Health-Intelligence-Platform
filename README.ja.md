# Python Smart Health Intelligence Platform

[English](README.md) | **日本語**

健康データ(食事・運動・睡眠・体重・体調)、学習・PF開発・仕事の記録(長期目標/タスク単位)、家計の入口を1日単位のPDCA(P/D/C/A)形式で記録し、Feature Engineering・ルールベース分析・AIレシピ生成・機械学習による予測を組み合わせて健康管理を支援するWebアプリケーション。

詳細な設計は以下を参照。

- [docs/requirements.md](docs/requirements.md) — 要件定義書(ER図・データベース設計は14.1節)
- [docs/architecture.md](docs/architecture.md) — アーキテクチャ設計書

## 主な機能

- 「今日」ページ: 1日分の記録をP(計画)→D(実績)→C(振り返り)→A(改善)のPDCA形式で1画面完結。睡眠・体調(5軸)・食事・運動(セッション/種目/セット構造)・学習/PF開発/仕事・家計(買い物メモ/食費)をここで記録する
- 長期目標(Goal)・タスク(Task)管理: 長期目標ごとにタスクを紐づけ、「今日」ページのPで日々選択、進捗を集計。学習/PF開発/仕事は数量・時間・メモを記録し、食事方針/運動目標/睡眠目標は選ぶだけで実績は既存ドメイン(MealLog/WorkoutLog/SleepLog)に記録される
- 学習ログ(試験勉強・PF開発・調べ物・キャリア/プロダクト戦略設計、カテゴリごとに入力項目が切り替わる)。「今日」ページのD(実績)タブで記録
- Dashboardページで睡眠・体調・食事・学習/作業時間・運動(筋トレ種目別の最大重量の推移、種目別の有酸素運動時間)・食費をグラフ表示(表示期間は直近7日/30日/90日から選択。既定は7日)
- Gemini APIによるAIレシピ生成(食材入力 → レシピ提案、生成結果はキャッシュ)。生成したレシピの材料は「今日」ページの買い物メモへワンタップで追記可能。レシピ履歴は開閉式のアコーディオンで一覧し、削除も可能
- 食べたものの自由記述からAIがカロリー・PFCを推定(食事記録の入力補助)
- 「前回と同じ内容」「よく使うテンプレート/キーワード」によるクイック入力、CSVファイルからのログ一括インポート(登録済みと内容が同一の行は二重取り込み防止のため自動でスキップ)
- 日本語/英語の表示切り替え(i18n、ユーザーごとにDB永続化)。新規ユーザーの初期表示言語はブラウザの`Accept-Language`から判定する(ログイン画面自体は常に英語表示)
- Google OAuth(OIDC、`st.login()`)によるマルチユーザーWebアプリ(ユーザーごとにデータを分離)
- Health Score(独自指標、医療診断目的ではない)とRule-basedによる改善提案(Recommendation Engine)をバックエンドに実装済み(現在のUIには非表示。[既知の制限事項](#既知の制限事項)参照)
- LightGBMによる体重変化予測のML Pipeline(Rule-based Baseline比較、採用基準を満たした場合のみ有効化。未達時はRule-basedにFallback)

## 技術スタック

- Python 3.13、[uv](https://docs.astral.sh/uv/)
- Streamlit(UI)
- PostgreSQL([Neon](https://neon.tech/)等) + SQLAlchemy + Alembic
- Google Gemini API(`google-genai`)
- LightGBM + MLflow(ML Pipeline)
- pytest + Ruff + mypy + GitHub Actions(CI)

アーキテクチャ全体はレイヤードアーキテクチャ(Presentation → Service → Domain ← Repository → Infrastructure)。詳細は[docs/architecture.md](docs/architecture.md)を参照。

## セットアップ

### 1. 依存関係のインストール

```bash
uv sync
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env`を編集し、以下を設定する。

| 変数 | 説明 |
|---|---|
| `DATABASE_URL` | PostgreSQL接続文字列(`postgresql+psycopg://...`形式)。Neon等のホスティングサービスを利用する場合、接続文字列のスキーム部分を`postgresql+psycopg://`に読み替える |
| `GEMINI_API_KEY` | Gemini APIキー |
| `AI_PROVIDER` | `gemini`(既定)または`fake`。`fake`を指定するとAPIキー無しで[`FakeAIProvider`](src/health_intelligence/ai/fake_provider.py)を使って動作確認できる |
| `LOG_LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR`。未設定時は`INFO` |

### 2.5. Google OAuthの設定

ログインにはGoogle OAuth(OIDC)を使う(`st.login()`)。
[Google Cloud Console](https://console.cloud.google.com/apis/credentials)で
以下を行う。

1. OAuth同意画面を設定する
2. 認証情報 → OAuthクライアントID(ウェブアプリケーション)を作成する
3. 承認済みリダイレクトURIを登録する(ローカル: `http://localhost:8501/oauth2callback`)

その後、`.streamlit/secrets.toml`に設定する(`.env`ではなくStreamlitの
Secrets機構を使う点に注意)。

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

```toml
# .streamlit/secrets.toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "ランダムな文字列"
client_id = "xxxxx.apps.googleusercontent.com"
client_secret = "xxxxx"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# 任意。設定しなければ誰でもログイン可能。
allowed_emails = "your-email@gmail.com,friend@gmail.com"
```

### 3. データベースの準備

```bash
uv run alembic upgrade head
```

### 3.5. (推奨) テスト用DBの分離

`tests/unit/test_migrations.py`は`DATABASE_URL`に対して実際に
`alembic downgrade base`(全テーブルdrop)→`upgrade head`を行い、
`tests/integration/`もDATABASE_URLへ実データを書き込む。`.env`に
日常使っているDBを設定していると、`pytest`(全体)を実行するたびに
そのDBが空にリセットされ、登録したユーザー等が消えてしまう。

これを避けるには、使い捨てて構わない別のDB(Neonの別ブランチ・別
プロジェクト、ローカルPostgres等)を用意し、`.env.test`に設定する。

```bash
cp .env.test.example .env.test
```

`.env.test`が存在すると、`tests/conftest.py`が起動時に`DATABASE_URL`
をこちらで上書きするため、`pytest`が日常用DBに触れなくなる
(`.env.test`が無ければ従来通り`.env`のDATABASE_URLがテストにも
使われる。CI等はこの既定動作を利用する)。

Claude Codeで開発する場合は、`.claude/settings.json`のPreToolUse hook
([.claude/hooks/guard_pytest_db.py](.claude/hooks/guard_pytest_db.py))が、
`.env.test`が無い状態でのpytest実行を(`DATABASE_URL`をlocalhostへ
上書きしている場合を除き)ブロックする。

### 4. アプリの起動

```bash
uv run streamlit run app/streamlit_app.py
```

## テスト

```bash
# Lint / Format / 型チェック / i18nの重複キー / Unit Testを一括実行
# (DATABASE_URLを到達不能なlocalhostへ差し替え、DBを破壊する
#  test_migrations.pyを除外して実行するため、.env.test無しでも安全)
.claude/skills/check/check.sh

# Migration Test・Integration Testを含む全体(要.env.test。3.5節参照)
uv run pytest
```

`tests/unit/`にもDBを使う`test_migrations.py`が含まれるため、`.env.test`が
無い状態で`uv run pytest tests/unit`を実行すると`.env`のDBが初期化される。
ローカルでは上の`check.sh`(Claude Codeでは`/check`スキル)を使う。

本番DBの状態(ログ件数・内容が同一の重複レコード・最終記録日など)は、
読み取り専用で点検できる(Claude Codeでは`/db-health`スキル)。

```bash
uv run python .claude/skills/db-health/db_health.py
```

CI(GitHub Actions)はPush・Pull Requestごとに上記一式を実行する。CIでは使い捨てのPostgreSQL 16サービスコンテナを起動して`DATABASE_URL`をそこへ向け、`pytest`の前に`alembic upgrade head`を実行するため、Migration Test・Integration Testも含めて実行される([.github/workflows/ci.yml](.github/workflows/ci.yml))。

## ML Pipeline

体重変化予測モデルの評価・学習は以下で実行する。

```bash
uv run python -m health_intelligence.ml.run_weight_pipeline
```

スクリプトはまずDBに蓄積された実データの状況(Weight領域: 60日分以上・欠損率30%未満)を確認する。

- **基準を満たす場合**: 実データでPipelineを評価し、結果を`mlruns/`(MLflow)に記録、採用判断を`ml_artifacts/weight_model_decision.json`に保存する
- **基準を満たさない場合**: 60日到達の見込み日を表示し、ダミーデータでPipelineの配線確認のみを行う。ダミーデータの評価結果はMLflowには記録する(run名`weight_change_model_dummy_wiring_check`)が、採用判断としては**保存しない**

このスクリプトは定期ワークフロー([.github/workflows/ml-weight-readiness.yml](.github/workflows/ml-weight-readiness.yml))により毎週月曜06:00 JSTに(手動実行も可)、リポジトリSecretの`DATABASE_URL`に対して実行され、出力はJob Summaryに書き出される。

`RecommendationService`はこの判断を読み取り、採用基準(Baseline比で改善率10%以上、過学習チェック20%以内、最低60日分のデータ)を満たしていればAI予測を表示し、満たしていなければRule-basedの提案のみを表示する。判断基準の詳細は[docs/requirements.md](docs/requirements.md)の9.3.1を参照。

## デプロイ(Streamlit Community Cloud + Neon を想定)

1. [Neon](https://neon.tech/)でPostgreSQLプロジェクトを作成し、接続文字列を取得する
2. ローカルから本番用DBに対して`uv run alembic upgrade head`を実行し、スキーマを適用する
3. [Streamlit Community Cloud](https://streamlit.io/cloud)でアプリをデプロイし、アプリの設定画面から Secrets に`.env.example`のキー(DB接続等)に加え、[2.5節](#25-google-oauthの設定)の`[auth]`セクション(`redirect_uri`は本番URLの`https://<app-name>.streamlit.app/oauth2callback`に置き換える)を設定する
4. Google Cloud Console側で、承認済みリダイレクトURIに本番の`redirect_uri`を追加登録する
5. デプロイ後、アプリのURLにアクセスしてGoogleログインから動作確認する

## 既知の制限事項

開発を圧縮スケジュールで進めた都合上、以下は意図的に簡易な実装のままにしてある。

- **Health Score / Recommendation Engine**: `RecommendationService`としてバックエンドには実装済みだが、Dashboardを週間グラフ中心の構成へ変更した際にUI表示を外しており、現在どのページからも呼び出されていない
- **Recipe Cache**: プロセスメモリ上の実装。アプリ再起動やStreamlit Community Cloudのスリープ復帰で消える([ai/recipe_cache.py](src/health_intelligence/ai/recipe_cache.py))
- **読み取りキャッシュ**: リモートDB(Neon)の往復待ちを減らすため、各Serviceの読み取り結果をプロセス内で最大10分キャッシュする([app/services.py](app/services.py))。アプリ経由の書き込みでは即座に破棄されるが、SQL等でDBを直接変更した場合は、アプリを再起動するまで(最長10分)画面に反映されない
- **HealthLogのフィールド構成**: 汎用的な体調記録の受け皿として、総合スコア(`condition_score`)・体調5軸(朝/夜/メンタル/疲労/ストレス)・`symptoms`・`memo`を持つ。実運用しながら見直しを重ねてきた経緯があり、今後もフィールド構成が変わる前提
- **ML Pipeline**: 実データが60日分・欠損率30%未満に達するまでは、Rule-basedのみで動作する(意図した挙動)。対象領域は現状Weightのみ(Nutrition/Sleep/Workoutへの横展開は未着手)
- **運動記録フォーム**: 同じ種目名・カテゴリの入力行をまとめて1種目・複数セットとして保存する設計のため、同じ種目を1日に複数回(例: 午前と夕方で2回)行った場合を区別できない

## プロジェクト構成

```text
├── app/                    Streamlit UI(ページ・コンポーネント・DI・i18n)
├── src/health_intelligence/
│   ├── domain/              Domain Model(dataclass。Goal/Task/DailyJournal含む)
│   ├── repositories/        Repository Interface + SQLAlchemy実装
│   ├── services/            Service Layer(ユースケース)
│   ├── ai/                  AI Provider(Gemini/Fake)・Retry方針
│   ├── auth/                認証・Session State
│   ├── features/            Feature Engineering(純粋関数)
│   ├── analysis/            Analyzer・Health Score
│   ├── recommendation/      Rule-based Recommendation Engine
│   ├── ml/                  ML Pipeline(Dataset/評価/LightGBM/MLflow)
│   └── database/            SQLAlchemy ORM・Alembic Migration
├── tests/
│   ├── unit/                 Unit Test(test_migrations.pyのみ要DATABASE_URL)
│   └── integration/          要DATABASE_URL(CI/ローカルDBで実行)
├── .claude/                  Claude Code用のhook(pytestのDB保護)・スキル(/check, /db-health)
└── docs/                     要件定義・アーキテクチャ・DB設計
```

## ライセンス

[MIT License](LICENSE)
