"""SqlAlchemyによる`UnitOfWork`実装。

architecture.md Section 15: 複数Repositoryにまたがる更新処理を
1つのSQLAlchemy Sessionで束ね、commit/rollbackをここで一元管理する。
Repository側は独自にSessionをcommit/rollbackしない
(各Repositoryの実装を参照)。
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from health_intelligence.repositories.sqlalchemy.health_log_repository import (
    SqlAlchemyHealthLogRepository,
)
from health_intelligence.repositories.sqlalchemy.ingredient_repository import (
    SqlAlchemyIngredientRepository,
)
from health_intelligence.repositories.sqlalchemy.learning_log_repository import (
    SqlAlchemyLearningLogRepository,
)
from health_intelligence.repositories.sqlalchemy.meal_log_repository import (
    SqlAlchemyMealLogRepository,
)
from health_intelligence.repositories.sqlalchemy.recipe_ingredient_repository import (
    SqlAlchemyRecipeIngredientRepository,
)
from health_intelligence.repositories.sqlalchemy.recipe_repository import (
    SqlAlchemyRecipeRepository,
)
from health_intelligence.repositories.sqlalchemy.sleep_log_repository import (
    SqlAlchemySleepLogRepository,
)
from health_intelligence.repositories.sqlalchemy.user_credential_repository import (
    SqlAlchemyUserCredentialRepository,
)
from health_intelligence.repositories.sqlalchemy.user_repository import (
    SqlAlchemyUserRepository,
)
from health_intelligence.repositories.sqlalchemy.weight_log_repository import (
    SqlAlchemyWeightLogRepository,
)
from health_intelligence.repositories.sqlalchemy.workout_log_repository import (
    SqlAlchemyWorkoutLogRepository,
)


class SqlAlchemyUnitOfWork:
    """`repositories.unit_of_work.UnitOfWork` Protocolを満たす実装。"""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._committed = False

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self._committed = False

        self.users = SqlAlchemyUserRepository(self._session)
        self.user_credentials = SqlAlchemyUserCredentialRepository(self._session)
        self.health_logs = SqlAlchemyHealthLogRepository(self._session)
        self.learning_logs = SqlAlchemyLearningLogRepository(self._session)
        self.meal_logs = SqlAlchemyMealLogRepository(self._session)
        self.workout_logs = SqlAlchemyWorkoutLogRepository(self._session)
        self.sleep_logs = SqlAlchemySleepLogRepository(self._session)
        self.weight_logs = SqlAlchemyWeightLogRepository(self._session)
        self.ingredients = SqlAlchemyIngredientRepository(self._session)
        self.recipes = SqlAlchemyRecipeRepository(self._session)
        self.recipe_ingredients = SqlAlchemyRecipeIngredientRepository(self._session)

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            # 例外発生時、またはcommit()が明示的に呼ばれていない場合は
            # rollbackする(UnitOfWork Protocolの契約通り)。
            if exc_type is not None or not self._committed:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        assert self._session is not None
        self._session.commit()
        self._committed = True

    def rollback(self) -> None:
        assert self._session is not None
        self._session.rollback()
