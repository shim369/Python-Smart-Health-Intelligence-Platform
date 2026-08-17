"""PostgreSQL接続設定。

architecture.md Section 7.3: Database接続情報は環境変数
(ローカル: .env、本番: Streamlit Secrets)から取得し、DATABASE_URLを
ソースコードへ直接記述しない。

architecture.md Section 7.1: 特定のクラウドPostgreSQLサービス
(Neon等)に直接依存しない。標準のPostgreSQL接続文字列であれば
どのホスティングサービスでも動作する。
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "環境変数 DATABASE_URL が設定されていません。"
            " ローカルでは.env、本番ではStreamlit Secretsで設定してください。"
        )
    return url


def get_engine() -> Engine:
    """SQLAlchemy Engineをシングルトンとして取得する。

    `pool_pre_ping=True` により、Neonのscale-to-zero(自動スリープ)
    復帰直後の切断済みコネクションを自動的に検知して再接続する。
    """
    global _engine
    if _engine is None:
        _engine = create_engine(_database_url(), pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    """デバッグ・簡易スクリプト用に1つのSessionを払い出すcontext manager。

    アプリケーション本体は`repositories.sqlalchemy.unit_of_work`の
    `SqlAlchemyUnitOfWork`を経由してSessionを扱う想定で、
    ここは主に単発のスクリプトやテストからの利用を想定する。
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
