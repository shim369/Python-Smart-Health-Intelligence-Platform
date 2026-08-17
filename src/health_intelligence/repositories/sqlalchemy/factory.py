"""`Callable[[], UnitOfWork]` を組み立てる便利関数。

Serviceの`__init__(self, uow_factory: Callable[[], UnitOfWork])`に
そのまま渡せる形のfactoryを提供する。
"""

from __future__ import annotations

from collections.abc import Callable

from health_intelligence.repositories.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)


def build_uow_factory() -> Callable[[], SqlAlchemyUnitOfWork]:
    """DATABASE_URLに基づくUnitOfWork factoryを組み立てる。

    呼び出しごとに`database.connection.get_session_factory()`から
    取得したsession_factoryを束ねた`SqlAlchemyUnitOfWork`インスタンスを
    生成する関数を返す。
    """
    from health_intelligence.database.connection import get_session_factory

    session_factory = get_session_factory()
    return lambda: SqlAlchemyUnitOfWork(session_factory)
