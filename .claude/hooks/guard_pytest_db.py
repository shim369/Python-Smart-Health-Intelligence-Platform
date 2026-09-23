#!/usr/bin/env python3
"""PreToolUse(Bash) hook: 本番DBを巻き込むpytest実行をブロックする。

tests/unit/test_migrations.py は全テーブルを drop/再作成し、
tests/integration/ は実データを書き込む。`.env.test`(テスト専用DB)が
無い状態でpytestを走らせると、`.env`の日常用DB(Neon)がそのまま使われ、
データが消える(過去に実際に起きかけた事故)。

次のいずれかを満たす場合のみpytestの実行を許可する:
- プロジェクト直下に `.env.test` がある(conftest.pyがテスト用DBへ上書きする)
- コマンド内で DATABASE_URL を localhost / 127.0.0.1 へ上書きしている
  (/check スキルはこの形で実行する)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# pytestを「コマンドとして」起動している箇所だけを検出する
# (`grep pytest pyproject.toml` のような引数中の出現は対象外)。
_PYTEST_INVOCATION = re.compile(
    r"(?:^|[;&|(\n]|\bthen\b|\bdo\b)\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
    r"(?:env\s+(?:(?:-u|--unset)\s+\S+\s+|-\S+\s+)*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*)?"
    r"(?:(?:uv|poetry)\s+run\s+)?"
    r"(?:\S*/)?(?:pytest|py\.test|python3?(?:\.\d+)?\s+-m\s+pytest)\b"
)
_SAFE_DB_OVERRIDE = re.compile(r"DATABASE_URL=\S*@(?:127\.0\.0\.1|localhost)[:/]")


def main() -> int:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    if not _PYTEST_INVOCATION.search(command):
        return 0

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
    if (project_dir / ".env.test").exists() or _SAFE_DB_OVERRIDE.search(command):
        return 0

    print(
        "Blocked: .env.test が無い状態で pytest を実行すると、.env の本番DB(Neon)に対して"
        " test_migrations.py が全テーブルを drop/再作成します。\n"
        "代わりに /check スキル(.claude/skills/check/check.sh)を使うか、"
        "DATABASE_URL=postgresql+psycopg://safe:safe@127.0.0.1:1/unreachable を"
        "コマンドの先頭に付けて実行してください。",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
