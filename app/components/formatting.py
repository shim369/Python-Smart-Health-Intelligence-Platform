"""表示用のフォーマットヘルパー。"""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type
from datetime import time as time_type

from health_intelligence.local_time import APP_TIMEZONE as _JST
from health_intelligence.local_time import local_today


def format_datetime_jst(dt: datetime) -> str:
    """aware datetime(DB保存値は一貫してUTC)を日本時間の文字列に変換する。

    DomainModel/DBはタイムゾーン付きUTCで統一する方針
    (database/schema.pyのDateTime(timezone=True)参照)のため、
    表示直前のこの関数でのみJSTへ変換する
    (タイムゾーン変換はPresentation Layerの責務)。
    """
    return dt.astimezone(_JST).strftime("%Y-%m-%d %H:%M")


def format_date_jst(dt: datetime) -> str:
    """aware datetimeを日本時間の日付(時刻無し)文字列に変換する。"""
    return dt.astimezone(_JST).strftime("%Y-%m-%d")


def combine_jst_to_utc(date_value: date_type, time_value: time_type) -> datetime:
    """日本時間で入力された日付・時刻を、保存用のUTC awareへ変換する。

    フォーム入力(`format_datetime_jst`の逆方向)。
    """
    local_dt = datetime.combine(date_value, time_value, tzinfo=_JST)
    return local_dt.astimezone(UTC)


def jst_date_of(dt: datetime) -> date_type:
    """aware datetimeを日本時間での日付(date型)に変換する。

    編集フォームの`st.date_input`初期値として使う。
    """
    return dt.astimezone(_JST).date()


def jst_time_of(dt: datetime) -> time_type:
    """aware datetimeを日本時間での時刻(time型)に変換する。

    編集フォームの`st.time_input`初期値として使う。
    """
    return dt.astimezone(_JST).time()


def jst_today() -> date_type:
    """日本時間での今日の日付。`st.date_input`の初期値として使う。

    `date.today()`は実行環境(Streamlit Community CloudはUTC)の
    タイムゾーンに依存し、JST 0:00〜8:59の間は前日になってしまう。
    """
    return local_today()


def jst_now_time() -> time_type:
    """日本時間での現在時刻(秒以下切り捨て)。`st.time_input`の初期値として使う。

    `datetime.now().time()`は実行環境のタイムゾーン(UTC)の時刻になり、
    `combine_jst_to_utc`でJSTとして解釈されると9時間ずれて保存される。
    """
    return jst_time_of(datetime.now(UTC)).replace(second=0, microsecond=0)
