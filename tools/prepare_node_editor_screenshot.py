"""Prepare one Blender Node Editor view for an external X11 screenshot."""
from pathlib import Path
import argparse
import sys

import bpy


GROUPS = {
    "temporal-response": "DH Audio Temporal Response",
    "spectrum-history": "DH Audio Spectrum History",
    "material-reader": "DH Audio Material Reader",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", required=True, choices=GROUPS)
    parser.add_argument("--ready-file", required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def prepare(args):
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo / "src"))
    import dh_audio_toolkit

    dh_audio_toolkit.main()
    tree = bpy.data.node_groups.get(GROUPS[args.group])
    if tree is None:
        raise RuntimeError(f"Missing node group: {GROUPS[args.group]}")

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {"VIEW_3D", "NODE_EDITOR"}:
                area.type = "NODE_EDITOR"
                space = area.spaces.active
                space.tree_type = "GeometryNodeTree"
                space.pin = True
                space.node_tree = tree
                region = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=window, area=area, region=region):
                    bpy.ops.node.view_all()
                Path(args.ready_file).touch()
                return
    raise RuntimeError("No suitable Blender UI area found")


def main():
    args = parse_args()
    prepare(args)


if __name__ == "__main__":
    main()
