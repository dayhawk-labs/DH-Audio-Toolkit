from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_material_recipe_documents_the_cross_editor_signal_path():
    recipe = (ROOT / "docs" / "recipes" / "material_response.md").read_text(encoding="utf-8")
    for text in (
        "DH Audio Analyzer [Spectrum]",
        "DH Audio Temporal Response [Spectrum]",
        "DH Audio Material Reader [Amplitude or Peak]",
        "DH Audio Shader Response",
        "Use Instancer",
        "dh_audio_amp",
        "dh_audio_peak",
        "sequential timeline evaluation",
    ):
        assert text in recipe


def test_material_recipe_is_linked_from_indexes():
    assert "recipes/material_response.md" in (ROOT / "docs" / "RECIPES.md").read_text(encoding="utf-8")
    assert "docs/recipes/material_response.md" in (ROOT / "README.md").read_text(encoding="utf-8")
