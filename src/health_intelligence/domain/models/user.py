"""User Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from health_intelligence.domain.enums import Locale


@dataclass(frozen=True, kw_only=True, slots=True)
class User:
    """システムを利用するユーザーを表すDomain Model。

    パスワードハッシュ等の認証情報はDomain Modelに含めない。
    認証の詳細はPhase 4A(認証PoC)/Phase 7(認証統合)で別途設計する。
    """

    user_id: UUID
    email: str
    display_name: str
    created_at: datetime
    locale: Locale = Locale.JA
    """UIの表示言語。app/i18n.pyのt()が参照する。"""
