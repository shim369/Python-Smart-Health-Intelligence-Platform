"""Alembicマイグレーションの適用・ロールバックを検証するIntegration Test。

実際のPostgreSQL接続を必要とする。DATABASE_URLが未設定の場合は
自動的にスキップする(tests/integration/test_user_isolation.py と同様)。

`alembic upgrade head` → `alembic downgrade base` の往復が
エラー無く完了することを確認する(Migration Test)。
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    DATABASE_URL is None,
    reason="DATABASE_URL が未設定のためMigration Testをスキップ",
)


def _run_alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_upgrade_and_downgrade_round_trip() -> None:
    upgrade_result = _run_alembic("upgrade", "head")
    assert upgrade_result.returncode == 0, upgrade_result.stderr

    downgrade_result = _run_alembic("downgrade", "base")
    assert downgrade_result.returncode == 0, downgrade_result.stderr

    # 後続のテストに影響しないよう、スキーマを再度head状態へ戻しておく
    _run_alembic("upgrade", "head")
