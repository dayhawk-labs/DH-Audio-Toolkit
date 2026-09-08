import importlib.util
import tempfile
from pathlib import Path

MODULE = Path(__file__).parents[1] / "tools" / "check_consistency.py"
SPEC = importlib.util.spec_from_file_location("check_consistency", MODULE)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(CHECKER)


def write_fixture(root: Path, *, missing_readme: bool = False) -> None:
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "docs").mkdir()
    (root / "tools").mkdir()
    (root / "VERSION").write_text("3.11.0-beta.1\n")
    (root / "src/dh_audio_toolkit.py").write_text(
        'TOOLKIT_VERSION = "3.11.0-beta.1"\n#   - DH Audio Analyzer\n'
    )
    (root / "tests/blender_52_regression.py").write_text(
        'TOOLKIT_VERSION = "3.11.0-beta.1"\nPUBLIC_GROUPS = {\n'
        '  "DH Audio Analyzer": ("GeometryNodeTree", 1, "id"),\n}\n'
    )
    (root / "README.md").write_text(
        "# DH AUDIO TOOLKIT 3.11.0-beta.1\n\nDH Audio Analyzer\n"
        if not missing_readme else "# DH AUDIO TOOLKIT 3.11.0-beta.1\n"
    )
    (root / "docs/VALIDATION.md").write_text(
        "# Validation\nDH Audio Toolkit 3.11.0-beta.1.blend\n"
    )
    (root / "docs/RELEASE_NOTES_3.11.0-beta.1.md").write_text(
        "# DH Audio Toolkit 3.11.0-beta.1\n"
    )
    (root / "releases").mkdir()
    (root / "releases/DH Audio Toolkit 3.11.0-beta.1.blend").write_bytes(b"")


def test_real_repository_is_consistent():
    root = Path(__file__).parents[1]
    assert CHECKER.check(root) == []


def test_missing_group_is_reported():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_fixture(root, missing_readme=True)
        errors = CHECKER.check(root)
        assert any("MISSING_GROUP: readme" in error for error in errors)


def test_version_mismatch_is_reported():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_fixture(root)
        (root / "docs/VALIDATION.md").write_text("DH Audio Toolkit 3.10.0.blend\n")
        assert any("STALE_VERSION" in error for error in CHECKER.check(root))
