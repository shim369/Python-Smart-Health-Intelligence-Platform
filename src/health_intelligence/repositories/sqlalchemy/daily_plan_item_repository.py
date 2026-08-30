"""SqlAlchemyによる`DailyPlanItemRepository`実装。"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from health_intelligence.database.schema import DailyPlanItemORM
from health_intelligence.domain.models import DailyPlanItem


def _to_domain(orm: DailyPlanItemORM) -> DailyPlanItem:
    return DailyPlanItem(
        daily_plan_item_id=orm.id,
        user_id=orm.user_id,
        journal_date=orm.journal_date,
        task_id=orm.task_id,
    )


class SqlAlchemyDailyPlanItemRepository:
    """`repositories.protocols.DailyPlanItemRepository` を満たす実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_date(self, user_id: UUID, journal_date: date) -> list[DailyPlanItem]:
        stmt = select(DailyPlanItemORM).where(
            DailyPlanItemORM.user_id == user_id, DailyPlanItemORM.journal_date == journal_date
        )
        return [_to_domain(orm) for orm in self._session.scalars(stmt)]

    def replace_for_date(self, user_id: UUID, journal_date: date, task_ids: list[UUID]) -> None:
        self._session.execute(
            delete(DailyPlanItemORM).where(
                DailyPlanItemORM.user_id == user_id,
                DailyPlanItemORM.journal_date == journal_date,
            )
        )
        self._session.add_all(
            DailyPlanItemORM(
                id=uuid4(), user_id=user_id, journal_date=journal_date, task_id=task_id
            )
            for task_id in task_ids
        )
