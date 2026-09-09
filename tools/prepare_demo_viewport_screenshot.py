"""Evaluate the Peak-Hold Waterfall demo and present its actual GN output."""
import argparse
from pathlib import Path
import sys
import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready-file", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    state = {"done": False}

    def prepare():
        scene = bpy.context.scene
        # Simulation Zones require sequential evaluation.
        for frame in range(scene.frame_start, 5):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
        window = bpy.context.window_manager.windows[0]
        area = next(a for a in window.screen.areas if a.type in {"VIEW_3D", "NODE_EDITOR"})
        area.type = "VIEW_3D"
        space = area.spaces.active
        space.region_3d.view_perspective = "CAMERA"
        space.shading.type = "MATERIAL"
        space.overlay.show_overlays = False
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(window=window, area=area, region=region):
            bpy.ops.screen.screen_full_area(use_hide_panels=True)
        return None

    def ready():
        window = bpy.context.window_manager.windows[0]
        area = next((a for a in window.screen.areas if a.type == "VIEW_3D"), None)
        if area is None:
            return 0.25
        bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=4)
        args.ready_file.write_text("ready\n", encoding="ascii")
        return None

    bpy.app.timers.register(prepare, first_interval=.5)
    bpy.app.timers.register(ready, first_interval=2.0)


main()
