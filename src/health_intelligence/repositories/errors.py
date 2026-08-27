"""Repository層の例外定義。

architecture.md Section 6.5: RepositoryはDatabase Exceptionの適切な
変換を責務とする。SQLAlchemy固有の例外(IntegrityError等)をここで
定義する汎用的な例外へ変換することで、Service層はSQLAlchemyへ直接
依存せずにハンドリングできる。
"""

from __future__ import annotations


class RepositoryError(Exception):
    """Repository層の例外の基底クラス。"""


class DuplicateKeyError(RepositoryError):
    """一意制約違反(例: 同じメールアドレスでの重複登録)。"""


class RecordNotFoundError(RepositoryError):
    """更新・削除対象のレコードが見つからない場合の例外。

    `user_id`と`id`の組み合わせで見つからない場合は、対象が
    元から存在しない場合と、他ユーザーのデータへアクセスしようと
    した場合の両方を区別なくこの例外として扱う(requirements.md
    13章のuser_id境界を、存在有無の推測に使わせないため)。
    """


class RepositoryConnectionError(RepositoryError):
    """DB接続エラー等、インフラ起因で一時的に発生しうる例外。"""
