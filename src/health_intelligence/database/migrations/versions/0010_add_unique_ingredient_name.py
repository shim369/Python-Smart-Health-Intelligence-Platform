"""add unique index on lower(ingredients.name)

食材マスタのget-or-createが同時リクエストで競合(TOCTOU)し、同名の食材が
重複作成されるのを防ぐため、`lower(name)`に一意インデックスを張る
(`IngredientRepository.get_by_name`が大文字小文字を区別しないのに合わせる)。

インデックス作成前に既存の重複を統合する。同じ`lower(name)`の中でidが
最小の行を残し、recipe_ingredientsの参照を付け替えてから重複行を削除する。
付け替えによって同一レシピ内で主キー(recipe_id, ingredient_id)が衝突する
行は、1件だけ残して削除する(同一レシピ内の同名食材は保存時に統合される
ため、通常は発生しない)。

Revision ID: 0010
Revises: 0009
Create Date: (食材マスタの重複作成対策に伴い追加)
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TEMP TABLE ingredient_dedup AS
        SELECT id AS dup_id, keep_id
        FROM (
            SELECT id, first_value(id) OVER (PARTITION BY lower(name) ORDER BY id) AS keep_id
            FROM ingredients
        ) ranked
        WHERE id <> keep_id
        """
    )
    # 付け替え後に同じ(recipe_id, keep_id)になる行のうち、ingredient_idが
    # 最小の行(=残す食材を直接参照している行があればそれ)以外を削除する
    op.execute(
        """
        DELETE FROM recipe_ingredients ri
        USING ingredient_dedup d
        WHERE ri.ingredient_id = d.dup_id
          AND EXISTS (
              SELECT 1
              FROM recipe_ingredients other
              LEFT JOIN ingredient_dedup od ON od.dup_id = other.ingredient_id
              WHERE other.recipe_id = ri.recipe_id
                AND COALESCE(od.keep_id, other.ingredient_id) = d.keep_id
                AND other.ingredient_id < ri.ingredient_id
          )
        """
    )
    op.execute(
        """
        UPDATE recipe_ingredients ri
        SET ingredient_id = d.keep_id
        FROM ingredient_dedup d
        WHERE ri.ingredient_id = d.dup_id
        """
    )
    op.execute("DELETE FROM ingredients WHERE id IN (SELECT dup_id FROM ingredient_dedup)")
    op.execute("DROP TABLE ingredient_dedup")

    op.execute("CREATE UNIQUE INDEX uq_ingredients_name_lower ON ingredients (lower(name))")


def downgrade() -> None:
    # 統合済みの重複データは復元しない(インデックスのみ削除する)
    op.drop_index("uq_ingredients_name_lower", table_name="ingredients")
