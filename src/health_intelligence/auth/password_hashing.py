"""パスワードハッシュ化。

外部ライブラリ(bcrypt等)を追加せず、標準ライブラリのみで実装する。
`hashlib.pbkdf2_hmac`による繰り返しハッシュ化 + ランダムsaltを用いる。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ALGORITHM = "sha256"
_ITERATIONS = 600_000
"""PBKDF2-HMAC-SHA256の反復回数。OWASPの目安を参考にした値。"""
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """パスワードをsalt付きでハッシュ化する。

    `{algorithm}${iterations}${salt_hex}${hash_hex}` 形式の文字列を
    返す。この文字列1つだけでverify_passwordによる検証が完結する。
    """
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """`hash_password`が生成した文字列に対してパスワードを検証する。

    不正な形式のpassword_hashが渡された場合はFalseを返す
    (例外を送出しない)。
    """
    try:
        algorithm, iterations_str, salt_hex, hash_hex = password_hash.split("$")
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False

    derived = hashlib.pbkdf2_hmac(algorithm, password.encode("utf-8"), salt, iterations)
    # タイミング攻撃を避けるため定数時間比較を使う。
    return hmac.compare_digest(derived, expected)
