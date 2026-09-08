"""Capture readable Blender Node Editor screenshots for selected node groups."""
from pathlib import Path
import sys

import bpy


GROUPS = {
    "temporal-response": "DH Audio Temporal Response",
    "spectrum-history": "DH Audio Spectrum History",
    "material-reader": "DH Audio Material Reader",
}


def node_area():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {"VIEW_3D", "NODE_EDITOR"}:
                return window, area
    raise RuntimeError("No suitable Blender UI area found")


def capture(tree, path):
    window, area = node_area()
    area.type = "NODE_EDITOR"
    space = area.spaces.active
    space.tree_type = "GeometryNodeTree"
    space.pin = True
    space.geometry_nodes_type = "MODIFIER"
    space.node_tree = tree
    with bpy.context.temp_override(window=window, area=area, region=next(r for r in area.regions if r.type == "WINDOW")):
        bpy.ops.node.view_all()
        bpy.ops.screen.screenshot(filepath=str(path), full=False)


def main():
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo / "src"))
    import dh_audio_toolkit
    dh_audio_toolkit.main()
    output = repo / "temp" / "node-previews"
    output.mkdir(parents=True, exist_ok=True)
    for slug, name in GROUPS.items():
        tree = bpy.data.node_groups.get(name)
        if tree:
            capture(tree, output / f"{slug}.png")
    print(f"Captured {len(list(output.glob('*.png')))} node editor previews")


if __name__ == "__main__":
    main()
