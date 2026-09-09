"""Keep the featured recipe aligned with the tested public workflow."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_featured_recipe_names_the_verified_public_connections():
    recipe = (ROOT / "docs" / "recipes" / "peak_hold_waterfall.md").read_text(
        encoding="utf-8"
    )
    for connection in (
        "Analyzer **Spectrum** | Temporal Response **Spectrum**",
        "Temporal Response **Spectrum** | Spectrum Points **Spectrum**",
        "Spectrum Points **Spectrum Points** | Spectrum History **Spectrum Points**",
        "Spectrum History **Surface** | Group Output **Geometry**",
    ):
        assert connection in recipe
    assert "32 vertices" in recipe
    assert "21 quad faces" in recipe
    assert "two Simulation Zones" in recipe


def test_recipe_index_and_readme_link_to_featured_recipe():
    recipe_path = "recipes/peak_hold_waterfall.md"
    assert recipe_path in (ROOT / "docs" / "RECIPES.md").read_text(encoding="utf-8")
    assert "docs/recipes/peak_hold_waterfall.md" in (ROOT / "README.md").read_text(
        encoding="utf-8"
    )
