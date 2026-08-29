"""Alembic実行環境の設定。

DATABASE_URLは環境変数から取得する(alembic.iniには書かない)。
`Base.metadata`(database/schema.py)をtarget_metadataとして渡すことで
`alembic revision --autogenerate` が使えるようにする。
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# src/ をimportパスに追加(alembic.iniのprepend_sys_pathでも設定済みだが、
# 直接 `alembic` コマンドを別ディレクトリから叩く場合の保険として明示する)
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from health_intelligence.config import load_environment  # noqa: E402
from health_intelligence.database.schema import Base  # noqa: E402

load_environment()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "環境変数 DATABASE_URL が設定されていません。 Migrationを実行する前に設定してください。"
        )
    return url


def run_migrations_offline() -> None:
    """`--sql` オプション等、DBに接続せずSQLを生成するモード。"""
    context.configure(
        url=_get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """実際にDBへ接続してMigrationを適用するモード(通常はこちら)。"""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
