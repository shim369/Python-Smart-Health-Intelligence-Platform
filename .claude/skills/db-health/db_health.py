"""本番DB(.envのDATABASE_URL)の健全性を読み取り専用で点検する。

- ログ種別ごとの件数・重複件数(内容が完全一致するレコード。CSVインポートの
  二重取り込み判定 `content_key` と同じ基準)・最終記録日(JST)
- 運動ログの子テーブル(種目・セット)の孤児行

接続は `postgresql_readonly` を指定したトランザクションで行うため、
このスクリプトからDBへ書き込むことはできない。

使い方(リポジトリ直下から):
    .venv/bin/python .claude/skills/db-health/db_health.py
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "app"))

from components.csv_import import content_key  # noqa: E402
from components.formatting import jst_date_of  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from health_intelligence.config import load_environment  # noqa: E402
from health_intelligence.repositories.sqlalchemy.unit_of_work import (  # noqa: E402
    SqlAlchemyUnitOfWork,
)

# (UoWの属性名, 表示名, 記録日時の属性名)
_LOGS = [
    ("meal_logs", "食事", "consumed_at"),
    ("workout_logs", "運動", "performed_at"),
    ("sleep_logs", "睡眠", "bedtime"),
    ("weight_logs", "体重", "recorded_at"),
    ("health_logs", "体調", "recorded_at"),
    ("learning_logs", "学習", "started_at"),
]
_STALE_DAYS = 7
_ORPHAN_QUERIES = {
    "workout_exercises(親の運動ログなし)": (
        "select count(*) from workout_exercises e"
        " where not exists (select 1 from workout_logs w where w.id = e.workout_log_id)"
    ),
    "workout_sets(親の種目なし)": (
        "select count(*) from workout_sets s"
        " where not exists (select 1 from workout_exercises e where e.id = s.workout_exercise_id)"
    ),
}


def main() -> int:
    load_environment()
    engine = create_engine(
        os.environ["DATABASE_URL"],
        pool_pre_ping=True,
        execution_options={"postgresql_readonly": True},
    )
    today = jst_date_of(datetime.now(UTC))
    problems: list[str] = []

    with SqlAlchemyUnitOfWork(sessionmaker(bind=engine)) as uow:
        session = uow._session
        assert session is not None
        users = session.execute(text("select id, email from users order by email")).all()

        for user_id, email in users:
            print(f"# {email}")
            print(f"  {'種別':<4} {'件数':>6} {'重複':>6} {'最終記録日(JST)':>16}")
            for attr, label, at_field in _LOGS:
                logs = getattr(uow, attr).list_by_user(user_id)
                counts = Counter(content_key(log) for log in logs)
                duplicates = sum(n - 1 for n in counts.values())
                latest = max((jst_date_of(getattr(log, at_field)) for log in logs), default=None)
                latest_text = latest.isoformat() if latest else "-"
                print(f"  {label:<4} {len(logs):>6} {duplicates:>6} {latest_text:>16}")

                if duplicates:
                    problems.append(f"{email} {label}: 内容が同一の重複 {duplicates}件")
                if latest is not None and (today - latest).days > _STALE_DAYS:
                    problems.append(
                        f"{email} {label}: 最終記録が{(today - latest).days}日前"
                        f"({latest.isoformat()}) → ダッシュボードの直近{_STALE_DAYS}日間は空"
                    )
            print()

        for label, sql in _ORPHAN_QUERIES.items():
            orphans = session.execute(text(sql)).scalar_one()
            if orphans:
                problems.append(f"{label}: {orphans}行")

    print("## 検出事項")
    for problem in problems or ["なし"]:
        print(f"- {problem}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
