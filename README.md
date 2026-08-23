# Python Smart Health Intelligence Platform

健康データ(食事・運動・睡眠・体重・体調)を記録し、Feature Engineering・ルールベース分析・AIレシピ生成・機械学習による予測を組み合わせて健康管理を支援するWebアプリケーション。

詳細な設計は以下を参照。

- [docs/requirements.md](docs/requirements.md) — 要件定義書
- [docs/architecture.md](docs/architecture.md) — アーキテクチャ設計書
- [docs/database.md](docs/database.md) — ER図・データベース設計

## 主な機能

- 食事・運動(セッション/種目/セット構造)・睡眠・体重・体調の記録
- 記録から算出するHealth Score(独自指標、医療診断目的ではない)
- Rule-basedによる改善提案(Recommendation Engine)
- Gemini APIによるAIレシピ生成(食材入力 → レシピ提案、生成結果はキャッシュ)
- Email/PasswordによるマルチユーザーWebアプリ(ユーザーごとにデータを分離)
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

### 3. データベースの準備

```bash
uv run alembic upgrade head
```

### 4. アプリの起動

```bash
uv run streamlit run app/streamlit_app.py
```

## テスト

```bash
# Unit Test(外部サービス不要)
uv run pytest tests/unit

# Integration Test(要DATABASE_URL。未設定の場合は自動的にスキップされる)
uv run pytest tests/integration

# 全体(Lint / Format / 型チェック / テスト)
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

CI(GitHub Actions)はPushごとに上記一式を実行する。Integration TestはCI上でPostgresサービスコンテナを使って実行される([.github/workflows/ci.yml](.github/workflows/ci.yml))。

## ML Pipeline

体重変化予測モデルの評価・学習は以下で実行する。

```bash
uv run python -m health_intelligence.ml.run_weight_pipeline
```

評価結果は`mlruns/`(MLflow)に記録され、採用判断は`ml_artifacts/weight_model_decision.json`に保存される。アプリ本体(`RecommendationService`)はこの判断を読み取り、採用基準(Baseline比で改善率10%以上、過学習チェック20%以内、最低60日分のデータ)を満たしていればAI予測を表示し、満たしていなければRule-basedの提案のみを表示する。判断基準の詳細は[docs/requirements.md](docs/requirements.md)の9.3.1を参照。

## デプロイ(Streamlit Community Cloud + Neon を想定)

1. [Neon](https://neon.tech/)でPostgreSQLプロジェクトを作成し、接続文字列を取得する
2. ローカルから本番用DBに対して`uv run alembic upgrade head`を実行し、スキーマを適用する
3. [Streamlit Community Cloud](https://streamlit.io/cloud)でアプリをデプロイし、アプリの設定画面から Secrets に`.env.example`と同じキーで値を設定する(`st.secrets`経由で環境変数として読み込まれる)
4. デプロイ後、アプリのURLにアクセスして新規登録から動作確認する

## 既知の制限事項

開発を圧縮スケジュールで進めた都合上、以下は意図的に簡易な実装のままにしてある。

- **Recipe Cache**: プロセスメモリ上の実装。アプリ再起動やStreamlit Community Cloudのスリープ復帰で消える([ai/recipe_cache.py](src/health_intelligence/ai/recipe_cache.py))
- **セッショントークン**: ブラウザ更新後もログイン状態を復元するため、トークンをURLクエリパラメータに載せている。ブラウザ履歴等に残るリスクがあるため、より厳密にするならhttponly Cookieへの置き換えを検討([auth/session_token_store.py](src/health_intelligence/auth/session_token_store.py))
- **HealthLogのフィールド構成**: 汎用的な体調記録の受け皿として暫定的に`condition_score`/`symptoms`/`memo`のみ。実運用しながら見直す前提
- **ML Pipeline**: 実データが60日分・欠損率30%未満に達するまでは、Rule-basedのみで動作する(意図した挙動)。対象領域は現状Weightのみ(Nutrition/Sleep/Workoutへの横展開は未着手)
- **運動記録フォーム**: 同じ種目名・カテゴリの入力行をまとめて1種目・複数セットとして保存する設計のため、同じ種目を1日に複数回(例: 午前と夕方で2回)行った場合を区別できない

## プロジェクト構成

```text
├── app/                    Streamlit UI(ページ・コンポーネント・DI)
├── src/health_intelligence/
│   ├── domain/              Domain Model(dataclass)
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
│   ├── unit/                 外部サービス不要のテスト
│   └── integration/          要DATABASE_URL(CI/ローカルDBで実行)
└── docs/                     要件定義・アーキテクチャ・DB設計
```

## ライセンス

[MIT License](LICENSE)
