"""アプリケーション全体のLogging設定。

architecture.md Section 19 Logging/Exception: Database Error /
Transaction Error / Validation Error / Authentication Error /
AI API Error / Timeout / Rate Limit / ML Prediction Errorを対象に、
内部エラー情報とユーザー向けエラーメッセージを適切に分離する。

標準ライブラリの`logging`のみを使用する(追加ライブラリを増やさない)。
"""

from __future__ import annotations

import logging
import os


def configure_logging(*, level: str | None = None) -> None:
    """アプリケーション全体のログ出力形式を設定する。

    環境変数`LOG_LEVEL`(未指定ならINFO)でログレベルを制御する。
    Streamlit(app/streamlit_app.py)・Alembic(database/migrations/
    env.py)・MLパイプラインスクリプト(ml/run_weight_pipeline.py)など、
    複数のエントリーポイントから共通してこの関数を呼び出す想定。
    """
    resolved_level = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # SQLAlchemyの生成SQLログは既定では抑制する。デバッグ時のみ
    # LOG_LEVEL=DEBUGに加えて明示的にこのロガーのレベルを下げること。
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """モジュール名を渡してLoggerを取得する薄いヘルパー。

    使用例: `logger = get_logger(__name__)`
    """
    return logging.getLogger(name)
