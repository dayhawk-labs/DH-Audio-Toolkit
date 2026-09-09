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
import math
from pathlib import Path
import runpy
import sys
import tempfile
import wave

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


def make_demo_sound():
    """Create and pack a tiny synthetic sound so the demo is immediately playable."""
    sample_rate = 44100
    duration = 4.0
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        wav_path = Path(handle.name)
    try:
        with wave.open(str(wav_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = bytearray()
            for index in range(int(sample_rate * duration)):
                time = index / sample_rate
                sweep = 180.0 + 700.0 * time / duration
                value = 0.35 * math.sin(2.0 * math.pi * sweep * time)
                value += 0.15 * math.sin(2.0 * math.pi * (sweep * 2.01) * time)
                frames.extend(int(max(-1.0, min(1.0, value)) * 32767).to_bytes(2, "little", signed=True))
            wav.writeframes(frames)
        sound = bpy.data.sounds.load(str(wav_path), check_existing=False)
        sound.name = "DH Demo - Synthetic Sweep (packed)"
        sound.pack()
        return sound
    finally:
        wav_path.unlink(missing_ok=True)


def make_showcase(scene, tree, material):
    """Create a camera aimed at the actual Geometry Nodes result."""
    host = bpy.data.objects.new("DH Demo - Evaluated Waterfall", bpy.data.meshes.new("DH Demo Host Mesh"))
    scene.collection.objects.link(host)
    host.modifiers.new(name="Peak-Hold Waterfall Demo", type="NODES").node_group = tree
    host.data.materials.append(material)
    host["dh_demo_notes"] = "This object is driven by the documented node tree; no decorative preview mesh is used."

    camera_data = bpy.data.cameras.new("DH Demo Camera")
    camera = bpy.data.objects.new("DH Demo Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0.0, -5.8, 3.8)
    camera.rotation_euler = (math.radians(58), 0.0, 0.0)
    camera_data.lens = 52
    scene.camera = camera
    for name, location, energy, size in (
        ("DH Demo Key", (2.5, -3.0, 5.0), 900, 4.0),
        ("DH Demo Fill", (-3.0, -1.0, 2.5), 500, 3.0),
    ):
        light_data = bpy.data.lights.new(name, "AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new(name, light_data)
        light.location = location
        scene.collection.objects.link(light)
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.filepath = "//DH Demo Waterfall Preview.png"


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
    analyzer.inputs["Sound"].default_value = make_demo_sound()
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
    material = bpy.data.materials.new("DH Demo - Peak Emission")
    material.diffuse_color = (0.04, 0.28, 0.8, 1.0)
    material.metallic = 0.15
    material.roughness = 0.28
    set_material = tree.nodes.new("GeometryNodeSetMaterial")
    set_material.inputs["Material"].default_value = material
    set_material.location = (650, -40)
    tree.links.new(socket(history.outputs, "Surface"), socket(set_material.inputs, "Geometry"))
    tree.links.new(socket(set_material.outputs, "Geometry"), socket(output.inputs, "Geometry"))

    f1 = frame(tree, "AUDIO IN", (-1100, 250), (330, 190))
    f2 = frame(tree, "TEMPORAL RESPONSE", (-700, 250), (330, 290))
    f3 = frame(tree, "WATERFALL SURFACE", (150, 250), (430, 290))
    analyzer.parent = f1
    temporal.parent = f2
    points.parent = f3
    history.parent = f3

    text = bpy.data.texts.new("Peak-Hold Waterfall - How To Use")
    text.write("DH AUDIO TOOLKIT - PEAK-HOLD WATERFALL\n\n")
    text.write("A packed synthetic sweep is assigned to Analyzer.Sound; replace it with your own Sound if desired.\n")
    text.write("The graph is intentionally small: 8 bands x 4 retained rows = 32 vertices / 21 quads.\n\n")
    text.write("Temporal Response keeps live dh_audio_amp and adds dh_audio_peak.\n")
    text.write("Spectrum History Surface preserves both attributes plus history metadata.\n")
    text.write("For a material, use DH Audio Material Reader after Set Material; choose Peak for held markers.\n")
    text.write("Simulation Zones require sequential playback or baking before final rendering.\n")

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 120
    scene.frame_set(1)
    tree["dh_demo_id"] = "peak_hold_waterfall"
    tree["dh_demo_expected_topology"] = "8 bands x 4 rows = 32 vertices, 21 quad faces"
    tree["dh_demo_workflow"] = "Analyzer -> Temporal Response -> Spectrum Points -> Spectrum History Surface"
    make_showcase(scene, tree, material)

    options.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(options.output), check_existing=False)
    print(f"DH_DEMO_CREATED={options.output}")


if __name__ == "__main__":
    main()
