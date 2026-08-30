"""shopping_memo.pyの純粋関数のテスト。"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from components.shopping_memo import (  # noqa: E402
    append_recipe_ingredients,
    format_recipe_ingredients_line,
)

from health_intelligence.domain.enums import RecipeSource  # noqa: E402
from health_intelligence.domain.models import Recipe  # noqa: E402


def _make_recipe(title: str = "鶏むね肉とキャベツの塩昆布炒め") -> Recipe:
    return Recipe(
        recipe_id=uuid4(),
        user_id=uuid4(),
        title=title,
        instructions="炒めるだけ",
        source=RecipeSource.AI_GENERATED,
        created_at=datetime.now(UTC),
    )


def test_format_recipe_ingredients_line_joins_names_with_comma() -> None:
    recipe = _make_recipe()
    line = format_recipe_ingredients_line(recipe, ["鶏むね肉", "キャベツ", "ごま油"])

    assert line == "鶏むね肉とキャベツの塩昆布炒め: 鶏むね肉, キャベツ, ごま油"


def test_append_recipe_ingredients_to_empty_memo() -> None:
    recipe = _make_recipe()
    result = append_recipe_ingredients("", recipe, ["鶏むね肉", "キャベツ"])

    assert result == "鶏むね肉とキャベツの塩昆布炒め: 鶏むね肉, キャベツ"


def test_append_recipe_ingredients_to_existing_memo_adds_newline() -> None:
    recipe = _make_recipe("味噌汁")
    result = append_recipe_ingredients("卵を買う", recipe, ["味噌", "豆腐"])

    assert result == "卵を買う\n味噌汁: 味噌, 豆腐"


def test_append_recipe_ingredients_treats_whitespace_only_memo_as_empty() -> None:
    recipe = _make_recipe("味噌汁")
    result = append_recipe_ingredients("   ", recipe, ["味噌"])

    assert result == "味噌汁: 味噌"
