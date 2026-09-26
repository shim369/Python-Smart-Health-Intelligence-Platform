"""ユーザーの生活時間帯(日本時間)に関するヘルパー。

DomainModel/DBの日時はタイムゾーン付きUTCで統一している
(database/schema.pyのDateTime(timezone=True)参照)。一方で「何日の
記録か」はユーザーの生活時間帯(JST)で区切る必要があり、UTCのまま
`.date()`を取るとJST 0:00〜8:59の記録(朝食・起床・朝の体重測定等)が
前日扱いになる。日次集計・「今日」の判定はこのモジュールを経由する。

実行環境(Streamlit Community Cloud等)のローカルタイムゾーンはUTCの
ため、`date.today()`/`datetime.now()`(naive)は使わないこと。
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

APP_TIMEZONE = ZoneInfo("Asia/Tokyo")


def local_date_of(dt: datetime) -> date:
    """aware datetimeを日本時間での日付に変換する。"""
    return dt.astimezone(APP_TIMEZONE).date()


def local_today() -> date:
    """日本時間での今日の日付を返す(実行環境のタイムゾーンに依存しない)。"""
    return local_date_of(datetime.now(UTC))
