"""Repository/UnitOfWorkの具体実装(SQLAlchemy)。

`repositories.protocols`および`repositories.unit_of_work`で定義した
Protocolを満たす。Service層はこのモジュールを直接importせず、
Protocol経由で扱うことでDB実装への直接依存を避ける
(依存はapp/側の組み立てコードでのみ発生する想定)。
"""

from health_intelligence.repositories.sqlalchemy.factory import build_uow_factory
from health_intelligence.repositories.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

__all__ = ["SqlAlchemyUnitOfWork", "build_uow_factory"]
