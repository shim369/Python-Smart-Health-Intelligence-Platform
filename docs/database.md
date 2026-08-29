# Database設計

`database/schema.py`のSQLAlchemy ORM Modelに対応するER図。GitHub上で
このファイルを開くと、以下のMermaidコードブロックがそのまま図として
表示される。

```mermaid
erDiagram
    USERS ||--|| USER_CREDENTIALS : has
    USERS ||--o{ HEALTH_LOGS : records
    USERS ||--o{ MEAL_LOGS : records
    USERS ||--o{ WORKOUT_LOGS : records
    USERS ||--o{ SLEEP_LOGS : records
    USERS ||--o{ WEIGHT_LOGS : records
    USERS ||--o{ LEARNING_LOGS : records
    USERS ||--o{ RECIPES : creates
    WORKOUT_LOGS ||--o{ WORKOUT_EXERCISES : contains
    WORKOUT_EXERCISES ||--o{ WORKOUT_SETS : contains
    RECIPES ||--o{ RECIPE_INGREDIENTS : uses
    INGREDIENTS ||--o{ RECIPE_INGREDIENTS : "used in"

    USERS {
        uuid id PK
        string email UK
        string display_name
        datetime created_at
    }
    USER_CREDENTIALS {
        uuid user_id PK_FK
        string password_hash
    }
    HEALTH_LOGS {
        uuid id PK
        uuid user_id FK
        datetime recorded_at
        int condition_score
        text symptoms
        text memo
    }
    MEAL_LOGS {
        uuid id PK
        uuid user_id FK
        datetime consumed_at
        string meal_type
        float calories
        float protein_g
        float fat_g
        float carbohydrate_g
        text memo
    }
    WORKOUT_LOGS {
        uuid id PK
        uuid user_id FK
        datetime performed_at
        float calories_burned
        text memo
    }
    WORKOUT_EXERCISES {
        uuid id PK
        uuid workout_log_id FK
        int order_index
        string exercise_name
        string category
        int duration_minutes
    }
    WORKOUT_SETS {
        uuid id PK
        uuid workout_exercise_id FK
        int order_index
        int reps
        float weight_kg
    }
    SLEEP_LOGS {
        uuid id PK
        uuid user_id FK
        datetime bedtime
        datetime wake_time
        string quality
    }
    WEIGHT_LOGS {
        uuid id PK
        uuid user_id FK
        datetime recorded_at
        float weight_kg
    }
    LEARNING_LOGS {
        uuid id PK
        uuid user_id FK
        datetime started_at
        string category
        string location
        text content
        text breakdown
        int duration_minutes
        text keywords
        text notes
    }
    INGREDIENTS {
        uuid id PK
        string name
        float calories_per_100g
        float protein_per_100g
        float fat_per_100g
        float carbohydrate_per_100g
    }
    RECIPES {
        uuid id PK
        uuid user_id FK
        string title
        text instructions
        string source
        datetime created_at
        float total_calories
        float protein_g
        float fat_g
        float carbohydrate_g
    }
    RECIPE_INGREDIENTS {
        uuid recipe_id PK_FK
        uuid ingredient_id PK_FK
        float amount
        string unit
    }
```

## 設計上のポイント

- **`user_id`境界**: `INGREDIENTS`以外の全テーブルが`user_id`を持つ(requirements.md 13章)。`INGREDIENTS`はシステム共通の食材マスタのため`user_id`を持たない。
- **`USER_CREDENTIALS`の分離**: パスワードハッシュは`USERS`テーブルに含めず、1対1の別テーブルに分離している(Domain Model設計の方針に合わせたもの。auth/authenticator.py参照)。
- **`WORKOUT_LOGS`の3階層構造**: 1回の運動セッション(`WORKOUT_LOGS`)は複数の種目(`WORKOUT_EXERCISES`)を持ち、筋力トレーニングの種目はさらに複数セット(`WORKOUT_SETS`)を持つ。有酸素運動は`WORKOUT_EXERCISES.duration_minutes`のみを使い、`WORKOUT_SETS`は持たない。
- **`LEARNING_LOGS`のカテゴリ依存フィールド**: `category`(試験勉強/PF開発/調べ物/キャリア・プロダクト戦略設計)によって使用するフィールドが異なる(例: 試験勉強は`content`/`breakdown`、キャリア戦略設計は`notes`を使う)。`WORKOUT_LOGS`と同様、全フィールドを同時に埋める必要はない。
- **`RECIPE_INGREDIENTS`は多対多の中間テーブル**: `RECIPES`と`INGREDIENTS`の間の分量情報(`amount`/`unit`)を保持する。
- **`RECIPES`の栄養情報**: `total_calories`/`protein_g`/`fat_g`/`carbohydrate_g`はAI生成時のみ推定・保存されるnullableな列で、手動登録のレシピでは`NULL`のままとなる。

## Migration

スキーマの変更履歴は`database/migrations/versions/`配下のAlembicリビジョンで管理する。初期スキーマは`0001_initial.py`。以降、`recipes`への栄養情報列追加(`0003`)、`learning_logs`テーブル追加(`0004`)などをリビジョンとして積み重ねている。最新リビジョンは`uv run alembic history`で確認できる。

```bash
# 最新スキーマを適用
uv run alembic upgrade head

# 1つ前のリビジョンへ戻す
uv run alembic downgrade -1
```
