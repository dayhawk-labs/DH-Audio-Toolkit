"""Prepare the complete Peak-Hold Waterfall demo graph for a UI screenshot."""
import argparse
from pathlib import Path
import sys
import bpy


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--ready-file", type=Path, required=True)
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:])


def main():
    a = args()
    tree = bpy.data.node_groups["DH Demo - Peak-Hold Waterfall"]
    state = {"framed": False}
    def prepare():
        win = bpy.context.window_manager.windows[0]
        area = next(x for x in win.screen.areas if x.type in {"VIEW_3D", "NODE_EDITOR"})
        area.type = "NODE_EDITOR"
        space = area.spaces.active
        space.tree_type = "GeometryNodeTree"; space.pin = True; space.node_tree = tree
        space.show_region_ui = False; space.show_region_toolbar = False
        region = next(x for x in area.regions if x.type == "WINDOW")
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.screen.screen_full_area(use_hide_panels=True)
        return None
    def frame():
        win = bpy.context.window_manager.windows[0]
        area = next((x for x in win.screen.areas if x.type == "NODE_EDITOR"), None)
        if area is None: return 0.25
        region = next(x for x in area.regions if x.type == "WINDOW")
        with bpy.context.temp_override(window=win, area=area, region=region):
            if not state["framed"]:
                bpy.ops.node.view_all(); bpy.ops.view2d.zoom_out(); state["framed"] = True; return 0.75
        bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=3)
        nodes = list(tree.nodes)
        left=min(n.location.x for n in nodes); right=max(n.location.x+n.width for n in nodes)
        top=max(n.location.y for n in nodes); bottom=min(n.location.y-n.dimensions.y for n in nodes)
        v=region.view2d
        x1,y1=v.view_to_region(left,top,clip=False); x2,y2=v.view_to_region(right,bottom,clip=False)
        a.ready_file.write_text(f"{region.x+min(x1,x2)} {region.y+max(y1,y2)} {abs(x2-x1)} {abs(y2-y1)}\n")
        return None
    bpy.app.timers.register(prepare, first_interval=.5)
    bpy.app.timers.register(frame, first_interval=1.5)

main()
