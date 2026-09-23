---
name: db-health
description: Read-only health check of the production Neon DB — per-user log counts, content-duplicate records (e.g. double CSV imports), latest record date per log type, and orphaned workout exercises/sets. Use when dashboard charts look empty, inflated, or wrong, or after bulk CSV imports.
---

# /db-health

Run from the repository root:

```bash
.venv/bin/python .claude/skills/db-health/db_health.py
```

The script connects with `postgresql_readonly` (Postgres rejects any write with `ReadOnlySqlTransaction`), so it is safe to run against production. It takes a few seconds because the DB is remote.

## Reading the output

- **重複**: records whose content matches another record exactly (all fields except the ID). Same rule as the CSV import dedupe (`content_key` in `app/components/csv_import.py`). Non-zero usually means a CSV was imported more than once, which multiplies dashboard totals.
- **最終記録日**: if it is more than 7 days ago, the dashboard's default "last 7 days" view is empty for that log type. That is expected, not a bug.
- **Orphans**: workout exercises or sets with no parent row.

## Fixing problems

This skill only diagnoses. Deleting duplicates is destructive and irreversible, so:

1. Show the user the counts and ask for explicit confirmation first.
2. Dry-run, then delete through the repositories (`uow.<logs>.delete(user_id, id)`, keeping one record per `content_key`) in a single transaction, so workout exercises and sets cascade and a failure rolls everything back.
3. Re-run `/db-health` to confirm, and tell the user to restart Streamlit: the app caches reads for up to 10 minutes and does not see changes made outside the app.
