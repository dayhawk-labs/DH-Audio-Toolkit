#!/usr/bin/env python3
"""Check public-group and version consistency without requiring Blender."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VERSION = re.compile(r"([0-9]+(?:\.[0-9]+)+(?:-[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)?)")
GROUP = re.compile(r"DH Audio [A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*")


def lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def authoritative_version(root: Path) -> str | None:
    path = root / "VERSION"
    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value if VERSION.fullmatch(value) else None


def versions(path: Path) -> list[tuple[str, int]]:
    result = []
    for number, line in enumerate(lines(path), 1):
        if "TOOLKIT_VERSION" in line:
            match = VERSION.search(line.split("=", 1)[-1])
        else:
            match = re.search(r"DH Audio Toolkit\s+(" + VERSION.pattern + r")", line, re.I)
        if match:
            result.append((match.group(1).removesuffix(".blend"), number))
    return result


def groups(path: Path, kind: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for number, line in enumerate(lines(path), 1):
        if kind == "source" and re.match(r"^\s*#\s+-\s+DH Audio ", line):
            match = GROUP.search(line)
        elif kind == "tests" and "PUBLIC_GROUPS" in "".join(lines(path)[:number]):
            match = re.search(r'"(DH Audio [^"]+)"\s*:', line)
        elif kind == "readme":
            match = re.search(
                r"\*\*(DH Audio [A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*)\*\*",
                line,
            )
            if not match:
                match = re.fullmatch(
                    r"\s*(DH Audio [A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*)\s*", line
                )
        else:
            match = None
        if match:
            name = match.group(1) if kind in {"tests", "readme"} else match.group(0)
            result[name] = number
    return result


def check(root: Path, *, require_release: bool = False) -> list[str]:
    required = {
        "source": root / "src/dh_audio_toolkit.py",
        "tests": root / "tests/blender_52_regression.py",
        "readme": root / "README.md",
        "validation": root / "docs/VALIDATION.md",
    }
    missing = [str(path.relative_to(root)) for path in required.values() if not path.is_file()]
    if not (root / "VERSION").is_file():
        missing.append("VERSION")
    if missing:
        return [f"MISSING: {path}" for path in missing]

    expected = authoritative_version(root)
    errors: list[str] = []
    if expected is None:
        errors.append("INVALID_VERSION: VERSION must contain one semantic version")
    else:
        for path in required.values():
            for value, line in versions(path):
                if value != expected:
                    errors.append(
                        f"STALE_VERSION: {path.relative_to(root)}:{line} has {value}, expected {expected}"
                    )
        expected_release_note = root / "docs" / f"RELEASE_NOTES_{expected}.md"
        if not expected_release_note.is_file():
            errors.append(f"MISSING_CURRENT_RELEASE_NOTE: {expected_release_note.relative_to(root)}")
        if require_release:
            expected_blend = (
                root / "releases" / f"DH Audio Toolkit {expected}"
                / f"DH Audio Toolkit {expected}.blend"
            )
            if not expected_blend.is_file():
                errors.append(f"MISSING_CURRENT_RELEASE: {expected_blend.relative_to(root)}")

    inventories = {kind: groups(path, kind) for kind, path in required.items() if kind != "validation"}
    authoritative = inventories["tests"]
    if not authoritative:
        errors.append("NO_PUBLIC_GROUPS: tests inventory is empty")
    for kind, inventory in inventories.items():
        for name, line in sorted(authoritative.items()):
            if name not in inventory:
                errors.append(f"MISSING_GROUP: {kind} lacks {name!r} (expected from tests:{line})")
        for name, line in sorted(inventory.items()):
            if name not in authoritative:
                errors.append(f"EXTRA_GROUP: {kind} has {name!r} at line {line}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--require-release",
        action="store_true",
        help="require the current generated .blend release artifact",
    )
    args = parser.parse_args()
    errors = check(args.root.resolve(), require_release=args.require_release)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: public groups and versions are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
