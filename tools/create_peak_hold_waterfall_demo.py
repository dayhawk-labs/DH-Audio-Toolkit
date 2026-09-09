"""Create the canonical Peak-Hold Waterfall Surface demo file.

Run from Blender 5.2+:
    blender --background --factory-startup --python \
      tools/create_peak_hold_waterfall_demo.py -- \
      --output "temp/DH Audio Toolkit Peak Hold Waterfall Demo.blend"

The demo intentionally contains no external audio or private scene data. Assign
a Sound datablock to the Analyzer node after opening it, then play from frame 1.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import runpy
import sys

import bpy


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def socket(sockets, name):
    for item in sockets:
        if item.name == name:
            return item
    raise KeyError(name)


def set_input(node, name, value):
    socket(node.inputs, name).default_value = value


def group_node(tree, group_name, label, location):
    node = tree.nodes.new("GeometryNodeGroup")
    node.node_tree = bpy.data.node_groups[group_name]
    node.label = label
    node.location = location
    return node


def frame(tree, label, location, size):
    item = tree.nodes.new("NodeFrame")
    item.label = label
    item.name = label
    item.location = location
    item.label_size = 24
    item.shrink = False
    item.width, item.height = size
    return item


def main():
    options = args()
    repo = Path(__file__).resolve().parents[1]
    namespace = runpy.run_path(str(repo / "src" / "dh_audio_toolkit.py"))
    namespace["main"]()

    tree = bpy.data.node_groups.new("DH Demo - Peak-Hold Waterfall", "GeometryNodeTree")
    tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    output = tree.nodes.new("NodeGroupOutput")
    output.is_active_output = True
    output.location = (1050, -40)

    analyzer = group_node(tree, "DH Audio Analyzer", "1  ANALYZE AUDIO", (-1050, 0))
    set_input(analyzer, "Bands", 8)
    temporal = group_node(tree, "DH Audio Temporal Response", "2  SMOOTH + PEAK", (-650, 0))
    set_input(temporal, "Attack", 0.05)
    set_input(temporal, "Release", 0.25)
    set_input(temporal, "Peak Hold", True)
    set_input(temporal, "Peak Hold Time", 0.20)
    set_input(temporal, "Peak Decay", 0.50)
    points = group_node(tree, "DH Audio Spectrum Points", "3  POSITION BANDS", (-250, 0))
    set_input(points, "Height", 3.0)
    set_input(points, "Center Spectrum", True)
    history = group_node(tree, "DH Audio Spectrum History", "4  RETAIN + CONNECT", (200, 0))
    set_input(history, "Frames", 4)
    set_input(history, "History Offset", (0.0, -0.15, 0.0))
    set_input(history, "Surface", True)
    set_input(history, "Row Decimation", 1)

    tree.links.new(socket(analyzer.outputs, "Spectrum"), socket(temporal.inputs, "Spectrum"))
    tree.links.new(socket(temporal.outputs, "Spectrum"), socket(points.inputs, "Spectrum"))
    tree.links.new(socket(points.outputs, "Spectrum Points"), socket(history.inputs, "Spectrum Points"))
    tree.links.new(socket(history.outputs, "Surface"), socket(output.inputs, "Geometry"))

    f1 = frame(tree, "AUDIO IN", (-1100, 250), (330, 190))
    f2 = frame(tree, "TEMPORAL RESPONSE", (-700, 250), (330, 290))
    f3 = frame(tree, "WATERFALL SURFACE", (150, 250), (430, 290))
    analyzer.parent = f1
    temporal.parent = f2
    points.parent = f3
    history.parent = f3

    text = bpy.data.texts.new("Peak-Hold Waterfall - How To Use")
    text.write("DH AUDIO TOOLKIT - PEAK-HOLD WATERFALL\n\n")
    text.write("Assign a Sound datablock to the Analyzer node, then play from frame 1.\n")
    text.write("The graph is intentionally small: 8 bands x 4 retained rows = 32 vertices / 21 quads.\n\n")
    text.write("Temporal Response keeps live dh_audio_amp and adds dh_audio_peak.\n")
    text.write("Spectrum History Surface preserves both attributes plus history metadata.\n")
    text.write("For a material, use DH Audio Material Reader after Set Material; choose Peak for held markers.\n")
    text.write("Simulation Zones require sequential playback or baking before final rendering.\n")

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 120
    scene.frame_set(1)
    obj = bpy.data.objects.new("DH Demo - Peak-Hold Waterfall", bpy.data.meshes.new("DH Demo Host Mesh"))
    obj.modifiers.new(name="Peak-Hold Waterfall Demo", type="NODES").node_group = tree
    scene.collection.objects.link(obj)

    tree["dh_demo_id"] = "peak_hold_waterfall"
    tree["dh_demo_expected_topology"] = "8 bands x 4 rows = 32 vertices, 21 quad faces"
    tree["dh_demo_workflow"] = "Analyzer -> Temporal Response -> Spectrum Points -> Spectrum History Surface"
    obj["dh_demo_notes"] = "Assign Sound, play sequentially from frame 1, then inspect Surface and peak attributes."

    options.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(options.output), check_existing=False)
    print(f"DH_DEMO_CREATED={options.output}")


if __name__ == "__main__":
    main()
