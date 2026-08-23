"""アプリケーション設定・依存関係の組み立て。

環境変数からUnitOfWork factory・AIProviderを構築する。Streamlit側は
`app/services.py`でこれらをさらに`st.cache_resource`によりキャッシュ
して使う。
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from health_intelligence.ai.fake_provider import FakeAIProvider
from health_intelligence.ai.gemini_provider import GeminiProvider
from health_intelligence.ai.protocols import AIProvider


def load_environment() -> None:
    """`.env`ファイルを読み込み、`os.environ`へ反映する。

    各エントリーポイント(app/streamlit_app.py、
    ml/run_weight_pipeline.py、database/migrations/env.py)の
    先頭で最初に呼び出すことを想定する。

    本番環境(Streamlit Community Cloud等)には`.env`ファイルが
    存在せず、Secretsが直接環境変数として渡されるため、
    `.env`が無い場合でもエラーにはならない
    (`load_dotenv()`は対象ファイルが無ければ何もせず戻る)。
    """
    load_dotenv()


def get_ai_provider() -> AIProvider:
    """`AI_PROVIDER`環境変数に応じてAIProviderを選択する。

    `AI_PROVIDER=fake` を指定するとFakeAIProviderを使う
    (Gemini APIキーが無い開発環境やCIでの動作確認向け)。
    未指定・それ以外の値の場合はGeminiProviderを使う。
    """
    if os.environ.get("AI_PROVIDER", "gemini").lower() == "fake":
        return FakeAIProvider()
    return GeminiProvider()
