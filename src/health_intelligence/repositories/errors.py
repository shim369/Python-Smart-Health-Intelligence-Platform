"""Repository層で使用する例外。"""


class DuplicateKeyError(Exception):
    """永続化時に一意制約違反が発生したことを表す。"""
