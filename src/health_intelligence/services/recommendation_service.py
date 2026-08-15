"""RecommendationService。"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from health_intelligence.repositories.unit_of_work import UnitOfWork


class RecommendationService:
    """Recommendationに関するユースケースを担当するService。

    Rule-based Recommendationおよび(採用判断後の)ML Recommendationは
    Feature Engineering(Phase 3)・Analysis(Phase 3)・ML Pipeline
    (Phase 8)に依存するため、現時点では未実装。

    Interfaceの形(メソッドシグネチャ)のみをここで確定し、
    実装は該当Phaseで行う。
    """

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def get_recommendations(self, user_id: UUID) -> list[str]:
        """ユーザーへの改善提案一覧を返す。

        戻り値の型(Recommendation Domain Model)はPhase 3の
        Analysis Architecture確定時に見直す。現状は仮にstr(提案文)の
        リストとしている。
        """
        raise NotImplementedError("Phase 3以降で実装する")
