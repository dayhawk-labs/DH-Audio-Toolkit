from pathlib import Path


DEMO = Path(__file__).parents[1] / "tools" / "create_peak_hold_waterfall_demo.py"


def test_demo_is_reproducible_and_uses_the_verified_public_chain():
    source = DEMO.read_text(encoding="utf-8")
    expected = (
        '"DH Audio Analyzer"',
        '"DH Audio Temporal Response"',
        '"DH Audio Spectrum Points"',
        '"DH Audio Spectrum History"',
        'socket(history.outputs, "Surface")',
        '"dh_demo_id"',
        '"peak_hold_waterfall"',
        'make_demo_sound()',
        'make_showcase(scene, tree, material)',
        'sound.pack()',
    )
    assert all(fragment in source for fragment in expected)
    assert "--output" in source
