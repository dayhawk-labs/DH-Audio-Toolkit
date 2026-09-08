#!/usr/bin/env python3
"""Validate the distributable DH Audio Toolkit ZIP without external tools."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile


def expected_members(version: str) -> set[str]:
    folder = f"DH Audio Toolkit {version}"
    return {
        f"{folder}/",
        f"{folder}/DH Audio Toolkit {version}.blend",
        f"{folder}/README.md",
        f"{folder}/blender_assets.cats.txt",
    }


def check(archive: Path, version: str) -> list[str]:
    if not archive.is_file():
        return [f"MISSING_ARCHIVE: {archive}"]
    try:
        with ZipFile(archive) as bundle:
            members = set(bundle.namelist())
            bad_backups = sorted(
                name for name in members if Path(name).name.startswith("DH Audio Toolkit")
                and ".blend" in Path(name).name
                and not Path(name).name.endswith(".blend")
            )
    except BadZipFile:
        return [f"INVALID_ARCHIVE: {archive}"]

    errors: list[str] = []
    if bad_backups:
        errors.append(f"BLENDER_BACKUPS: {', '.join(bad_backups)}")
    expected = expected_members(version)
    if members != expected:
        missing = sorted(expected - members)
        extra = sorted(members - expected)
        if missing:
            errors.append(f"MISSING_MEMBERS: {', '.join(missing)}")
        if extra:
            errors.append(f"UNEXPECTED_MEMBERS: {', '.join(extra)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    errors = check(args.archive, args.version)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: release package matches {args.version} manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
