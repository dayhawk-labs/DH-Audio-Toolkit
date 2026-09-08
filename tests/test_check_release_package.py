import importlib.util
from pathlib import Path
from zipfile import ZipFile


MODULE = Path(__file__).parents[1] / "tools" / "check_release_package.py"
SPEC = importlib.util.spec_from_file_location("check_release_package", MODULE)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(CHECKER)


def make_archive(path: Path, members: set[str]) -> None:
    with ZipFile(path, "w") as bundle:
        for member in members:
            bundle.writestr(member, b"")


def test_expected_manifest_is_accepted(tmp_path):
    archive = tmp_path / "release.zip"
    make_archive(archive, CHECKER.expected_members("3.11.1"))
    assert CHECKER.check(archive, "3.11.1") == []


def test_backup_file_is_rejected(tmp_path):
    archive = tmp_path / "release.zip"
    members = CHECKER.expected_members("3.11.1") | {
        "DH Audio Toolkit 3.11.1/DH Audio Toolkit 3.11.1.blend1"
    }
    make_archive(archive, members)
    errors = CHECKER.check(archive, "3.11.1")
    assert any(error.startswith("BLENDER_BACKUPS:") for error in errors)


def test_unexpected_member_is_rejected(tmp_path):
    archive = tmp_path / "release.zip"
    members = CHECKER.expected_members("3.11.1") | {"DH Audio Toolkit 3.11.1/notes.txt"}
    make_archive(archive, members)
    assert any(error.startswith("UNEXPECTED_MEMBERS:") for error in CHECKER.check(archive, "3.11.1"))
