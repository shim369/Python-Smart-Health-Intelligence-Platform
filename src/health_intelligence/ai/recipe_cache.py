"""レシピ生成結果のプロセス内キャッシュ。

requirements.md 11章 Recipe Cache: 同一入力(食材リスト・食事制限・
カロリー目標)に対する重複したAI API呼び出しを抑制する。

プロセスメモリ上のキャッシュのため、アプリケーション再起動やStreamlit
Community Cloudのスリープ復帰では消える。複数プロセス間で共有したい
場合や永続化したい場合は、Phase 9以降でDB等への保存を検討する
(現状はこの制約を許容した簡易実装)。
"""

from __future__ import annotations

from health_intelligence.ai.schemas import GeneratedRecipe, RecipeInput


def _cache_key(recipe_input: RecipeInput) -> tuple[object, ...]:
    return (
        tuple(sorted(recipe_input.ingredient_names)),
        recipe_input.dietary_preference,
        recipe_input.calorie_target,
    )


class RecipeCache:
    """`RecipeInput`をキーにした単純なプロセス内キャッシュ。"""

    def __init__(self) -> None:
        self._store: dict[tuple[object, ...], GeneratedRecipe] = {}

    def get(self, recipe_input: RecipeInput) -> GeneratedRecipe | None:
        return self._store.get(_cache_key(recipe_input))

    def set(self, recipe_input: RecipeInput, recipe: GeneratedRecipe) -> None:
        self._store[_cache_key(recipe_input)] = recipe
