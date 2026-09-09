"""Export the generated public node interfaces as reviewable JSON.

Run this from Blender after opening a freshly generated DH Audio Toolkit blend:

    blender --background "temp/DH Audio Toolkit <version>.blend" \
      --python tools/export_public_node_interfaces.py -- \
      --output temp/public_node_interfaces.json --expect 25

The output is intentionally limited to public asset groups.  It is the machine
readable source for the Markdown node reference generator, so documentation is
grounded in the generated Blender interface rather than copied by hand.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import bpy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect", type=int, default=25)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def json_value(value):
    """Return a stable JSON representation of a Blender socket property."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    # Blender vector and color defaults are bpy property arrays rather than
    # Python lists. They are iterable, but their repr contains transient RNA
    # implementation text and is not useful documentation.
    try:
        return [json_value(item) for item in value]
    except TypeError:
        pass
    return str(value)


def optional_property(item, name):
    try:
        return json_value(getattr(item, name))
    except (AttributeError, TypeError, ValueError):
        return None


def export_socket(item) -> dict[str, object]:
    return {
        "kind": "socket",
        "name": item.name,
        "panel": item.parent.name if item.parent else None,
        "direction": item.in_out,
        "socket_type": item.socket_type,
        "interface_type": type(item).__name__,
        "description": item.description or "",
        "default": optional_property(item, "default_value"),
        "minimum": optional_property(item, "min_value"),
        "maximum": optional_property(item, "max_value"),
        "subtype": optional_property(item, "subtype"),
    }


def export_panel(item) -> dict[str, object]:
    return {
        "kind": "panel",
        "name": item.name,
        "panel": item.parent.name if item.parent else None,
        "default_closed": bool(item.default_closed),
        "description": item.description or "",
    }


def export_tree(tree) -> dict[str, object]:
    items = []
    for item in tree.interface.items_tree:
        if item.item_type == "SOCKET":
            items.append(export_socket(item))
        elif item.item_type == "PANEL":
            items.append(export_panel(item))

    return {
        "name": tree.name,
        "tree_type": tree.bl_idname,
        "description": tree.description or "",
        "default_width": int(tree.default_group_node_width),
        "catalog_id": tree.asset_data.catalog_id if tree.asset_data else "",
        "items": items,
    }


def main() -> None:
    args = parse_args()
    public_trees = sorted(
        (tree for tree in bpy.data.node_groups if tree.asset_data),
        key=lambda tree: tree.name,
    )
    if len(public_trees) != args.expect:
        raise RuntimeError(
            f"expected {args.expect} public assets, found {len(public_trees)}: "
            f"{[tree.name for tree in public_trees]}"
        )

    document = {
        "schema": "dh-audio-toolkit.public-node-interfaces.v1",
        "blender": bpy.app.version_string,
        "toolkit_version": public_trees[0].get("dh_audio_toolkit_version", ""),
        "nodes": [export_tree(tree) for tree in public_trees],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        "DH_AUDIO_PUBLIC_INTERFACES="
        + json.dumps({"nodes": len(public_trees), "output": str(args.output)})
    )


if __name__ == "__main__":
    main()
