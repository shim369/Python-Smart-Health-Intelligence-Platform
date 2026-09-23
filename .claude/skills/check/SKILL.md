---
name: check
description: Run this project's full quality gate (ruff lint, ruff format, mypy, i18n duplicate-key check, unit tests against a safe dummy DB). Use after code changes and before committing, instead of running pytest directly — plain pytest can wipe the production Neon DB.
---

# /check

Run the bundled script from the repository root:

```bash
.claude/skills/check/check.sh
```

It runs, in order, and reports every failure (it does not stop at the first):

1. `ruff check app src tests`
2. `ruff format --check app src tests`
3. `mypy src`
4. Duplicate keys in `TRANSLATIONS` (`app/i18n.py`)
5. `pytest tests/unit` with `DATABASE_URL` pointed at an unreachable localhost and `tests/unit/test_migrations.py` excluded

## Rules

- Never run `pytest` directly against the default environment. Without `.env.test`, `tests/unit/test_migrations.py` drops and recreates every table in the `.env` production DB, and `tests/integration/` writes to it. A PreToolUse hook (`.claude/hooks/guard_pytest_db.py`) blocks such runs.
- If ruff format fails, fix with `.venv/bin/ruff format app src tests` and re-run.
- Report the final `ALL PASSED` / `FAILED: ...` line to the user; on failure include the failing step's output.
