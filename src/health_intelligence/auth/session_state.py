"""認証状態を扱うSession Stateのラッパー。

architecture.md Section 9 / 9.1 Session Lifecycle:
Session Stateには`authenticated`/`user_id`等、必要最小限の状態のみ
保持し、永続データの保存場所として利用しない。

```text
Application Start
      ↓
Session Initialization  → initialize()
      ↓
Authentication
      ↓
Authenticated User      → login(user_id)
      ↓
Application Usage       → require_user_id() でガード
      ↓
Logout                  → logout()
      ↓
Session State Reset
```

Streamlitの`st.session_state`に直接依存させず、`MutableMapping`を
受け取る設計にすることで、Streamlit未起動でもUnit Testできるようにする
(requirements.md 16章 Session State Test)。
"""

from __future__ import annotations

from collections.abc import MutableMapping
from uuid import UUID

from health_intelligence.auth.session_keys import SessionKey
from health_intelligence.domain.enums import Locale


class AuthSessionState:
    """認証状態を`SessionKey`経由で読み書きするラッパー。

    使用例(Streamlit側):

    ```python
    import streamlit as st

    auth_state = AuthSessionState(st.session_state)
    auth_state.initialize()
    ```
    """

    def __init__(self, state: MutableMapping[str, object]) -> None:
        self._state = state

    def initialize(self) -> None:
        """未初期化のキーに初期値を設定する。

        Application Start直後、Login前に呼び出す想定。既に値が
        入っている場合(再実行等)は上書きしない。
        """
        self._state.setdefault(SessionKey.AUTHENTICATED, False)
        self._state.setdefault(SessionKey.USER_ID, None)
        self._state.setdefault(SessionKey.LOCALE, Locale.JA)

    @property
    def is_authenticated(self) -> bool:
        return bool(self._state.get(SessionKey.AUTHENTICATED, False))

    @property
    def user_id(self) -> UUID | None:
        value = self._state.get(SessionKey.USER_ID)
        return value if isinstance(value, UUID) else None

    @property
    def locale(self) -> Locale:
        """現在の表示言語。`app.i18n.t()`がここを参照して翻訳を切り替える。"""
        value = self._state.get(SessionKey.LOCALE)
        return value if isinstance(value, Locale) else Locale.JA

    def login(self, user_id: UUID, locale: Locale = Locale.JA) -> None:
        """認証成功時にSession Stateへユーザーを紐付ける。

        `locale`はUser.localeをそのまま渡す想定(DBに保存された
        言語設定を、DB往復せずに毎リクエスト参照できるようにする)。
        """
        self._state[SessionKey.AUTHENTICATED] = True
        self._state[SessionKey.USER_ID] = user_id
        self._state[SessionKey.LOCALE] = locale

    def set_locale(self, locale: Locale) -> None:
        """言語切り替えUIから呼ばれる、Session State側のみの即時反映。

        DBへの永続化(UserService.update_locale)は呼び出し側の責務とする。
        """
        self._state[SessionKey.LOCALE] = locale

    def logout(self) -> None:
        """ログアウト時にユーザー固有のSession Stateをリセットする。

        architecture.md Section 9.1: Logout時には、認証情報および
        ユーザー固有のSession Stateを適切にリセットする。
        `authenticated`/`user_id`以外のUI状態キーがPhase 6以降で
        追加された場合も、ここで同様にリセットする想定。
        """
        self._state[SessionKey.AUTHENTICATED] = False
        self._state[SessionKey.USER_ID] = None
        self._state[SessionKey.LOCALE] = Locale.JA

    def require_user_id(self) -> UUID:
        """認証済みであることを前提にuser_idを取得する。

        Presentation Layer(app/pages等)からService呼び出し前の
        ガードとして利用する想定。未認証状態で呼び出された場合は
        RuntimeErrorとする。
        """
        if not self.is_authenticated or self.user_id is None:
            raise RuntimeError("認証されていません")
        return self.user_id
