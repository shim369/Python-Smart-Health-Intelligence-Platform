# Python Smart Health Intelligence Platform

**English** | [日本語](README.ja.md)

A web application that records health data (meals, workouts, sleep, weight, condition), study/portfolio-development/work logs (tracked per long-term goal/task), and a shopping memo, all in a daily PDCA (Plan/Do/Check/Act) format, and supports health management by combining Feature Engineering, rule-based analysis, AI recipe generation, and machine-learning prediction.

See below for the detailed design (documents are in Japanese).

- [docs/requirements.md](docs/requirements.md) — Requirements definition (ER diagram / database design in section 14.1)
- [docs/architecture.md](docs/architecture.md) — Architecture design

## Key features

- **"Today" page**: Complete one day's record in a single screen, in PDCA order — Plan → Do → Check → Act. Sleep, condition (5 axes), meals, workouts (session/exercise/set structure), study/PF-dev/work, and a shopping memo are all recorded here.
- **Goal & Task management**: Attach tasks to long-term goals, select them daily in the "Today" page's Plan step, and track progress. Study/PF-dev/work tasks record quantity/duration/memo; diet-policy/exercise-goal/sleep-goal tasks are just selected, with the actual record still living in the existing domains (MealLog/WorkoutLog/SleepLog).
- **Learning log** (exam study, portfolio development, research, career/product strategy — the input fields change per category). Recorded in the "Today" page's Do tab.
- **Dashboard** showing sleep/condition, meals, study/work time, workouts (max weight per strength exercise over time, cardio time by exercise) as charts, stacked one per row rather than side by side, with a selectable period (last 7 / 30 / 90 days; defaults to 7).
- **AI recipe generation** via the Gemini API (enter ingredients → get a recipe suggestion, results are cached). Past recipes are listed as collapsible accordions and can be deleted. Ingredients from a generated recipe can be appended to the "Today" page's shopping memo with one tap.
- AI estimates calories/PFC from a free-text description of what you ate (assists meal logging).
- Quick entry via "same as last time" / frequently-used templates & keywords, plus bulk log import from CSV files (rows identical to an existing log are skipped automatically to prevent double imports).
- **i18n**: switch the UI between Japanese and English (persisted per user in the DB). A new user's initial language is detected from the browser's `Accept-Language`; the login screen itself is always shown in English.
- Multi-user web app with Google OAuth (OIDC, via `st.login()`) login (data isolated per user).
- **Health Score** (a proprietary metric, not intended for medical diagnosis) and rule-based improvement suggestions (Recommendation Engine) are implemented on the backend (currently hidden from the UI — see [Known limitations](#known-limitations)).
- ML pipeline for weight-change prediction using LightGBM (compared against a rule-based baseline; only enabled once it meets the adoption criteria, otherwise falls back to rule-based).

## Tech stack

- Python 3.13, [uv](https://docs.astral.sh/uv/)
- Streamlit (UI)
- PostgreSQL ([Neon](https://neon.tech/), etc.) + SQLAlchemy + Alembic
- Google Gemini API (`google-genai`)
- LightGBM + MLflow (ML pipeline)
- pytest + Ruff + mypy + GitHub Actions (CI)

The overall architecture is layered (Presentation → Service → Domain ← Repository → Infrastructure). See [docs/architecture.md](docs/architecture.md) for details.

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set the following.

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+psycopg://...` form). If using a hosting service such as Neon, rewrite the scheme part of the connection string to `postgresql+psycopg://` |
| `GEMINI_API_KEY` | Gemini API key |
| `AI_PROVIDER` | `gemini` (default) or `fake`. With `fake`, you can verify behavior without an API key, using [`FakeAIProvider`](src/health_intelligence/ai/fake_provider.py) |
| `LOG_LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR`. Defaults to `INFO` if unset |

### 2.5. Configure Google OAuth

Login uses Google OAuth (OIDC) via `st.login()`. In
[Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Configure the OAuth consent screen.
2. Under Credentials, create an OAuth client ID (Web application).
3. Register an authorized redirect URI: `http://localhost:8501/oauth2callback`
   for local development.

Then configure the client in `.streamlit/secrets.toml` (note: this uses
Streamlit's Secrets mechanism, not `.env`).

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

```toml
# .streamlit/secrets.toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "a random string"
client_id = "xxxxx.apps.googleusercontent.com"
client_secret = "xxxxx"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# Optional. If unset, anyone can log in.
allowed_emails = "your-email@gmail.com,friend@gmail.com"
```

### 3. Prepare the database

```bash
uv run alembic upgrade head
```

### 3.5. (Recommended) Isolate a test database

`tests/unit/test_migrations.py` actually runs `alembic downgrade base`
(dropping every table) → `upgrade head` against `DATABASE_URL`, and
`tests/integration/` also writes real data to `DATABASE_URL`. If your
`.env` points at the database you use day to day, running the full
`pytest` suite will reset that database every time, wiping out any
registered users and other data.

To avoid this, provision a separate, disposable database (a different
Neon branch/project, a local Postgres, etc.) and configure it in
`.env.test`.

```bash
cp .env.test.example .env.test
```

If `.env.test` exists, `tests/conftest.py` overrides `DATABASE_URL`
with it at startup, so `pytest` never touches your everyday database
(if `.env.test` is absent, the `DATABASE_URL` from `.env` is used for
tests as before — CI relies on this default behavior).

When developing with Claude Code, a PreToolUse hook in
`.claude/settings.json` ([.claude/hooks/guard_pytest_db.py](.claude/hooks/guard_pytest_db.py))
blocks pytest runs while `.env.test` is absent, unless the command
overrides `DATABASE_URL` to localhost.

### 4. Run the app

```bash
uv run streamlit run app/streamlit_app.py
```

## Testing

```bash
# Lint / format / type check / i18n duplicate keys / unit tests in one go
# (points DATABASE_URL at an unreachable localhost and excludes the
#  DB-destroying test_migrations.py, so it is safe without .env.test)
.claude/skills/check/check.sh

# Everything, including migration and integration tests (requires .env.test; see 3.5)
uv run pytest
```

`tests/unit/` also contains `test_migrations.py`, which uses the database,
so running `uv run pytest tests/unit` without `.env.test` resets the DB in
`.env`. Locally, use `check.sh` above (the `/check` skill in Claude Code).

The production database can be inspected read-only (log counts,
content-duplicate records, latest record date, etc.; the `/db-health`
skill in Claude Code):

```bash
uv run python .claude/skills/db-health/db_health.py
```

CI (GitHub Actions) runs the full suite above on every push and pull request. CI starts a disposable PostgreSQL 16 service container, points `DATABASE_URL` at it, and runs `alembic upgrade head` before `pytest`, so migration tests and integration tests run there too ([.github/workflows/ci.yml](.github/workflows/ci.yml)).

## ML pipeline

Evaluate and train the weight-change prediction model with:

```bash
uv run python -m health_intelligence.ml.run_weight_pipeline
```

The script first checks how much real data has accumulated in the database (Weight domain: at least 60 days with under 30% missing-value rate).

- **Criteria met**: the pipeline is evaluated on real data; the result is logged to `mlruns/` (MLflow) and the adoption decision is saved to `ml_artifacts/weight_model_decision.json`.
- **Criteria not met**: it prints the estimated date on which 60 days will be reached, then runs the pipeline on dummy data only as a wiring check. The dummy-data result is logged to MLflow (run name `weight_change_model_dummy_wiring_check`) but is **not** saved as an adoption decision.

A scheduled workflow ([.github/workflows/ml-weight-readiness.yml](.github/workflows/ml-weight-readiness.yml)) runs this script every Monday at 06:00 JST (also runnable manually) against the `DATABASE_URL` repository secret and writes the output to the job summary. `RecommendationService` reads this decision: if the adoption criteria are met (≥10% relative improvement over baseline, overfitting check within 20%, at least 60 days of data), it shows the AI prediction; otherwise it shows only rule-based suggestions. See section 9.3.1 of [docs/requirements.md](docs/requirements.md) for the full adoption criteria.

## Deployment (assumes Streamlit Community Cloud + Neon)

1. Create a PostgreSQL project on [Neon](https://neon.tech/) and get the connection string.
2. Run `uv run alembic upgrade head` locally against the production database to apply the schema.
3. Deploy the app on [Streamlit Community Cloud](https://streamlit.io/cloud) and, under the app's Secrets settings, set the `.env.example` keys (DB connection, etc.) plus the `[auth]` section from [section 2.5](#25-configure-google-oauth) (with `redirect_uri` replaced by the production URL, `https://<app-name>.streamlit.app/oauth2callback`).
4. In Google Cloud Console, add the production `redirect_uri` to the authorized redirect URIs.
5. After deployment, visit the app's URL and verify it works by logging in with Google.

## Known limitations

Because development proceeded on a compressed schedule, the following are intentionally left as simplified implementations.

- **Health Score / Recommendation Engine**: implemented on the backend as `RecommendationService`, but its UI display was removed when the Dashboard was redesigned around weekly charts, and it is currently not called from any page.
- **Recipe Cache**: an in-process-memory implementation. It is lost on app restart or when Streamlit Community Cloud wakes from sleep ([ai/recipe_cache.py](src/health_intelligence/ai/recipe_cache.py)).
- **Read cache**: to cut round trips to the remote DB (Neon), each service's read results are cached in-process for up to 10 minutes ([app/services.py](app/services.py)). Writes made through the app invalidate it immediately, but changes made directly in the DB (e.g. via SQL) do not show up until the app restarts (up to 10 minutes).
- **HealthLog field set**: as a catch-all for general condition tracking, it holds an overall score (`condition_score`), the 5-axis condition (morning/evening/mental/fatigue/stress), `symptoms`, and `memo`. This field set has already been revised once based on real-world use, and is expected to keep evolving.
- **ML pipeline**: runs rule-based only until real data reaches 60 days with under 30% missing-value rate (intended behavior). Currently scoped to Weight only (extending to Nutrition/Sleep/Workout has not started).
- **Workout log form**: rows with the same exercise name/category are grouped and saved as one exercise with multiple sets, so performing the same exercise more than once in a day (e.g., morning and evening) cannot be distinguished.

## Project structure

```text
├── app/                    Streamlit UI (pages, components, DI, i18n)
├── src/health_intelligence/
│   ├── domain/              Domain models (dataclass; includes Goal/Task/DailyJournal)
│   ├── repositories/        Repository interfaces + SQLAlchemy implementation
│   ├── services/            Service layer (use cases)
│   ├── ai/                  AI provider (Gemini/Fake) & retry policy
│   ├── auth/                Authentication & session state
│   ├── features/             Feature engineering (pure functions)
│   ├── analysis/             Analyzers & Health Score
│   ├── recommendation/       Rule-based recommendation engine
│   ├── ml/                  ML pipeline (dataset/evaluation/LightGBM/MLflow)
│   └── database/            SQLAlchemy ORM & Alembic migrations
├── tests/
│   ├── unit/                 Unit tests (only test_migrations.py needs DATABASE_URL)
│   └── integration/          Requires DATABASE_URL (run in CI/local DB)
├── .claude/                  Claude Code hook (pytest DB guard) & skills (/check, /db-health)
└── docs/                     Requirements, architecture, DB design
```

## License

[MIT License](LICENSE)
