#!/usr/bin/env bash
# lint / format / 型 / i18n / ユニットテストを一括で実行する。
# テストは本番DB(.envのNeon)に触れないよう、DATABASE_URLを到達不能な
# localhostへ差し替え、DBを破壊するtest_migrations.pyを除外して実行する
# (.env.testがある場合はconftest.pyがそちらで上書きする)。
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

SAFE_DB_URL="postgresql+psycopg://safe:safe@127.0.0.1:1/unreachable"
failed=()

step() {
  local name="$1"
  shift
  echo "== ${name}"
  if "$@"; then echo "   OK"; else echo "   FAILED"; failed+=("$name"); fi
}

check_i18n() {
  .venv/bin/python - <<'PY'
import collections
import re
import sys

keys = re.findall(r'^    "(.+?)":', open("app/i18n.py", encoding="utf-8").read(), re.M)
dups = [k for k, n in collections.Counter(keys).items() if n > 1]
if dups:
    print("   duplicate TRANSLATIONS keys:", dups)
    sys.exit(1)
PY
}

step "ruff check" .venv/bin/ruff check app src tests
step "ruff format" .venv/bin/ruff format --check app src tests
step "mypy" .venv/bin/mypy src
step "i18n duplicate keys" check_i18n
step "pytest (unit, safe DB)" env DATABASE_URL="$SAFE_DB_URL" \
  .venv/bin/pytest tests/unit --ignore=tests/unit/test_migrations.py -q -p no:cacheprovider

echo
if ((${#failed[@]})); then
  echo "FAILED: ${failed[*]}"
  exit 1
fi
echo "ALL PASSED"
