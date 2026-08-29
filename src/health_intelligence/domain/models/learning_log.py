"""LearningLog Domain Model。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from health_intelligence.domain.enums import LearningCategory, LearningLocation


@dataclass(frozen=True, kw_only=True, slots=True)
class LearningLog:
    """試験勉強・PF開発・調べ物・キャリア戦略設計の学習記録を表すDomain Model。

    WorkoutExerciseのcardio/strengthと同様に、`category`によって
    意味を持つフィールドが変わる(試験勉強はcontent/breakdown、
    キャリア戦略設計はnotesを使う等)。全フィールドを同時に埋める
    必要はない。
    """

    learning_log_id: UUID
    user_id: UUID
    started_at: datetime
    category: LearningCategory
    location: LearningLocation | None = None
    content: str | None = None
    """勉強内容 / PF開発内容。試験勉強・PF開発カテゴリで使用する。"""
    breakdown: list[str] = field(default_factory=list)
    """内訳・章立て等(例: "Chapter3", "Chapter5")。試験勉強カテゴリで使用する。"""
    duration_minutes: int | None = None
    """勉強時間/開発時間/h。カテゴリ共通のフィールドとして扱う。"""
    keywords: list[str] = field(default_factory=list)
    """技術的成長キーワード。"""
    notes: list[str] = field(default_factory=list)
    """箇条書きメモ。キャリア・プロダクト戦略設計カテゴリで使用する。"""
