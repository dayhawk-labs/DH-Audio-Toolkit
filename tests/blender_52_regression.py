"""Dependency-free Blender 5.2 regression suite for DH Audio Toolkit.

Run from Blender 5.2 or newer:

    blender --background --factory-startup \
      --python tests/blender_52_regression.py -- \
      --report temp/blender_52_report.json

Pass ``--release`` to finish by rebuilding and saving a clean asset library.
All generated audio and intermediate .blend files live in a temporary directory.
The release path and its adjacent ``blender_assets.cats.txt`` are the only
intentional persistent outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import struct
import sys
import tempfile
import traceback
import wave

import bpy


TOOLKIT_VERSION = (Path(__file__).resolve().parents[1] / "VERSION").read_text(
    encoding="utf-8"
).strip()

PUBLIC_GROUPS = {
    "DH Audio Analyzer": ("GeometryNodeTree", 330, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Stereo Analyzer": ("GeometryNodeTree", 350, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Bands": ("GeometryNodeTree", 330, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Sample Range": ("GeometryNodeTree", 315, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Frequency Map": ("GeometryNodeTree", 300, "bb4cca6c-c5d5-52c9-80fb-754adc068f91"),
    "DH Audio Frequency Selection": ("GeometryNodeTree", 280, "9b46dff4-fa9d-510f-b0ae-a8af6da87e3a"),
    "DH Audio Band Query": ("GeometryNodeTree", 285, "9b46dff4-fa9d-510f-b0ae-a8af6da87e3a"),
    "DH Audio Spectrum Sample": ("GeometryNodeTree", 310, "9b46dff4-fa9d-510f-b0ae-a8af6da87e3a"),
    "DH Audio Spectrum Bridge": ("GeometryNodeTree", 340, "a4faf3f4-5a13-5f83-ae97-28993f20ac20"),
    "DH Audio Mesh Deform": ("GeometryNodeTree", 340, "a4faf3f4-5a13-5f83-ae97-28993f20ac20"),
    "DH Audio Mesh Extrude": ("GeometryNodeTree", 350, "a4faf3f4-5a13-5f83-ae97-28993f20ac20"),
    "DH Audio Response": ("GeometryNodeTree", 285, "a4faf3f4-5a13-5f83-ae97-28993f20ac20"),
    "DH Audio Temporal Response": ("GeometryNodeTree", 310, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Spectrum History": ("GeometryNodeTree", 310, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Spectrum Points": ("GeometryNodeTree", 285, "bb4cca6c-c5d5-52c9-80fb-754adc068f91"),
    "DH Audio Stereo Points": ("GeometryNodeTree", 315, "bb4cca6c-c5d5-52c9-80fb-754adc068f91"),
    "DH Audio Radial Spectrum": ("GeometryNodeTree", 315, "bb4cca6c-c5d5-52c9-80fb-754adc068f91"),
    "DH Audio Spectrum Bars": ("GeometryNodeTree", 350, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Spectrum Instances": ("GeometryNodeTree", 315, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Spectrum Curve": ("GeometryNodeTree", 310, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Spectrum Fill": ("GeometryNodeTree", 290, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Material Reader": ("ShaderNodeTree", 300, "1a181044-5483-5a07-ad44-2025bf0459e4"),
    "DH Audio Shader Response": ("ShaderNodeTree", 285, "1a181044-5483-5a07-ad44-2025bf0459e4"),
    "DH Audio Shader Map": ("ShaderNodeTree", 300, "1a181044-5483-5a07-ad44-2025bf0459e4"),
    "DH Audio Shader UV Transform": ("ShaderNodeTree", 320, "1a181044-5483-5a07-ad44-2025bf0459e4"),
}

INTERNAL_GROUPS = {
    "DH Internal - Store Spectrum Attributes",
    "DH Internal - Store Stereo Attributes",
    "DH Internal - Store Spectrum Bridge Attributes",
    "DH Internal - Store Spectrum Face Attributes",
    "DH Internal - Named Band Map",
    "DH Internal - Store Named Band Metadata",
    "DH Internal - Store Named Bands",
}

SPECTRUM_ATTRIBUTES = (
    "dh_audio_amp",
    "dh_audio_norm",
    "dh_audio_raw",
    "dh_audio_band_index",
    "dh_audio_band_pos",
    "dh_audio_low_hz",
    "dh_audio_center_hz",
    "dh_audio_high_hz",
    "dh_audio_bandwidth_hz",
)

NAMED_BAND_ATTRIBUTES = (
    "dh_audio_total",
    "dh_audio_sub",
    "dh_audio_bass",
    "dh_audio_low_mid",
    "dh_audio_mid",
    "dh_audio_high_mids",
    "dh_audio_presence",
    "dh_audio_brilliance",
    "dh_audio_air",
)

HISTORY_ATTRIBUTES = (
    "dh_audio_history_index",
    "dh_audio_history_pos",
)

TEMPORAL_ATTRIBUTES = (
    "dh_audio_peak",
)

STEREO_ATTRIBUTES = (
    "dh_audio_channel",
    "dh_audio_channel_pos",
    "dh_audio_left_amp",
    "dh_audio_right_amp",
    "dh_audio_left_norm",
    "dh_audio_right_norm",
    "dh_audio_left_raw",
    "dh_audio_right_raw",
)

EXPECTED_PANELS = {
    "DH Audio Analyzer": {
        "Audio": False,
        "Spectrum": False,
        "Response": False,
        "Carrier": True,
        "Primary Outputs": False,
        "Frequency Metadata": True,
    },
    "DH Audio Stereo Analyzer": {
        "Audio": False,
        "Spectrum": False,
        "Response": False,
        "Carrier": True,
        "Stereo Outputs": False,
        "Advanced Outputs": True,
    },
    "DH Audio Bands": {
        "Audio": False,
        "Total Range": True,
        "Band Limits": False,
        "Band Outputs": False,
        "Attribute Bridge": True,
    },
    "DH Audio Spectrum Bars": {
        "Audio": False,
        "Spectrum": False,
        "Response": False,
        "Bars": False,
        "Profile": False,
        "Outputs": False,
        "Advanced Outputs": True,
    },
    "DH Audio Spectrum Curve": {
        "Source": False,
        "Curve": False,
        "Tube": True,
        "Outputs": False,
    },
    "DH Audio Temporal Response": {
        "Source": False,
        "Timing": False,
        "Peak Hold": False,
        "Outputs": False,
    },
    "DH Audio Spectrum History": {
        "Source": False,
        "History": False,
        "Surface": False,
        "Outputs": False,
    },
    "DH Audio Radial Spectrum": {
        "Source": False,
        "Radial Layout": False,
        "Outputs": False,
    },
    "DH Audio Stereo Points": {
        "Stereo Source": False,
        "Mirrored Layout": False,
        "Outputs": False,
    },
    "DH Audio Material Reader": {
        "Source": False,
        "Spectrum Attributes": False,
        "Stereo Attributes": False,
        "Frequency Metadata": True,
        "Spectrum History": True,
        "Temporal Response": True,
        "Named Bands": False,
    },
    "DH Audio Spectrum Sample": {
        "Query": False,
        "Band Values": False,
        "Stereo Values": False,
        "Frequency Metadata": True,
    },
    "DH Audio Spectrum Bridge": {
        "Geometry & Spectrum": False,
        "Band Mapping": False,
        "Attribute Storage": False,
        "Result": False,
        "Band Values": False,
        "Stereo Values": False,
        "Frequency Metadata": True,
    },
    "DH Audio Mesh Deform": {
        "Geometry & Spectrum": False,
        "Band Mapping": False,
        "Deformation": False,
        "Attribute Storage": True,
        "Outputs": False,
    },
    "DH Audio Mesh Extrude": {
        "Mesh & Spectrum": False,
        "Band Mapping": False,
        "Extrusion": False,
        "Outputs": False,
    },
    "DH Audio Shader Map": {
        "Mapping": False,
    },
    "DH Audio Shader UV Transform": {
        "Coordinates": False,
        "Offset": False,
        "Scale": True,
        "Rotation": True,
        "Outputs": False,
    },
}


class Report:
    def __init__(self):
        self.checks = []
        self.observations = {}

    def check(self, name, condition, details=None):
        passed = bool(condition)
        self.checks.append({"name": name, "passed": passed, "details": details})
        return passed

    def section(self, name, callback):
        try:
            callback()
        except Exception:
            self.check(name, False, traceback.format_exc())

    def result(self):
        passed = sum(item["passed"] for item in self.checks)
        failed = len(self.checks) - passed
        return {
            "blender": bpy.app.version_string,
            "toolkit": TOOLKIT_VERSION,
            "summary": {"passed": passed, "failed": failed},
            "checks": self.checks,
            "observations": self.observations,
        }


def _socket(sockets, name):
    socket = sockets[name] if isinstance(name, int) else sockets.get(name)
    if socket is None:
        raise KeyError(f"Socket {name!r} was not found")
    return socket


def _interface_socket(tree, name, in_out="INPUT"):
    for item in tree.interface.items_tree:
        if item.item_type == "SOCKET" and item.in_out == in_out and item.name == name:
            return item
    raise KeyError(f"{tree.name}: interface {in_out.lower()} {name!r} was not found")


def _set_input(node, name, value):
    socket = _socket(node.inputs, name)
    socket.default_value = value
    return socket


def _default_value(item):
    try:
        value = item.default_value
    except AttributeError:
        return None
    if hasattr(value, "name"):
        return value.name
    if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        try:
            return list(value)
        except TypeError:
            pass
    return value


def _tree_signature():
    payload = []
    for tree in sorted(
        (tree for tree in bpy.data.node_groups if tree.name in PUBLIC_GROUPS or tree.name in INTERNAL_GROUPS),
        key=lambda item: item.name,
    ):
        interface = []
        for item in tree.interface.items_tree:
            row = {
                "item_type": item.item_type,
                "name": item.name,
                "parent": item.parent.name if item.parent else None,
            }
            if item.item_type == "PANEL":
                row["default_closed"] = bool(item.default_closed)
            else:
                row.update(
                    in_out=item.in_out,
                    socket_type=item.socket_type,
                    identifier=item.identifier,
                    hide_value=bool(item.hide_value),
                    default=_default_value(item),
                )
            interface.append(row)

        nodes = sorted(
            (
                node.name,
                node.bl_idname,
                node.parent.name if node.parent else None,
                round(float(node.location.x), 3),
                round(float(node.location.y), 3),
                round(float(node.width), 3),
                round(float(node.get("dh_layout_height", node.height)), 3),
            )
            for node in tree.nodes
        )
        links = sorted(
            (
                link.from_node.name,
                link.from_socket.identifier,
                link.to_node.name,
                link.to_socket.identifier,
            )
            for link in tree.links
        )
        payload.append(
            {
                "name": tree.name,
                "type": tree.bl_idname,
                "role": tree.get("dh_role"),
                "width": tree.default_group_node_width,
                "asset": bool(tree.asset_data),
                "catalog": str(tree.asset_data.catalog_id) if tree.asset_data else None,
                "interface": interface,
                "nodes": nodes,
                "links": links,
            }
        )

    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf8")
    return hashlib.sha256(raw).hexdigest()


def _run_generator(repo_root):
    namespace = runpy.run_path(str(repo_root / "src" / "dh_audio_toolkit.py"))
    namespace["main"]()


def _layout_collisions(tree, margin=20.0):
    """Audit deterministic logical bounds without requiring a drawn UI."""
    scopes = {}
    for node in tree.nodes:
        if node.bl_idname == "NodeReroute":
            continue
        scopes.setdefault(node.parent.name if node.parent else None, []).append(node)

    def bounds(node):
        x = float(node.location.x)
        y = float(node.location.y)
        width = float(node.get("dh_layout_width", node.width))
        height = float(node.get("dh_layout_height", node.height))
        return x, x + width, y - height, y

    def intersects(first, second):
        return not (
            first[1] + margin <= second[0]
            or second[1] + margin <= first[0]
            or first[3] + margin <= second[2]
            or second[3] + margin <= first[2]
        )

    collisions = []
    for parent_name, nodes in scopes.items():
        for index, first_node in enumerate(nodes):
            first_bounds = bounds(first_node)
            for second_node in nodes[index + 1 :]:
                if intersects(first_bounds, bounds(second_node)):
                    collisions.append(
                        {
                            "parent": parent_name,
                            "first": first_node.name,
                            "second": second_node.name,
                        }
                    )
    return collisions


def _write_test_wav(path):
    sample_rate = 48000
    duration = 3.25
    frames = int(sample_rate * duration)
    left_frequencies = (80.0, 1000.0, 8000.0, 8000.0)
    right_frequencies = (200.0, 3000.0, 12000.0, 12000.0)

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        chunk = bytearray()
        for index in range(frames):
            time = index / sample_rate
            section = min(int(time), 3)
            local_time = time - section
            fade = min(1.0, local_time * 30.0, max(0.0, (1.0 - local_time) * 30.0))
            left = 0.72 * fade * math.sin(2.0 * math.pi * left_frequencies[section] * time)
            right = 0.58 * fade * math.sin(2.0 * math.pi * right_frequencies[section] * time)
            chunk.extend(struct.pack("<hh", int(left * 32767), int(right * 32767)))
            if len(chunk) >= 1024 * 1024:
                handle.writeframesraw(chunk)
                chunk.clear()
        if chunk:
            handle.writeframesraw(chunk)


def _new_geometry_tree(name, *, geometry_input=False):
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    if geometry_input:
        tree.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = tree.nodes
    group_in = nodes.new("NodeGroupInput") if geometry_input else None
    group_out = nodes.new("NodeGroupOutput")
    group_out.is_active_output = True
    return tree, group_in, group_out


def _group_node(tree, group_name):
    node = tree.nodes.new("GeometryNodeGroup")
    node.node_tree = bpy.data.node_groups[group_name]
    return node


def _single_point(tree):
    node = tree.nodes.new("GeometryNodeMeshLine")
    node.mode = "OFFSET"
    _set_input(node, "Count", 1)
    return node


def _store_attribute(tree, geometry_socket, value_socket, name, data_type="FLOAT"):
    store = tree.nodes.new("GeometryNodeStoreNamedAttribute")
    store.data_type = data_type
    store.domain = "POINT"
    _set_input(store, "Name", name)
    tree.links.new(geometry_socket, _socket(store.inputs, "Geometry"))
    tree.links.new(value_socket, _socket(store.inputs, "Value"))
    return store


def _synthetic_spectrum_source(tree):
    """Four bands with predictable mono/stereo fields for consumer tests."""
    source = tree.nodes.new("GeometryNodeMeshLine")
    source.mode = "OFFSET"
    _set_input(source, "Count", 4)
    index = tree.nodes.new("GeometryNodeInputIndex")

    quarter = tree.nodes.new("ShaderNodeMath")
    quarter.operation = "MULTIPLY"
    _set_input(quarter, 1, 0.25)
    amplitude = tree.nodes.new("ShaderNodeMath")
    amplitude.operation = "ADD"
    _set_input(amplitude, 1, 0.25)
    left = tree.nodes.new("ShaderNodeMath")
    left.operation = "ADD"
    _set_input(left, 1, 1.0)
    right_scale = tree.nodes.new("ShaderNodeMath")
    right_scale.operation = "MULTIPLY"
    _set_input(right_scale, 1, 10.0)
    right = tree.nodes.new("ShaderNodeMath")
    right.operation = "ADD"
    _set_input(right, 1, 10.0)

    tree.links.new(_socket(index.outputs, "Index"), _socket(quarter.inputs, 0))
    tree.links.new(_socket(quarter.outputs, "Value"), _socket(amplitude.inputs, 0))
    tree.links.new(_socket(index.outputs, "Index"), _socket(left.inputs, 0))
    tree.links.new(_socket(index.outputs, "Index"), _socket(right_scale.inputs, 0))
    tree.links.new(_socket(right_scale.outputs, "Value"), _socket(right.inputs, 0))

    current = _store_attribute(
        tree, _socket(source.outputs, "Mesh"), _socket(amplitude.outputs, "Value"),
        "dh_audio_amp",
    )
    current = _store_attribute(
        tree, _socket(current.outputs, "Geometry"), _socket(index.outputs, "Index"),
        "dh_audio_band_index", "INT",
    )
    current = _store_attribute(
        tree, _socket(current.outputs, "Geometry"), _socket(left.outputs, "Value"),
        "dh_audio_left_amp",
    )
    current = _store_attribute(
        tree, _socket(current.outputs, "Geometry"), _socket(right.outputs, "Value"),
        "dh_audio_right_amp",
    )
    return _socket(current.outputs, "Geometry")


def _new_host(name, node_tree, vertices=None, edges=None, faces=None):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices or [(0.0, 0.0, 0.0)], edges or [], faces or [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new(name="DH Regression", type="NODES")
    modifier.node_group = node_tree
    return obj


def _attribute_values(mesh, name):
    attribute = mesh.attributes.get(name)
    if attribute is None:
        return None
    values = []
    for item in attribute.data:
        if hasattr(item, "value"):
            values.append(item.value)
        elif hasattr(item, "vector"):
            values.append(tuple(item.vector))
        elif hasattr(item, "color"):
            values.append(tuple(item.color))
    return values


def _snapshot(obj, frame=None):
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    obj.update_tag()
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    try:
        return {
            "vertices": [tuple(vertex.co) for vertex in mesh.vertices],
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "attributes": {
                attribute.name: _attribute_values(mesh, attribute.name)
                for attribute in mesh.attributes
            },
        }
    finally:
        bpy.data.meshes.remove(mesh)


def _build_analyzer_wrapper(sound, output="Spectrum"):
    tree, _group_in, group_out = _new_geometry_tree("DH Test Analyzer")
    analyzer = _group_node(tree, "DH Audio Analyzer")
    _set_input(analyzer, "Sound", sound)
    tree.links.new(_socket(analyzer.outputs, output), _socket(group_out.inputs, "Geometry"))
    return tree, analyzer


def _build_stereo_wrapper(sound, output="Stereo Spectrum", bands=16):
    tree, _group_in, group_out = _new_geometry_tree(f"DH Test Stereo {output}")
    analyzer = _group_node(tree, "DH Audio Stereo Analyzer")
    _set_input(analyzer, "Sound", sound)
    _set_input(analyzer, "Bands", bands)
    tree.links.new(_socket(analyzer.outputs, output), _socket(group_out.inputs, "Geometry"))
    return tree, analyzer


def _audit_interface(report):
    report.check("Blender 5.2 or newer", bpy.app.version >= (5, 2, 0), bpy.app.version_string)
    report.check("All public groups generated", all(bpy.data.node_groups.get(name) for name in PUBLIC_GROUPS))
    report.check("All internal groups generated", all(bpy.data.node_groups.get(name) for name in INTERNAL_GROUPS))

    for name in sorted(set(PUBLIC_GROUPS) | set(INTERNAL_GROUPS)):
        tree = bpy.data.node_groups[name]
        report.check(
            f"{name}: deterministic readable layout",
            tree.get("dh_layout_version") == 1,
            tree.get("dh_layout_version"),
        )
        collisions = _layout_collisions(tree)
        report.check(
            f"{name}: no internal node/frame overlaps",
            not collisions,
            collisions,
        )

    asset_names = {tree.name for tree in bpy.data.node_groups if tree.asset_data}
    report.check("Exactly 25 public assets", asset_names == set(PUBLIC_GROUPS), sorted(asset_names))

    for name, (tree_type, width, catalog) in PUBLIC_GROUPS.items():
        tree = bpy.data.node_groups[name]
        report.check(f"{name}: node-tree type", tree.bl_idname == tree_type, tree.bl_idname)
        report.check(f"{name}: default width", abs(tree.default_group_node_width - width) < 0.01, tree.default_group_node_width)
        actual_catalog = str(tree.asset_data.catalog_id) if tree.asset_data else None
        report.check(f"{name}: stable catalog", actual_catalog == catalog, actual_catalog)

        for item in tree.interface.items_tree:
            if item.item_type == "SOCKET":
                report.check(f"{name}: readable socket {item.identifier}", bool(item.name.strip()), item.name)

        host_type = "GeometryNodeTree" if tree_type == "GeometryNodeTree" else "ShaderNodeTree"
        group_node_type = "GeometryNodeGroup" if tree_type == "GeometryNodeTree" else "ShaderNodeGroup"
        host = bpy.data.node_groups.new("DH Test Menu Host", host_type)
        try:
            group_node = host.nodes.new(group_node_type)
            group_node.node_tree = tree
            for socket in group_node.inputs:
                if socket.bl_idname == "NodeSocketMenu":
                    report.check(f"{name}: {socket.name} menu default", bool(socket.default_value), socket.default_value)
        finally:
            bpy.data.node_groups.remove(host)

    for name, expected in EXPECTED_PANELS.items():
        tree = bpy.data.node_groups[name]
        actual = {
            item.name: bool(item.default_closed)
            for item in tree.interface.items_tree
            if item.item_type == "PANEL"
        }
        report.check(f"{name}: panel organization", actual == expected, actual)

    defaults = {
        ("DH Audio Analyzer", "FFT Size"): "8192",
        ("DH Audio Analyzer", "Window Function"): "Hann",
        ("DH Audio Stereo Analyzer", "FFT Size"): "8192",
        ("DH Audio Stereo Analyzer", "Window Function"): "Hann",
        ("DH Audio Stereo Analyzer", "Bands"): 32,
        ("DH Audio Stereo Analyzer", "Spacing"): 1.0,
        ("DH Audio Stereo Analyzer", "Channel Spacing"): 1.0,
        ("DH Audio Spectrum Sample", "Band"): 0,
        ("DH Audio Spectrum Bridge", "Band"): 0,
        ("DH Audio Spectrum Bridge", "Selection"): True,
        ("DH Audio Spectrum Bridge", "Store on Points"): True,
        ("DH Audio Spectrum Bridge", "Store on Instances"): True,
        ("DH Audio Mesh Deform", "Audio Source"): "Amplitude",
        ("DH Audio Mesh Deform", "Use Normals"): True,
        ("DH Audio Mesh Deform", "Direction"): [0.0, 0.0, 1.0],
        ("DH Audio Mesh Deform", "Strength"): 1.0,
        ("DH Audio Mesh Deform", "Center"): 0.0,
        ("DH Audio Mesh Deform", "Store on Points"): True,
        ("DH Audio Mesh Deform", "Store on Instances"): False,
        ("DH Audio Mesh Extrude", "Audio Source"): "Amplitude",
        ("DH Audio Mesh Extrude", "Use Normals"): True,
        ("DH Audio Mesh Extrude", "Direction"): [0.0, 0.0, 1.0],
        ("DH Audio Mesh Extrude", "Strength"): 1.0,
        ("DH Audio Mesh Extrude", "Center"): 0.0,
        ("DH Audio Mesh Extrude", "Base Top Scale"): 1.0,
        ("DH Audio Mesh Extrude", "Audio Top Scale"): 0.0,
        ("DH Audio Spectrum Bars", "Bar Profile"): "Box",
        ("DH Audio Spectrum Curve", "Curve Style"): "Smooth",
        ("DH Audio Response", "Gain"): 1.0,
        ("DH Audio Response", "Floor"): 0.0,
        ("DH Audio Response", "Ceiling"): 0.8,
        ("DH Audio Response", "Clamp to 1"): True,
        ("DH Audio Response", "Response"): 0.7,
        ("DH Audio Temporal Response", "Attack"): 0.05,
        ("DH Audio Temporal Response", "Release"): 0.25,
        ("DH Audio Temporal Response", "Peak Hold"): True,
        ("DH Audio Temporal Response", "Peak Hold Time"): 0.2,
        ("DH Audio Temporal Response", "Peak Decay"): 0.5,
        ("DH Audio Spectrum History", "Frames"): 32,
        ("DH Audio Spectrum History", "History Offset"): [0.0, -0.15, 0.0],
        ("DH Audio Spectrum History", "Reset"): False,
        ("DH Audio Radial Spectrum", "Radius"): 3.0,
        ("DH Audio Radial Spectrum", "Audio Radius"): 1.5,
        ("DH Audio Radial Spectrum", "Spiral"): 0.0,
        ("DH Audio Radial Spectrum", "Height Scale"): 1.0,
        ("DH Audio Radial Spectrum", "Center"): [0.0, 0.0, 0.0],
        ("DH Audio Radial Spectrum", "Start Angle"): 0.0,
        ("DH Audio Radial Spectrum", "Sweep Angle"): math.tau,
        ("DH Audio Radial Spectrum", "Cyclic"): True,
        ("DH Audio Stereo Points", "Height"): 3.0,
        ("DH Audio Stereo Points", "Baseline"): 0.0,
        ("DH Audio Stereo Points", "Center Spectrum"): True,
        ("DH Audio Shader Response", "Gain"): 1.0,
        ("DH Audio Shader Response", "Floor"): 0.0,
        ("DH Audio Shader Response", "Ceiling"): 0.8,
        ("DH Audio Shader Response", "Clamp to 1"): True,
        ("DH Audio Shader Response", "Response"): 0.7,
        ("DH Audio Material Reader", "Use Instancer"): False,
        ("DH Audio Shader Map", "From Min"): 0.0,
        ("DH Audio Shader Map", "From Max"): 1.0,
        ("DH Audio Shader Map", "To Min"): 0.0,
        ("DH Audio Shader Map", "To Max"): 1.0,
        ("DH Audio Shader Map", "Invert"): False,
        ("DH Audio Shader Map", "Clamp"): True,
        ("DH Audio Shader Map", "Curve"): 1.0,
        ("DH Audio Shader UV Transform", "Factor"): 0.0,
        ("DH Audio Shader UV Transform", "Pivot"): [0.5, 0.5, 0.0],
        ("DH Audio Shader UV Transform", "Base Offset"): [0.0, 0.0, 0.0],
        ("DH Audio Shader UV Transform", "Audio Offset"): [0.1, 0.0, 0.0],
        ("DH Audio Shader UV Transform", "Base Scale"): [1.0, 1.0, 1.0],
        ("DH Audio Shader UV Transform", "Audio Scale"): [0.0, 0.0, 0.0],
        ("DH Audio Shader UV Transform", "Base Rotation"): 0.0,
        ("DH Audio Shader UV Transform", "Audio Rotation"): 0.0,
    }
    for (group_name, socket_name), expected in defaults.items():
        item = _interface_socket(bpy.data.node_groups[group_name], socket_name)
        actual = _default_value(item)
        if isinstance(expected, float):
            equal = abs(actual - expected) < 1e-5
        elif isinstance(expected, (list, tuple)):
            equal = (
                isinstance(actual, (list, tuple))
                and len(actual) == len(expected)
                and all(abs(a - b) < 1e-5 for a, b in zip(actual, expected))
            )
        else:
            equal = actual == expected
        report.check(f"{group_name}: {socket_name} default", equal, actual)

    spectrum_sample = bpy.data.node_groups["DH Audio Spectrum Sample"]
    sample_band = _interface_socket(spectrum_sample, "Band", "INPUT")
    sample_outputs = [
        item for item in spectrum_sample.interface.items_tree
        if item.item_type == "SOCKET" and item.in_out == "OUTPUT"
    ]
    report.check(
        "Spectrum Sample Band is a field input",
        sample_band.structure_type == "FIELD",
        sample_band.structure_type,
    )
    report.check(
        "Spectrum Sample outputs are fields",
        sample_outputs and all(item.structure_type == "FIELD" for item in sample_outputs),
        {item.name: item.structure_type for item in sample_outputs},
    )

    spectrum_bridge = bpy.data.node_groups["DH Audio Spectrum Bridge"]
    bridge_band = _interface_socket(spectrum_bridge, "Band", "INPUT")
    bridge_selection = _interface_socket(spectrum_bridge, "Selection", "INPUT")
    bridge_geometry = _interface_socket(spectrum_bridge, "Geometry", "OUTPUT")
    bridge_field_outputs = [
        item for item in spectrum_bridge.interface.items_tree
        if item.item_type == "SOCKET"
        and item.in_out == "OUTPUT"
        and item.name != "Geometry"
    ]
    report.check(
        "Spectrum Bridge Band and Selection are field inputs",
        bridge_band.structure_type == "FIELD"
        and bridge_selection.structure_type == "FIELD",
        {
            "Band": bridge_band.structure_type,
            "Selection": bridge_selection.structure_type,
        },
    )
    report.check(
        "Spectrum Bridge geometry is a single value and sampled outputs are fields",
        bridge_geometry.structure_type == "SINGLE"
        and bridge_field_outputs
        and all(item.structure_type == "FIELD" for item in bridge_field_outputs),
        {
            "Geometry": bridge_geometry.structure_type,
            "fields": {item.name: item.structure_type for item in bridge_field_outputs},
        },
    )

    for group_name, geometry_name in (
        ("DH Audio Mesh Deform", "Geometry"),
        ("DH Audio Mesh Extrude", "Mesh"),
    ):
        effect = bpy.data.node_groups[group_name]
        band = _interface_socket(effect, "Band", "INPUT")
        selection = _interface_socket(effect, "Selection", "INPUT")
        geometry_output = _interface_socket(effect, geometry_name, "OUTPUT")
        field_outputs = [
            item for item in effect.interface.items_tree
            if item.item_type == "SOCKET"
            and item.in_out == "OUTPUT"
            and item.name != geometry_name
        ]
        report.check(
            f"{group_name}: mapping inputs and diagnostic outputs use fields",
            band.structure_type == "FIELD"
            and selection.structure_type == "FIELD"
            and geometry_output.structure_type == "SINGLE"
            and field_outputs
            and all(item.structure_type == "FIELD" for item in field_outputs),
            {
                "Band": band.structure_type,
                "Selection": selection.structure_type,
                "Geometry": geometry_output.structure_type,
                "outputs": {item.name: item.structure_type for item in field_outputs},
            },
        )

    boolean_inputs = {
        ("DH Audio Analyzer", "Use Scene Time"),
        ("DH Audio Analyzer", "All Channels"),
        ("DH Audio Analyzer", "Logarithmic"),
        ("DH Audio Analyzer", "Clamp to 1"),
        ("DH Audio Stereo Analyzer", "Use Scene Time"),
        ("DH Audio Stereo Analyzer", "Logarithmic"),
        ("DH Audio Stereo Analyzer", "Clamp to 1"),
        ("DH Audio Bands", "Store on Points"),
        ("DH Audio Bands", "Store on Instances"),
        ("DH Audio Spectrum Bridge", "Selection"),
        ("DH Audio Spectrum Bridge", "Store on Points"),
        ("DH Audio Spectrum Bridge", "Store on Instances"),
        ("DH Audio Mesh Deform", "Selection"),
        ("DH Audio Mesh Deform", "Use Normals"),
        ("DH Audio Mesh Deform", "Store on Points"),
        ("DH Audio Mesh Deform", "Store on Instances"),
        ("DH Audio Mesh Extrude", "Selection"),
        ("DH Audio Mesh Extrude", "Use Normals"),
        ("DH Audio Spectrum Instances", "Realize Instances"),
        ("DH Audio Material Reader", "Use Instancer"),
        ("DH Audio Shader Response", "Clamp to 1"),
        ("DH Audio Shader Map", "Invert"),
        ("DH Audio Shader Map", "Clamp"),
        ("DH Audio Spectrum History", "Reset"),
        ("DH Audio Radial Spectrum", "Cyclic"),
        ("DH Audio Stereo Points", "Center Spectrum"),
    }
    for group_name, socket_name in boolean_inputs:
        item = _interface_socket(bpy.data.node_groups[group_name], socket_name)
        report.check(f"{group_name}: {socket_name} is Boolean", item.socket_type == "NodeSocketBool", item.socket_type)

    for group_name in (
        "DH Audio Analyzer",
        "DH Audio Stereo Analyzer",
        "DH Audio Bands",
        "DH Audio Sample Range",
        "DH Audio Spectrum Bars",
    ):
        sound = _interface_socket(bpy.data.node_groups[group_name], "Sound")
        report.check(
            f"{group_name}: Sound is documented as required",
            "Required" in sound.description and "zero amplitude" in sound.description,
            sound.description,
        )

    instancer = _interface_socket(bpy.data.node_groups["DH Audio Material Reader"], "Use Instancer")
    report.check(
        "Material Reader explains geometry versus instancer lookup",
        "realized" in instancer.description and "instancer" in instancer.description,
        instancer.description,
    )


def _evaluate_shader_math_input(socket, group_values):
    if socket.is_linked:
        return _evaluate_shader_math_output(socket.links[0].from_socket, group_values)
    return float(socket.default_value)


def _evaluate_shader_math_output(socket, group_values):
    node = socket.node
    if node.type == "GROUP_INPUT":
        return float(group_values[socket.name])
    if node.bl_idname != "ShaderNodeMath":
        raise TypeError(f"Unsupported shader test node: {node.bl_idname}")

    values = [_evaluate_shader_math_input(input_socket, group_values) for input_socket in node.inputs]
    a = values[0]
    b = values[1] if len(values) > 1 else 0.0
    operations = {
        "ADD": lambda: a + b,
        "SUBTRACT": lambda: a - b,
        "MULTIPLY": lambda: a * b,
        "DIVIDE": lambda: a / b if b != 0.0 else 0.0,
        "POWER": lambda: math.pow(a, b),
        "ABSOLUTE": lambda: abs(a),
        "SIGN": lambda: 1.0 if a > 0.0 else (-1.0 if a < 0.0 else 0.0),
        "MINIMUM": lambda: min(a, b),
        "MAXIMUM": lambda: max(a, b),
    }
    if node.operation not in operations:
        raise ValueError(f"Unsupported shader test operation: {node.operation}")
    return operations[node.operation]()


def _test_shader_map(report):
    tree = bpy.data.node_groups["DH Audio Shader Map"]
    output = next(node for node in tree.nodes if node.type == "GROUP_OUTPUT" and node.is_active_output)
    defaults = {
        "Value": 0.0,
        "From Min": 0.0,
        "From Max": 1.0,
        "To Min": 0.0,
        "To Max": 1.0,
        "Invert": 0.0,
        "Clamp": 1.0,
        "Curve": 1.0,
    }
    cases = [
        ("linear default", {"Value": 0.25}, 0.25, 0.25),
        ("invert", {"Value": 0.25, "Invert": 1.0}, 0.75, 0.75),
        ("curve and output range", {"Value": 0.5, "To Min": 2.0, "To Max": 6.0, "Curve": 2.0}, 3.0, 0.25),
        ("clamp high", {"Value": 2.0}, 1.0, 1.0),
        ("sign-safe unclamped curve", {"Value": -0.5, "Clamp": 0.0, "Curve": 2.0}, -0.25, -0.25),
        ("custom source range", {"Value": 15.0, "From Min": 10.0, "From Max": 20.0}, 0.5, 0.5),
    ]
    for label, changes, expected_value, expected_factor in cases:
        values = defaults | changes
        actual_value = _evaluate_shader_math_input(_socket(output.inputs, "Value"), values)
        actual_factor = _evaluate_shader_math_input(_socket(output.inputs, "Factor"), values)
        report.check(
            f"Shader Map {label}",
            abs(actual_value - expected_value) < 1e-6 and abs(actual_factor - expected_factor) < 1e-6,
            {"value": actual_value, "factor": actual_factor},
        )


def _evaluate_shader_value_input(socket, group_values):
    if socket.is_linked:
        return _evaluate_shader_value_output(socket.links[0].from_socket, group_values)
    value = socket.default_value
    if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        return tuple(float(component) for component in value)
    return float(value)


def _evaluate_shader_value_output(socket, group_values):
    node = socket.node
    if node.type == "GROUP_INPUT":
        return group_values[socket.name]
    if node.bl_idname == "ShaderNodeMath":
        values = [_evaluate_shader_value_input(item, group_values) for item in node.inputs]
        a, b = values[0], values[1]
        if node.operation == "ADD":
            return a + b
        if node.operation == "MULTIPLY":
            return a * b
        raise ValueError(f"Unsupported UV test math operation: {node.operation}")
    if node.bl_idname == "ShaderNodeVectorMath":
        a = _evaluate_shader_value_input(node.inputs[0], group_values)
        b = _evaluate_shader_value_input(node.inputs[1], group_values)
        if node.operation == "ADD":
            return tuple(x + y for x, y in zip(a, b))
        if node.operation == "SUBTRACT":
            return tuple(x - y for x, y in zip(a, b))
        if node.operation == "MULTIPLY":
            return tuple(x * y for x, y in zip(a, b))
        if node.operation == "SCALE":
            scale = _evaluate_shader_value_input(node.inputs[3], group_values)
            return tuple(x * scale for x in a)
        raise ValueError(f"Unsupported UV test vector operation: {node.operation}")
    if node.bl_idname == "ShaderNodeVectorRotate":
        vector = _evaluate_shader_value_input(_socket(node.inputs, "Vector"), group_values)
        center = _evaluate_shader_value_input(_socket(node.inputs, "Center"), group_values)
        axis = _evaluate_shader_value_input(_socket(node.inputs, "Axis"), group_values)
        angle = _evaluate_shader_value_input(_socket(node.inputs, "Angle"), group_values)
        if node.rotation_type != "AXIS_ANGLE" or any(
            abs(actual - expected) > 1e-6 for actual, expected in zip(axis, (0.0, 0.0, 1.0))
        ):
            raise ValueError("UV test evaluator supports the generated Z axis-angle rotation")
        x, y, z = (vector[i] - center[i] for i in range(3))
        cosine, sine = math.cos(angle), math.sin(angle)
        return (
            x * cosine - y * sine + center[0],
            x * sine + y * cosine + center[1],
            z + center[2],
        )
    raise TypeError(f"Unsupported UV test node: {node.bl_idname}")


def _test_shader_uv_transform(report):
    tree = bpy.data.node_groups["DH Audio Shader UV Transform"]
    output = next(node for node in tree.nodes if node.type == "GROUP_OUTPUT" and node.is_active_output)
    values = {
        "Vector": (1.0, 0.5, 0.0),
        "Factor": 2.0,
        "Pivot": (0.5, 0.5, 0.0),
        "Base Offset": (0.1, 0.2, 0.0),
        "Audio Offset": (0.05, 0.0, 0.0),
        "Base Scale": (1.0, 1.0, 1.0),
        "Audio Scale": (0.5, 0.0, 0.0),
        "Base Rotation": 0.0,
        "Audio Rotation": math.pi / 4.0,
    }
    actual = {
        name: _evaluate_shader_value_input(_socket(output.inputs, name), values)
        for name in ("Vector", "Offset", "Scale", "Rotation")
    }
    expected = {
        "Vector": (0.7, 1.7, 0.0),
        "Offset": (0.2, 0.2, 0.0),
        "Scale": (2.0, 1.0, 1.0),
        "Rotation": math.pi / 2.0,
    }

    def close(first, second):
        if isinstance(second, tuple):
            return all(abs(a - b) < 1e-6 for a, b in zip(first, second))
        return abs(first - second) < 1e-6

    report.check(
        "Shader UV Transform offset, pivot scale, and rotation",
        all(close(actual[name], expected[name]) for name in expected),
        actual,
    )


def _test_analyzer(report, sound):
    tree, analyzer = _build_analyzer_wrapper(sound)
    obj = _new_host("DH Test Analyzer Host", tree)
    frames = {}
    for frame in (10, 40, 70):
        snapshot = _snapshot(obj, frame)
        amplitudes = snapshot["attributes"].get("dh_audio_amp") or []
        frames[frame] = {
            "vertices": len(snapshot["vertices"]),
            "edges": snapshot["edges"],
            "peak_band": max(range(len(amplitudes)), key=amplitudes.__getitem__),
            "peak": max(amplitudes),
            "sum": sum(amplitudes),
        }
        report.check(f"Analyzer frame {frame}: 32-band carrier", len(snapshot["vertices"]) == 32 and snapshot["edges"] == 31, frames[frame])
        report.check(f"Analyzer frame {frame}: spectrum attributes", all(name in snapshot["attributes"] for name in SPECTRUM_ATTRIBUTES), sorted(snapshot["attributes"]))
        report.check(f"Analyzer frame {frame}: nonzero audio", bool(amplitudes) and max(amplitudes) > 1e-5, max(amplitudes) if amplitudes else None)

    peaks = [frames[frame]["peak_band"] for frame in (10, 40, 70)]
    report.check("Analyzer peak moves low to mid to high", peaks[0] < peaks[1] < peaks[2], peaks)

    _set_input(analyzer, "All Channels", False)
    _set_input(analyzer, "Channel", 0)
    left = _snapshot(obj, 10)["attributes"]["dh_audio_amp"]
    _set_input(analyzer, "Channel", 1)
    right = _snapshot(obj, 10)["attributes"]["dh_audio_amp"]
    channel_delta = sum(abs(a - b) for a, b in zip(left, right))
    report.check("Analyzer channel selection changes values", channel_delta > 1e-4, channel_delta)

    _set_input(analyzer, "All Channels", True)
    _set_input(analyzer, "Use Scene Time", False)
    _set_input(analyzer, "Time", 1.55)
    custom = _snapshot(obj, 10)["attributes"]["dh_audio_amp"]
    custom_peak = max(range(len(custom)), key=custom.__getitem__)
    report.check("Analyzer custom Time overrides scene frame", custom_peak > peaks[0], {"scene_peak": peaks[0], "custom_peak": custom_peak})

    report.observations["analyzer_frames"] = frames


def _test_stereo_analyzer(report, sound):
    bands = 16
    tree, analyzer = _build_stereo_wrapper(sound, bands=bands)
    obj = _new_host("DH Test Stereo Analyzer Host", tree)
    snapshot = _snapshot(obj, 10)
    attrs = snapshot["attributes"]

    channels = attrs.get("dh_audio_channel", [])
    channel_positions = attrs.get("dh_audio_channel_pos", [])
    band_indices = attrs.get("dh_audio_band_index", [])
    amplitude = attrs.get("dh_audio_amp", [])
    left_amplitude = attrs.get("dh_audio_left_amp", [])
    right_amplitude = attrs.get("dh_audio_right_amp", [])

    report.check(
        "Stereo Analyzer creates two independent carrier rows",
        len(snapshot["vertices"]) == bands * 2 and snapshot["edges"] == (bands - 1) * 2,
        {"vertices": len(snapshot["vertices"]), "edges": snapshot["edges"]},
    )
    report.check(
        "Stereo Analyzer stores all stereo attributes",
        all(name in attrs for name in STEREO_ATTRIBUTES),
        sorted(attrs),
    )
    report.check(
        "Stereo Analyzer channel metadata is ordered Left then Right",
        channels == [0] * bands + [1] * bands
        and channel_positions == [-1.0] * bands + [1.0] * bands
        and band_indices == list(range(bands)) * 2,
        {"channels": channels, "positions": channel_positions, "bands": band_indices},
    )
    report.check(
        "Stereo Analyzer paired attributes repeat by matching band",
        all(abs(left_amplitude[i] - left_amplitude[i + bands]) < 1e-6 for i in range(bands))
        and all(abs(right_amplitude[i] - right_amplitude[i + bands]) < 1e-6 for i in range(bands)),
    )
    report.check(
        "Stereo Analyzer standard amplitude follows each point's channel",
        all(abs(amplitude[i] - left_amplitude[i]) < 1e-6 for i in range(bands))
        and all(abs(amplitude[i + bands] - right_amplitude[i + bands]) < 1e-6 for i in range(bands)),
    )
    left_peak = max(range(bands), key=lambda i: left_amplitude[i])
    right_peak = max(range(bands), key=lambda i: right_amplitude[i])
    report.check(
        "Stereo Analyzer separates distinct Left and Right spectra",
        left_peak != right_peak and sum(abs(left_amplitude[i] - right_amplitude[i]) for i in range(bands)) > 1e-4,
        {"left_peak": left_peak, "right_peak": right_peak},
    )

    stereo_tree = bpy.data.node_groups["DH Audio Stereo Analyzer"]
    sample_nodes = [node for node in stereo_tree.nodes if node.bl_idname == "GeometryNodeSampleSoundFrequencies"]
    report.check(
        "Stereo Analyzer uses one field-driven Sample Sound node",
        len(sample_nodes) == 1 and _socket(sample_nodes[0].inputs, "Channel").is_linked,
        [node.name for node in sample_nodes],
    )

    for output_name, expected_channel in (("Left Spectrum", 0), ("Right Spectrum", 1)):
        output_tree, _node = _build_stereo_wrapper(sound, output=output_name, bands=bands)
        output_obj = _new_host(f"DH Test {output_name} Host", output_tree)
        output_snapshot = _snapshot(output_obj, 10)
        report.check(
            f"Stereo Analyzer {output_name} is a mono-compatible carrier",
            len(output_snapshot["vertices"]) == bands
            and output_snapshot["edges"] == bands - 1
            and output_snapshot["attributes"].get("dh_audio_channel") == [expected_channel] * bands,
            {"vertices": len(output_snapshot["vertices"]), "edges": output_snapshot["edges"]},
        )

    points_tree, _group_in, points_out = _new_geometry_tree("DH Test Mirrored Stereo Points")
    points_analyzer = _group_node(points_tree, "DH Audio Stereo Analyzer")
    _set_input(points_analyzer, "Sound", sound)
    _set_input(points_analyzer, "Bands", bands)
    stereo_points = _group_node(points_tree, "DH Audio Stereo Points")
    points_tree.links.new(_socket(points_analyzer.outputs, "Left Spectrum"), _socket(stereo_points.inputs, "Left Spectrum"))
    points_tree.links.new(_socket(points_analyzer.outputs, "Right Spectrum"), _socket(stereo_points.inputs, "Right Spectrum"))
    points_tree.links.new(_socket(stereo_points.outputs, "Mirrored Points"), _socket(points_out.inputs, "Geometry"))
    points_obj = _new_host("DH Test Mirrored Stereo Points Host", points_tree)
    points_snapshot = _snapshot(points_obj, 10)
    point_channels = points_snapshot["attributes"].get("dh_audio_channel", [])
    left_z = [co[2] for co, channel_value in zip(points_snapshot["vertices"], point_channels) if channel_value == 0]
    right_z = [co[2] for co, channel_value in zip(points_snapshot["vertices"], point_channels) if channel_value == 1]
    report.check(
        "Stereo Points mirrors Left above and Right below the baseline",
        min(left_z) >= -1e-6 and max(left_z) > 1e-4
        and max(right_z) <= 1e-6 and min(right_z) < -1e-4,
        {"left": [min(left_z), max(left_z)], "right": [min(right_z), max(right_z)]},
    )
    report.check(
        "Stereo Points preserves stereo and spectrum attributes",
        all(name in points_snapshot["attributes"] for name in (*SPECTRUM_ATTRIBUTES, *STEREO_ATTRIBUTES)),
        sorted(points_snapshot["attributes"]),
    )

    fill_tree, _fill_in, fill_out = _new_geometry_tree("DH Test Stereo Fill")
    fill_analyzer = _group_node(fill_tree, "DH Audio Stereo Analyzer")
    _set_input(fill_analyzer, "Sound", sound)
    _set_input(fill_analyzer, "Bands", bands)
    fill_points = _group_node(fill_tree, "DH Audio Stereo Points")
    fill = _group_node(fill_tree, "DH Audio Spectrum Fill")
    fill_tree.links.new(_socket(fill_analyzer.outputs, "Left Spectrum"), _socket(fill_points.inputs, "Left Spectrum"))
    fill_tree.links.new(_socket(fill_analyzer.outputs, "Right Spectrum"), _socket(fill_points.inputs, "Right Spectrum"))
    fill_tree.links.new(_socket(fill_points.outputs, "Left Points"), _socket(fill.inputs, "Spectrum Points"))
    fill_tree.links.new(_socket(fill.outputs, "Mesh"), _socket(fill_out.inputs, "Geometry"))
    fill_obj = _new_host("DH Test Stereo Fill Host", fill_tree)
    fill_snapshot = _snapshot(fill_obj, 10)
    report.check(
        "Spectrum Fill preserves paired stereo attributes",
        all(name in fill_snapshot["attributes"] for name in STEREO_ATTRIBUTES)
        and set(fill_snapshot["attributes"].get("dh_audio_channel", [])) == {0},
        sorted(fill_snapshot["attributes"]),
    )

    report.observations["stereo"] = {
        "bands_per_channel": bands,
        "left_peak": left_peak,
        "right_peak": right_peak,
        "mirrored_z": {"left": [min(left_z), max(left_z)], "right": [min(right_z), max(right_z)]},
    }


def _test_temporal_response(report):
    tree, _group_in, group_out = _new_geometry_tree("DH Test Temporal Response")
    line = tree.nodes.new("GeometryNodeMeshLine")
    line.mode = "OFFSET"
    _set_input(line, "Count", 1)

    scene_time = tree.nodes.new("GeometryNodeInputSceneTime")
    after_start = tree.nodes.new("ShaderNodeMath")
    after_start.operation = "GREATER_THAN"
    _set_input(after_start, 1, 10.0)
    before_end = tree.nodes.new("ShaderNodeMath")
    before_end.operation = "LESS_THAN"
    _set_input(before_end, 1, 20.0)
    pulse = tree.nodes.new("ShaderNodeMath")
    pulse.operation = "MULTIPLY"
    tree.links.new(_socket(scene_time.outputs, "Frame"), _socket(after_start.inputs, 0))
    tree.links.new(_socket(scene_time.outputs, "Frame"), _socket(before_end.inputs, 0))
    tree.links.new(_socket(after_start.outputs, "Value"), _socket(pulse.inputs, 0))
    tree.links.new(_socket(before_end.outputs, "Value"), _socket(pulse.inputs, 1))

    source = _store_attribute(
        tree,
        _socket(line.outputs, "Mesh"),
        _socket(pulse.outputs, "Value"),
        "dh_audio_amp",
    )
    metadata = tree.nodes.new("GeometryNodeStoreNamedAttribute")
    metadata.data_type = "INT"
    metadata.domain = "POINT"
    _set_input(metadata, "Name", "dh_test_metadata")
    _set_input(metadata, "Value", 42)
    tree.links.new(_socket(source.outputs, "Geometry"), _socket(metadata.inputs, "Geometry"))

    temporal = _group_node(tree, "DH Audio Temporal Response")
    _set_input(temporal, "Attack", 0.1)
    _set_input(temporal, "Release", 0.4)
    _set_input(temporal, "Peak Hold Time", 0.2)
    _set_input(temporal, "Peak Decay", 0.2)
    tree.links.new(_socket(metadata.outputs, "Geometry"), _socket(temporal.inputs, "Spectrum"))
    output_store = _store_attribute(
        tree,
        _socket(temporal.outputs, "Spectrum"),
        _socket(temporal.outputs, "Amplitude"),
        "dh_test_temporal_output",
    )
    peak_output_store = _store_attribute(
        tree,
        _socket(output_store.outputs, "Geometry"),
        _socket(temporal.outputs, "Peak"),
        "dh_test_peak_output",
    )
    tree.links.new(_socket(peak_output_store.outputs, "Geometry"), _socket(group_out.inputs, "Geometry"))

    obj = _new_host("DH Test Temporal Response Host", tree)
    values = {}
    peaks = {}
    metadata_preserved = True
    output_field_matches = True
    peak_output_matches = True
    for frame in range(1, 31):
        snapshot = _snapshot(obj, frame)
        values[frame] = snapshot["attributes"]["dh_audio_amp"][0]
        peaks[frame] = snapshot["attributes"]["dh_audio_peak"][0]
        metadata_preserved = (
            metadata_preserved
            and snapshot["attributes"].get("dh_test_metadata") == [42]
        )
        output_field_matches = (
            output_field_matches
            and abs(
                snapshot["attributes"]["dh_test_temporal_output"][0]
                - values[frame]
            ) < 1e-6
        )
        peak_output_matches = (
            peak_output_matches
            and abs(
                snapshot["attributes"]["dh_test_peak_output"][0]
                - peaks[frame]
            ) < 1e-6
        )

    expected_first_rise = 1.0 - math.exp(-(1.0 / 24.0) / 0.1)
    report.check(
        "Temporal Response attack follows exponential time constant",
        (
            abs(values[11] - expected_first_rise) < 1e-4
            and values[11] < values[12] < values[19] < 1.0
        ),
        {
            "expected_frame_11": expected_first_rise,
            "actual_frame_11": values[11],
            "frame_12": values[12],
            "frame_19": values[19],
        },
    )
    report.check(
        "Temporal Response release is slower than attack",
        0.0 < values[30] < values[20] < values[19],
        {"frame_19": values[19], "frame_20": values[20], "frame_30": values[30]},
    )
    report.check("Temporal Response preserves current metadata", metadata_preserved)
    report.check("Temporal Response Amplitude output matches stored attribute", output_field_matches)
    report.check("Temporal Response Peak output matches stored attribute", peak_output_matches)
    report.check(
        "Temporal Response peak holds before decaying toward live amplitude",
        (
            abs(peaks[19] - values[19]) < 1e-6
            and abs(peaks[23] - peaks[19]) < 1e-6
            and values[23] < peaks[23]
            and values[30] < peaks[30] < peaks[23]
        ),
        {
            "peak_19": peaks[19],
            "peak_23": peaks[23],
            "peak_30": peaks[30],
            "amplitude_23": values[23],
            "amplitude_30": values[30],
        },
    )

    sample_previous = bpy.data.node_groups["DH Audio Temporal Response"].nodes.get("Sample Previous Band")
    report.check(
        "Temporal Response does not clamp new band indices",
        sample_previous is not None and sample_previous.bl_idname == "GeometryNodeSampleIndex" and not sample_previous.clamp,
        None if sample_previous is None else sample_previous.clamp,
    )

    _set_input(temporal, "Peak Hold", False)
    disabled_matches_live = True
    for frame in range(1, 21):
        snapshot = _snapshot(obj, frame)
        disabled_matches_live = disabled_matches_live and abs(
            snapshot["attributes"]["dh_audio_peak"][0]
            - snapshot["attributes"]["dh_audio_amp"][0]
        ) < 1e-6
    report.check(
        "Temporal Response disabled Peak Hold preserves live amplitude as Peak",
        disabled_matches_live,
    )

    _set_input(temporal, "Attack", 0.0)
    _set_input(temporal, "Release", 0.0)
    zero_values = {}
    for frame in range(1, 21):
        zero_values[frame] = _snapshot(obj, frame)["attributes"]["dh_audio_amp"][0]
    report.check(
        "Temporal Response zero times are immediate and finite",
        (
            zero_values[10] == 0.0
            and zero_values[11] == 1.0
            and zero_values[19] == 1.0
            and zero_values[20] == 0.0
            and all(math.isfinite(value) for value in zero_values.values())
        ),
        {frame: zero_values[frame] for frame in (10, 11, 19, 20)},
    )

    report.observations["temporal_response"] = {
        "attack_seconds": 0.1,
        "release_seconds": 0.4,
        "frame_11": values[11],
        "frame_12": values[12],
        "frame_19": values[19],
        "frame_20": values[20],
        "frame_30": values[30],
        "peak_19": peaks[19],
        "peak_23": peaks[23],
        "peak_30": peaks[30],
        "timeline_requirement": "Play sequentially or bake/cache; an uncached forward jump advances one simulation step.",
    }


def _test_spectrum_history(report):
    def build_host(name, frames, *, reset_frame=None, varying_topology=False, store_outputs=False, surface=False, row_decimation=1):
        tree, _group_in, group_out = _new_geometry_tree(name)
        line = tree.nodes.new("GeometryNodeMeshLine")
        line.mode = "OFFSET"
        _set_input(line, "Start Location", (0.0, 0.0, 0.0))
        _set_input(line, "Offset", (1.0, 0.0, 0.0))

        scene_time = tree.nodes.new("GeometryNodeInputSceneTime")
        if varying_topology:
            after_change = tree.nodes.new("FunctionNodeCompare")
            after_change.data_type = "INT"
            after_change.operation = "GREATER_EQUAL"
            _set_input(after_change, "B", 5)
            tree.links.new(_socket(scene_time.outputs, "Frame"), _socket(after_change.inputs, "A"))

            count_switch = tree.nodes.new("GeometryNodeSwitch")
            count_switch.input_type = "INT"
            _set_input(count_switch, "False", 3)
            _set_input(count_switch, "True", 5)
            tree.links.new(_socket(after_change.outputs, "Result"), _socket(count_switch.inputs, "Switch"))
            tree.links.new(_socket(count_switch.outputs, "Output"), _socket(line.inputs, "Count"))
        else:
            _set_input(line, "Count", 3)

        amplitude = _store_attribute(
            tree,
            _socket(line.outputs, "Mesh"),
            _socket(scene_time.outputs, "Frame"),
            "dh_audio_amp",
        )
        index = tree.nodes.new("GeometryNodeInputIndex")
        band_index = _store_attribute(
            tree,
            _socket(amplitude.outputs, "Geometry"),
            _socket(index.outputs, "Index"),
            "dh_audio_band_index",
            "INT",
        )

        history = _group_node(tree, "DH Audio Spectrum History")
        _set_input(history, "Frames", frames)
        _set_input(history, "History Offset", (0.0, -1.0, 0.0))
        _set_input(history, "Surface", surface)
        _set_input(history, "Row Decimation", row_decimation)
        tree.links.new(_socket(band_index.outputs, "Geometry"), _socket(history.inputs, "Spectrum Points"))

        if reset_frame is not None:
            reset = tree.nodes.new("FunctionNodeCompare")
            reset.data_type = "INT"
            reset.operation = "EQUAL"
            _set_input(reset, "B", reset_frame)
            tree.links.new(_socket(scene_time.outputs, "Frame"), _socket(reset.inputs, "A"))
            tree.links.new(_socket(reset.outputs, "Result"), _socket(history.inputs, "Reset"))

        geometry = _socket(history.outputs, "Surface" if surface else "History")
        if store_outputs:
            output_index = _store_attribute(
                tree,
                geometry,
                _socket(history.outputs, "History Index"),
                "dh_test_history_index_output",
                "INT",
            )
            output_position = _store_attribute(
                tree,
                _socket(output_index.outputs, "Geometry"),
                _socket(history.outputs, "History Position"),
                "dh_test_history_pos_output",
            )
            geometry = _socket(output_position.outputs, "Geometry")

        tree.links.new(geometry, _socket(group_out.inputs, "Geometry"))
        return _new_host(name + " Host", tree)

    obj = build_host(
        "DH Test Spectrum History",
        4,
        reset_frame=6,
        store_outputs=True,
    )
    expected_vertices = {1: 3, 2: 6, 3: 9, 4: 12, 5: 12, 6: 3, 7: 6, 8: 9}
    expected_edges = {frame: vertices // 3 * 2 for frame, vertices in expected_vertices.items()}
    snapshots = {}
    core_ok = True
    attributes_ok = True
    output_fields_ok = True
    provenance_ok = True

    for frame in range(1, 9):
        snapshot = _snapshot(obj, frame)
        snapshots[frame] = snapshot
        attrs = snapshot["attributes"]
        core_ok = core_ok and (
            len(snapshot["vertices"]) == expected_vertices[frame]
            and snapshot["edges"] == expected_edges[frame]
        )
        attributes_ok = attributes_ok and all(
            name in attrs
            for name in (*HISTORY_ATTRIBUTES, "dh_audio_amp", "dh_audio_band_index")
        )
        if not attributes_ok:
            continue

        ages = attrs["dh_audio_history_index"]
        positions = attrs["dh_audio_history_pos"]
        amplitudes = attrs["dh_audio_amp"]
        bands = attrs["dh_audio_band_index"]
        output_fields_ok = output_fields_ok and (
            attrs.get("dh_test_history_index_output") == ages
            and all(
                abs(a - b) < 1e-6
                for a, b in zip(attrs.get("dh_test_history_pos_output", ()), positions)
            )
        )

        for age in sorted(set(ages)):
            point_indices = [i for i, value in enumerate(ages) if value == age]
            expected_amp = frame - age
            provenance_ok = provenance_ok and (
                len(point_indices) == 3
                and {bands[i] for i in point_indices} == {0, 1, 2}
                and all(abs(amplitudes[i] - expected_amp) < 1e-6 for i in point_indices)
                and all(abs(positions[i] - age / 3.0) < 1e-6 for i in point_indices)
                and all(abs(snapshot["vertices"][i][1] + age) < 1e-6 for i in point_indices)
            )

    report.check("Spectrum History stays bounded and keeps separate row edges", core_ok, {
        frame: {"vertices": len(value["vertices"]), "edges": value["edges"]}
        for frame, value in snapshots.items()
    })
    report.check("Spectrum History preserves and adds standardized attributes", attributes_ok)
    report.check("Spectrum History output fields match stored attributes", output_fields_ok)
    report.check("Spectrum History age, offset, normalization, and frame provenance", provenance_ok)
    report.check(
        "Spectrum History reset clears previous rows in one frame",
        len(snapshots[5]["vertices"]) == 12 and len(snapshots[6]["vertices"]) == 3 and len(snapshots[7]["vertices"]) == 6,
        {frame: len(snapshots[frame]["vertices"]) for frame in (5, 6, 7)},
    )

    one_frame_obj = build_host("DH Test Spectrum History One Frame", 1)
    one_frame = [_snapshot(one_frame_obj, frame) for frame in range(1, 6)]
    report.check(
        "Spectrum History Frames = 1 retains only current row",
        all(
            len(snapshot["vertices"]) == 3
            and snapshot["edges"] == 2
            and snapshot["attributes"].get("dh_audio_history_index") == [0, 0, 0]
            and snapshot["attributes"].get("dh_audio_history_pos") == [0.0, 0.0, 0.0]
            for snapshot in one_frame
        ),
    )

    varying_obj = build_host(
        "DH Test Spectrum History Topology",
        4,
        varying_topology=True,
    )
    varying = {frame: _snapshot(varying_obj, frame) for frame in range(1, 9)}
    expected_varying = {1: 3, 2: 6, 3: 9, 4: 12, 5: 14, 6: 16, 7: 18, 8: 20}
    topology_ok = all(
        len(varying[frame]["vertices"]) == count
        for frame, count in expected_varying.items()
    )
    topology_attrs_ok = True
    for frame, snapshot in varying.items():
        ages = snapshot["attributes"].get("dh_audio_history_index", [])
        bands = snapshot["attributes"].get("dh_audio_band_index", [])
        for age in set(ages):
            expected_count = 5 if frame - age >= 5 else 3
            point_indices = [i for i, value in enumerate(ages) if value == age]
            topology_attrs_ok = topology_attrs_ok and (
                len(point_indices) == expected_count
                and {bands[i] for i in point_indices} == set(range(expected_count))
            )
    report.check(
        "Spectrum History supports changing source topology",
        topology_ok and topology_attrs_ok,
        {frame: len(snapshot["vertices"]) for frame, snapshot in varying.items()},
    )

    history_tree = bpy.data.node_groups["DH Audio Spectrum History"]
    delete_node = history_tree.nodes.get("Delete Expired Rows")
    stored_index = history_tree.nodes.get("Stored History Index")
    report.check(
        "Spectrum History uses Blender 5.2 point-domain bounded deletion",
        (
            delete_node is not None
            and delete_node.bl_idname == "GeometryNodeDeleteGeometry"
            and delete_node.domain == "POINT"
            and delete_node.mode == "ALL"
            and stored_index is not None
            and stored_index.bl_idname == "GeometryNodeInputNamedAttribute"
        ),
    )

    surface_obj = build_host("DH Test Connected Waterfall", 4, surface=True)
    surface = {frame: _snapshot(surface_obj, frame) for frame in range(1, 5)}
    surface_attrs_ok = all(
        all(
            name in snapshot["attributes"]
            for name in (*SPECTRUM_ATTRIBUTES, *TEMPORAL_ATTRIBUTES, *HISTORY_ATTRIBUTES)
        )
        for snapshot in surface.values()
    )
    surface_ok = (
        len(surface[1]["vertices"]) == 3
        and surface[1]["faces"] == 0
        and len(surface[4]["vertices"]) == 12
        and surface[4]["faces"] == 6
        and surface_attrs_ok
    )
    report.check(
        "Spectrum History optional surface connects retained rows and preserves attributes",
        surface_ok,
        {frame: {"vertices": len(snapshot["vertices"]), "faces": snapshot["faces"]} for frame, snapshot in surface.items()},
    )

    decimated_surface_obj = build_host(
        "DH Test Decimated Waterfall", 4, surface=True, row_decimation=2
    )
    # Spectrum History is a Simulation Zone: evaluate the preceding timeline
    # frames before inspecting the retained, decimated surface at frame 4.
    for frame in range(1, 4):
        _snapshot(decimated_surface_obj, frame)
    decimated_surface = _snapshot(decimated_surface_obj, 4)
    report.check(
        "Spectrum History surface row decimation reduces connected rows",
        len(decimated_surface["vertices"]) == 6 and decimated_surface["faces"] == 2,
        {"vertices": len(decimated_surface["vertices"]), "faces": decimated_surface["faces"]},
    )

    report.observations["spectrum_history"] = {
        "frames": 4,
        "offset": [0.0, -1.0, 0.0],
        "frame_vertex_counts": {frame: len(snapshot["vertices"]) for frame, snapshot in snapshots.items()},
        "varying_topology_vertex_counts": {frame: len(snapshot["vertices"]) for frame, snapshot in varying.items()},
        "surface_frame_4": {"vertices": len(surface[4]["vertices"]), "faces": surface[4]["faces"]},
        "timeline_requirement": "Play sequentially or bake/cache; an uncached forward jump advances one simulation step.",
    }


def _test_peak_hold_waterfall_recipe(report, sound):
    """Verify the public, documented Analyzer → Temporal → History workflow."""
    tree, _group_in, group_out = _new_geometry_tree("DH Recipe Peak Hold Waterfall")
    analyzer = _group_node(tree, "DH Audio Analyzer")
    _set_input(analyzer, "Sound", sound)
    _set_input(analyzer, "Bands", 8)

    temporal = _group_node(tree, "DH Audio Temporal Response")
    _set_input(temporal, "Attack", 0.05)
    _set_input(temporal, "Release", 0.25)
    _set_input(temporal, "Peak Hold", True)
    _set_input(temporal, "Peak Hold Time", 0.2)
    _set_input(temporal, "Peak Decay", 0.5)

    points = _group_node(tree, "DH Audio Spectrum Points")
    _set_input(points, "Height", 3.0)
    _set_input(points, "Center Spectrum", True)

    history = _group_node(tree, "DH Audio Spectrum History")
    _set_input(history, "Frames", 4)
    _set_input(history, "History Offset", (0.0, -0.15, 0.0))
    _set_input(history, "Surface", True)
    _set_input(history, "Row Decimation", 1)

    tree.links.new(_socket(analyzer.outputs, "Spectrum"), _socket(temporal.inputs, "Spectrum"))
    tree.links.new(_socket(temporal.outputs, "Spectrum"), _socket(points.inputs, "Spectrum"))
    tree.links.new(_socket(points.outputs, "Spectrum Points"), _socket(history.inputs, "Spectrum Points"))
    tree.links.new(_socket(history.outputs, "Surface"), _socket(group_out.inputs, "Geometry"))

    obj = _new_host("DH Recipe Peak Hold Waterfall Host", tree)
    snapshots = {frame: _snapshot(obj, frame) for frame in range(1, 5)}
    final = snapshots[4]
    expected_attributes = {
        *SPECTRUM_ATTRIBUTES,
        *HISTORY_ATTRIBUTES,
        *TEMPORAL_ATTRIBUTES,
    }
    report.check(
        "Peak Hold Waterfall recipe connects a temporal spectrum to a surface",
        (
            len(final["vertices"]) == 32
            and final["faces"] == 21
            and expected_attributes.issubset(final["attributes"])
        ),
        {
            "frame_4": {
                "vertices": len(final["vertices"]),
                "faces": final["faces"],
                "attributes": sorted(final["attributes"]),
            },
            "connections": [
                "Analyzer Spectrum -> Temporal Response Spectrum",
                "Temporal Response Spectrum -> Spectrum Points Spectrum",
                "Spectrum Points -> Spectrum History",
                "Spectrum History Surface -> Group Output",
            ],
        },
    )
    report.observations["peak_hold_waterfall_recipe"] = {
        "bands": 8,
        "frames": 4,
        "frame_4": {"vertices": len(final["vertices"]), "faces": final["faces"]},
        "timeline_requirement": "Evaluate frames sequentially or bake/cache the Simulation Zones.",
    }


def _test_radial_spectrum(report):
    def build_source(name, count):
        tree, _group_in, group_out = _new_geometry_tree(name)
        line = tree.nodes.new("GeometryNodeMeshLine")
        line.mode = "OFFSET"
        _set_input(line, "Count", count)
        _set_input(line, "Offset", (1.0, 0.0, 0.0))
        index = tree.nodes.new("GeometryNodeInputIndex")
        position = tree.nodes.new("ShaderNodeMath")
        position.operation = "DIVIDE"
        _set_input(position, 1, float(max(count - 1, 1)))
        tree.links.new(_socket(index.outputs, "Index"), _socket(position.inputs, 0))

        height = tree.nodes.new("ShaderNodeMath")
        height.operation = "MULTIPLY"
        _set_input(height, 1, 0.75)
        tree.links.new(_socket(position.outputs, "Value"), _socket(height.inputs, 0))
        height_vector = tree.nodes.new("ShaderNodeCombineXYZ")
        tree.links.new(_socket(height.outputs, "Value"), _socket(height_vector.inputs, "Z"))
        set_position = tree.nodes.new("GeometryNodeSetPosition")
        tree.links.new(_socket(line.outputs, "Mesh"), _socket(set_position.inputs, "Geometry"))
        tree.links.new(_socket(height_vector.outputs, "Vector"), _socket(set_position.inputs, "Offset"))

        band_index = _store_attribute(
            tree,
            _socket(set_position.outputs, "Geometry"),
            _socket(index.outputs, "Index"),
            "dh_audio_band_index",
            "INT",
        )
        band_position = _store_attribute(
            tree,
            _socket(band_index.outputs, "Geometry"),
            _socket(position.outputs, "Value"),
            "dh_audio_band_pos",
        )
        amplitude = _store_attribute(
            tree,
            _socket(band_position.outputs, "Geometry"),
            _socket(position.outputs, "Value"),
            "dh_audio_amp",
        )
        tree.links.new(_socket(amplitude.outputs, "Geometry"), _socket(group_out.inputs, "Geometry"))
        return tree

    def build_host(
        name,
        source,
        *,
        cyclic,
        sweep,
        center=(0.0, 0.0, 0.0),
        height_scale=1.0,
        audio_radius=0.0,
        spiral=0.0,
        curve_output=False,
        store_fields=False,
    ):
        tree, _group_in, group_out = _new_geometry_tree(name)
        source_node = tree.nodes.new("GeometryNodeGroup")
        source_node.node_tree = source
        radial = _group_node(tree, "DH Audio Radial Spectrum")
        _set_input(radial, "Radius", 2.0)
        _set_input(radial, "Audio Radius", audio_radius)
        _set_input(radial, "Spiral", spiral)
        _set_input(radial, "Height Scale", height_scale)
        _set_input(radial, "Center", center)
        _set_input(radial, "Start Angle", 0.0)
        _set_input(radial, "Sweep Angle", sweep)
        _set_input(radial, "Cyclic", cyclic)
        tree.links.new(_socket(source_node.outputs, "Geometry"), _socket(radial.inputs, "Spectrum"))

        if curve_output:
            profile = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
            _set_input(profile, "Resolution", 3)
            _set_input(profile, "Radius", 0.05)
            tube = tree.nodes.new("GeometryNodeCurveToMesh")
            tree.links.new(_socket(radial.outputs, "Curve"), _socket(tube.inputs, "Curve"))
            tree.links.new(_socket(profile.outputs, "Curve"), _socket(tube.inputs, "Profile Curve"))
            geometry = _socket(tube.outputs, "Mesh")
        else:
            geometry = _socket(radial.outputs, "Spectrum Points")

        if store_fields:
            angle_store = _store_attribute(
                tree,
                geometry,
                _socket(radial.outputs, "Angle"),
                "dh_test_radial_angle",
            )
            radius_store = _store_attribute(
                tree,
                _socket(angle_store.outputs, "Geometry"),
                _socket(radial.outputs, "Mapped Radius"),
                "dh_test_radial_radius",
            )
            geometry = _socket(radius_store.outputs, "Geometry")

        tree.links.new(geometry, _socket(group_out.inputs, "Geometry"))
        return _new_host(name + " Host", tree)

    source = build_source("DH Test Radial Source", 8)
    cyclic_obj = build_host(
        "DH Test Radial Cyclic",
        source,
        cyclic=True,
        sweep=math.tau,
        audio_radius=1.0,
        spiral=2.0,
        store_fields=True,
    )
    cyclic = _snapshot(cyclic_obj)
    attrs = cyclic["attributes"]
    unique_xy = {
        (round(vertex[0], 5), round(vertex[1], 5))
        for vertex in cyclic["vertices"]
    }
    angles = attrs.get("dh_test_radial_angle", [])
    sorted_angles = sorted(angles)
    gaps = [
        sorted_angles[index + 1] - sorted_angles[index]
        for index in range(len(sorted_angles) - 1)
    ]
    if sorted_angles:
        gaps.append(math.tau - sorted_angles[-1] + sorted_angles[0])

    expected_positions = [index / 7.0 for index in range(8)]
    expected_radii = [2.0 + 3.0 * position for position in expected_positions]
    actual_radii = attrs.get("dh_test_radial_radius", [])
    xy_radii = [math.hypot(vertex[0], vertex[1]) for vertex in cyclic["vertices"]]
    report.check(
        "Radial Spectrum cyclic layout has unique evenly spaced seam",
        (
            len(cyclic["vertices"]) == 8
            and len(unique_xy) == 8
            and len(gaps) == 8
            and all(abs(gap - math.tau / 8.0) < 1e-5 for gap in gaps)
        ),
        {"unique_xy": len(unique_xy), "angle_gaps": gaps},
    )
    report.check(
        "Radial Spectrum preserves source attributes",
        (
            attrs.get("dh_audio_band_index") == list(range(8))
            and all(
                abs(a - b) < 1e-6
                for a, b in zip(attrs.get("dh_audio_band_pos", ()), expected_positions)
            )
            and all(
                abs(a - b) < 1e-6
                for a, b in zip(attrs.get("dh_audio_amp", ()), expected_positions)
            )
        ),
    )
    report.check(
        "Radial Spectrum audio/spiral radius and output fields agree",
        (
            len(actual_radii) == 8
            and all(abs(a - b) < 1e-5 for a, b in zip(actual_radii, expected_radii))
            and all(abs(a - b) < 1e-5 for a, b in zip(xy_radii, expected_radii))
            and all(abs(a - b) < 1e-5 for a, b in zip(angles, [index * math.tau / 8.0 for index in range(8)]))
        ),
        {"field_radii": actual_radii, "xy_radii": xy_radii},
    )

    open_obj = build_host(
        "DH Test Radial Open Arc",
        source,
        cyclic=False,
        sweep=math.pi,
        center=(1.0, -2.0, 3.0),
        height_scale=2.0,
    )
    open_arc = _snapshot(open_obj)
    first = open_arc["vertices"][0]
    last = open_arc["vertices"][-1]
    report.check(
        "Radial Spectrum open arc includes both endpoints and preserves height",
        (
            all(abs(a - b) < 1e-5 for a, b in zip(first, (3.0, -2.0, 3.0)))
            and all(abs(a - b) < 1e-5 for a, b in zip(last, (-1.0, -2.0, 4.5)))
        ),
        {"first": first, "last": last},
    )

    cyclic_curve = _snapshot(build_host(
        "DH Test Radial Cyclic Curve",
        source,
        cyclic=True,
        sweep=math.tau,
        curve_output=True,
    ))
    open_curve = _snapshot(build_host(
        "DH Test Radial Open Curve",
        source,
        cyclic=False,
        sweep=math.pi,
        curve_output=True,
    ))
    report.check(
        "Radial Spectrum Curve output closes only in Cyclic mode",
        cyclic_curve["faces"] == 24 and open_curve["faces"] == 21,
        {"cyclic_faces": cyclic_curve["faces"], "open_faces": open_curve["faces"]},
    )

    single_source = build_source("DH Test Radial Single Source", 1)
    single = _snapshot(build_host(
        "DH Test Radial Single Band",
        single_source,
        cyclic=False,
        sweep=math.pi,
    ))
    report.check(
        "Radial Spectrum one-band layout is finite",
        (
            len(single["vertices"]) == 1
            and all(math.isfinite(value) for value in single["vertices"][0])
        ),
        single["vertices"],
    )

    radial_tree = bpy.data.node_groups["DH Audio Radial Spectrum"]
    domain_size = radial_tree.nodes.get("Spectrum Domain Size")
    cyclic_node = radial_tree.nodes.get("Set Radial Curve Cyclic")
    report.check(
        "Radial Spectrum uses Blender 5.2 domain-size and cyclic-curve nodes",
        (
            domain_size is not None
            and domain_size.bl_idname == "GeometryNodeAttributeDomainSize"
            and domain_size.component == "MESH"
            and cyclic_node is not None
            and cyclic_node.bl_idname == "GeometryNodeSetSplineCyclic"
        ),
    )

    report.observations["radial_spectrum"] = {
        "cyclic_unique_xy": len(unique_xy),
        "cyclic_angle_gaps": gaps,
        "open_arc_first": first,
        "open_arc_last": last,
        "curve_faces": {"cyclic": cyclic_curve["faces"], "open": open_curve["faces"]},
        "seam_policy": "Cyclic uses Index / Point Count; open arcs use Index / max(Point Count - 1, 1).",
    }


def _test_bands(report, sound):
    tree, _group_in, group_out = _new_geometry_tree("DH Test Bands")
    bands = _group_node(tree, "DH Audio Bands")
    _set_input(bands, "Sound", sound)
    tree.links.new(_socket(bands.outputs, "Band Data"), _socket(group_out.inputs, "Geometry"))
    obj = _new_host("DH Test Bands Host", tree)

    values_by_frame = {}
    for frame in (10, 40, 70):
        snapshot = _snapshot(obj, frame)
        amplitude = snapshot["attributes"].get("dh_audio_named_amp") or []
        values_by_frame[frame] = amplitude
        report.check(f"Bands frame {frame}: nine carrier points", len(snapshot["vertices"]) == 9, len(snapshot["vertices"]))
        report.check(f"Bands frame {frame}: varying values", bool(amplitude) and max(amplitude) > 1e-5, amplitude)

    # Index 0 is the independent Total Volume range, so compare the eight
    # contiguous musical bands at indices 1..8.
    peak_indices = [max(range(1, 9), key=values_by_frame[frame].__getitem__) for frame in (10, 40, 70)]
    report.check("Named musical-band peaks move upward", peak_indices[0] < peak_indices[1] < peak_indices[2], peak_indices)

    bridge_tree, _bridge_in, bridge_out = _new_geometry_tree("DH Test Bands Bridge")
    bridge_bands = _group_node(bridge_tree, "DH Audio Bands")
    _set_input(bridge_bands, "Sound", sound)
    point = _single_point(bridge_tree)
    bridge_tree.links.new(_socket(point.outputs, "Mesh"), _socket(bridge_bands.inputs, "Geometry"))
    bridge_tree.links.new(_socket(bridge_bands.outputs, "Geometry"), _socket(bridge_out.inputs, "Geometry"))
    bridge_obj = _new_host("DH Test Bands Bridge Host", bridge_tree)
    bridge = _snapshot(bridge_obj, 40)
    report.check("Bands point attribute bridge", all(name in bridge["attributes"] for name in NAMED_BAND_ATTRIBUTES), sorted(bridge["attributes"]))
    report.check("Bands bridged values are nonzero", any(abs(bridge["attributes"][name][0]) > 1e-5 for name in NAMED_BAND_ATTRIBUTES), {name: bridge["attributes"].get(name) for name in NAMED_BAND_ATTRIBUTES})

    report.observations["named_band_peak_indices"] = peak_indices


def _test_sample_range_and_query(report, sound):
    range_tree, _range_in, range_out = _new_geometry_tree("DH Test Sample Range")
    sample = _group_node(range_tree, "DH Audio Sample Range")
    _set_input(sample, "Sound", sound)
    _set_input(sample, "Low Frequency", 50.0)
    _set_input(sample, "High Frequency", 300.0)
    point = _single_point(range_tree)
    store = _store_attribute(range_tree, _socket(point.outputs, "Mesh"), _socket(sample.outputs, "Amplitude"), "dh_test_value")
    range_tree.links.new(_socket(store.outputs, "Geometry"), _socket(range_out.inputs, "Geometry"))
    range_obj = _new_host("DH Test Sample Range Host", range_tree)
    low = _snapshot(range_obj, 10)["attributes"]["dh_test_value"][0]
    mid = _snapshot(range_obj, 40)["attributes"]["dh_test_value"][0]
    report.check("Sample Range changes across frames", abs(low - mid) > 1e-4, {"frame_10": low, "frame_40": mid})

    query_tree, _query_in, query_out = _new_geometry_tree("DH Test Band Query")
    analyzer = _group_node(query_tree, "DH Audio Analyzer")
    _set_input(analyzer, "Sound", sound)
    query = _group_node(query_tree, "DH Audio Band Query")
    query_tree.links.new(_socket(analyzer.outputs, "Spectrum"), _socket(query.inputs, "Spectrum"))
    query_point = _single_point(query_tree)
    store_index = _store_attribute(query_tree, _socket(query_point.outputs, "Mesh"), _socket(query.outputs, "Band Index"), "dh_test_index", "INT")
    query_tree.links.new(_socket(store_index.outputs, "Geometry"), _socket(query_out.inputs, "Geometry"))
    query_obj = _new_host("DH Test Band Query Host", query_tree)

    _set_input(query, "Band", -5)
    low_index = _snapshot(query_obj, 10)["attributes"]["dh_test_index"][0]
    _set_input(query, "Band", 999)
    high_index = _snapshot(query_obj, 10)["attributes"]["dh_test_index"][0]
    report.check("Band Query clamps below range", low_index == 0, low_index)
    report.check("Band Query clamps above range", high_index == 31, high_index)


def _test_spectrum_sample(report):
    tree, _group_in, group_out = _new_geometry_tree("DH Test Spectrum Sample")

    source = tree.nodes.new("GeometryNodeMeshLine")
    source.mode = "OFFSET"
    _set_input(source, "Count", 4)
    source_index = tree.nodes.new("GeometryNodeInputIndex")

    amplitude_scale = tree.nodes.new("ShaderNodeMath")
    amplitude_scale.operation = "MULTIPLY"
    _set_input(amplitude_scale, 1, 0.25)
    amplitude_add = tree.nodes.new("ShaderNodeMath")
    amplitude_add.operation = "ADD"
    _set_input(amplitude_add, 1, 0.1)
    tree.links.new(_socket(source_index.outputs, "Index"), _socket(amplitude_scale.inputs, 0))
    tree.links.new(_socket(amplitude_scale.outputs, "Value"), _socket(amplitude_add.inputs, 0))

    left_add = tree.nodes.new("ShaderNodeMath")
    left_add.operation = "ADD"
    _set_input(left_add, 1, 10.0)
    right_add = tree.nodes.new("ShaderNodeMath")
    right_add.operation = "ADD"
    _set_input(right_add, 1, 20.0)
    tree.links.new(_socket(source_index.outputs, "Index"), _socket(left_add.inputs, 0))
    tree.links.new(_socket(source_index.outputs, "Index"), _socket(right_add.inputs, 0))

    source_amp = _store_attribute(
        tree,
        _socket(source.outputs, "Mesh"),
        _socket(amplitude_add.outputs, "Value"),
        "dh_audio_amp",
    )
    source_band = _store_attribute(
        tree,
        _socket(source_amp.outputs, "Geometry"),
        _socket(source_index.outputs, "Index"),
        "dh_audio_band_index",
        "INT",
    )
    source_left = _store_attribute(
        tree,
        _socket(source_band.outputs, "Geometry"),
        _socket(left_add.outputs, "Value"),
        "dh_audio_left_amp",
    )
    source_right = _store_attribute(
        tree,
        _socket(source_left.outputs, "Geometry"),
        _socket(right_add.outputs, "Value"),
        "dh_audio_right_amp",
    )

    target = tree.nodes.new("GeometryNodeMeshLine")
    target.mode = "OFFSET"
    _set_input(target, "Count", 6)
    target_index = tree.nodes.new("GeometryNodeInputIndex")
    modulo = tree.nodes.new("FunctionNodeIntegerMath")
    modulo.operation = "MODULO"
    _set_input(modulo, 1, 4)
    tree.links.new(_socket(target_index.outputs, "Index"), _socket(modulo.inputs, 0))

    sample = _group_node(tree, "DH Audio Spectrum Sample")
    tree.links.new(_socket(source_right.outputs, "Geometry"), _socket(sample.inputs, "Spectrum"))
    tree.links.new(_socket(modulo.outputs, "Value"), _socket(sample.inputs, "Band"))

    sampled_amp = _store_attribute(
        tree,
        _socket(target.outputs, "Mesh"),
        _socket(sample.outputs, "Amplitude"),
        "dh_test_sample_amp",
    )
    sampled_band = _store_attribute(
        tree,
        _socket(sampled_amp.outputs, "Geometry"),
        _socket(sample.outputs, "Band Index"),
        "dh_test_sample_band",
        "INT",
    )
    sampled_left = _store_attribute(
        tree,
        _socket(sampled_band.outputs, "Geometry"),
        _socket(sample.outputs, "Left Amplitude"),
        "dh_test_sample_left",
    )
    sampled_right = _store_attribute(
        tree,
        _socket(sampled_left.outputs, "Geometry"),
        _socket(sample.outputs, "Right Amplitude"),
        "dh_test_sample_right",
    )
    tree.links.new(_socket(sampled_right.outputs, "Geometry"), _socket(group_out.inputs, "Geometry"))

    obj = _new_host("DH Test Spectrum Sample Host", tree)
    snapshot = _snapshot(obj)
    attributes = snapshot["attributes"]

    expected_amp = [0.1, 0.35, 0.6, 0.85, 0.1, 0.35]
    expected_band = [0, 1, 2, 3, 0, 1]
    expected_left = [10.0, 11.0, 12.0, 13.0, 10.0, 11.0]
    expected_right = [20.0, 21.0, 22.0, 23.0, 20.0, 21.0]

    def close(actual, expected):
        return actual is not None and len(actual) == len(expected) and all(
            abs(float(a) - float(b)) < 1e-5 for a, b in zip(actual, expected)
        )

    report.check(
        "Spectrum Sample evaluates Band as a per-element field",
        close(attributes.get("dh_test_sample_amp"), expected_amp),
        attributes.get("dh_test_sample_amp"),
    )
    report.check(
        "Spectrum Sample returns sampled band indices",
        attributes.get("dh_test_sample_band") == expected_band,
        attributes.get("dh_test_sample_band"),
    )
    report.check(
        "Spectrum Sample returns paired left fields",
        close(attributes.get("dh_test_sample_left"), expected_left),
        attributes.get("dh_test_sample_left"),
    )
    report.check(
        "Spectrum Sample returns paired right fields",
        close(attributes.get("dh_test_sample_right"), expected_right),
        attributes.get("dh_test_sample_right"),
    )

    sample_tree = bpy.data.node_groups["DH Audio Spectrum Sample"]
    sample_nodes = [
        node for node in sample_tree.nodes
        if node.bl_idname == "GeometryNodeSampleIndex"
    ]
    report.check(
        "Spectrum Sample clamps every sampled attribute",
        len(sample_nodes) == len(SPECTRUM_ATTRIBUTES) + len(STEREO_ATTRIBUTES)
        and all(node.clamp and node.domain == "POINT" for node in sample_nodes),
        {"count": len(sample_nodes), "clamp": [node.clamp for node in sample_nodes]},
    )


def _test_spectrum_bridge(report):
    def synthetic_source(tree):
        source = tree.nodes.new("GeometryNodeMeshLine")
        source.mode = "OFFSET"
        _set_input(source, "Count", 4)
        source_index = tree.nodes.new("GeometryNodeInputIndex")

        amplitude_scale = tree.nodes.new("ShaderNodeMath")
        amplitude_scale.operation = "MULTIPLY"
        _set_input(amplitude_scale, 1, 0.25)
        amplitude_add = tree.nodes.new("ShaderNodeMath")
        amplitude_add.operation = "ADD"
        _set_input(amplitude_add, 1, 0.1)
        tree.links.new(_socket(source_index.outputs, "Index"), _socket(amplitude_scale.inputs, 0))
        tree.links.new(_socket(amplitude_scale.outputs, "Value"), _socket(amplitude_add.inputs, 0))

        left_add = tree.nodes.new("ShaderNodeMath")
        left_add.operation = "ADD"
        _set_input(left_add, 1, 10.0)
        right_add = tree.nodes.new("ShaderNodeMath")
        right_add.operation = "ADD"
        _set_input(right_add, 1, 20.0)
        tree.links.new(_socket(source_index.outputs, "Index"), _socket(left_add.inputs, 0))
        tree.links.new(_socket(source_index.outputs, "Index"), _socket(right_add.inputs, 0))

        source_amp = _store_attribute(
            tree,
            _socket(source.outputs, "Mesh"),
            _socket(amplitude_add.outputs, "Value"),
            "dh_audio_amp",
        )
        source_band = _store_attribute(
            tree,
            _socket(source_amp.outputs, "Geometry"),
            _socket(source_index.outputs, "Index"),
            "dh_audio_band_index",
            "INT",
        )
        source_left = _store_attribute(
            tree,
            _socket(source_band.outputs, "Geometry"),
            _socket(left_add.outputs, "Value"),
            "dh_audio_left_amp",
        )
        source_right = _store_attribute(
            tree,
            _socket(source_left.outputs, "Geometry"),
            _socket(right_add.outputs, "Value"),
            "dh_audio_right_amp",
        )
        return _socket(source_right.outputs, "Geometry")

    def repeating_band_field(tree):
        target_index = tree.nodes.new("GeometryNodeInputIndex")
        modulo = tree.nodes.new("FunctionNodeIntegerMath")
        modulo.operation = "MODULO"
        _set_input(modulo, 1, 4)
        tree.links.new(_socket(target_index.outputs, "Index"), _socket(modulo.inputs, 0))
        return target_index, _socket(modulo.outputs, "Value")

    def close(actual, expected):
        return actual is not None and len(actual) == len(expected) and all(
            abs(float(a) - float(b)) < 1e-5 for a, b in zip(actual, expected)
        )

    # Point-domain storage, partial Selection, and direct output fields.
    point_tree, _group_in, point_out = _new_geometry_tree("DH Test Spectrum Bridge Points")
    source_geometry = synthetic_source(point_tree)
    target = point_tree.nodes.new("GeometryNodeMeshLine")
    target.mode = "OFFSET"
    _set_input(target, "Count", 6)
    target_index, band_field = repeating_band_field(point_tree)

    selected = point_tree.nodes.new("FunctionNodeCompare")
    selected.data_type = "INT"
    selected.operation = "LESS_THAN"
    _set_input(selected, "B", 3)
    point_tree.links.new(_socket(target_index.outputs, "Index"), _socket(selected.inputs, "A"))

    bridge = _group_node(point_tree, "DH Audio Spectrum Bridge")
    _set_input(bridge, "Store on Points", True)
    _set_input(bridge, "Store on Instances", False)
    point_tree.links.new(_socket(target.outputs, "Mesh"), _socket(bridge.inputs, "Geometry"))
    point_tree.links.new(source_geometry, _socket(bridge.inputs, "Spectrum"))
    point_tree.links.new(band_field, _socket(bridge.inputs, "Band"))
    point_tree.links.new(_socket(selected.outputs, "Result"), _socket(bridge.inputs, "Selection"))

    direct = _store_attribute(
        point_tree,
        _socket(bridge.outputs, "Geometry"),
        _socket(bridge.outputs, "Amplitude"),
        "dh_test_bridge_direct",
    )
    point_tree.links.new(_socket(direct.outputs, "Geometry"), _socket(point_out.inputs, "Geometry"))
    point_obj = _new_host("DH Test Spectrum Bridge Point Host", point_tree)
    point_attributes = _snapshot(point_obj)["attributes"]

    sampled = [0.1, 0.35, 0.6, 0.85, 0.1, 0.35]
    selected_sampled = [0.1, 0.35, 0.6, 0.0, 0.0, 0.0]
    report.check(
        "Spectrum Bridge stores sampled amplitudes on selected points",
        close(point_attributes.get("dh_audio_amp"), selected_sampled),
        point_attributes.get("dh_audio_amp"),
    )
    report.check(
        "Spectrum Bridge direct fields remain available outside storage Selection",
        close(point_attributes.get("dh_test_bridge_direct"), sampled),
        point_attributes.get("dh_test_bridge_direct"),
    )
    report.check(
        "Spectrum Bridge stores paired stereo values on points",
        close(point_attributes.get("dh_audio_left_amp"), [10.0, 11.0, 12.0, 0.0, 0.0, 0.0])
        and close(point_attributes.get("dh_audio_right_amp"), [20.0, 21.0, 22.0, 0.0, 0.0, 0.0]),
        {
            "left": point_attributes.get("dh_audio_left_amp"),
            "right": point_attributes.get("dh_audio_right_amp"),
        },
    )

    # Instance-domain storage must be readable before realization and should
    # propagate to the realized mesh in Blender 5.2.
    instance_tree, _group_in, instance_out = _new_geometry_tree("DH Test Spectrum Bridge Instances")
    instance_source = synthetic_source(instance_tree)
    points = instance_tree.nodes.new("GeometryNodeMeshLine")
    points.mode = "OFFSET"
    _set_input(points, "Count", 6)
    _target_index, instance_band = repeating_band_field(instance_tree)
    cube = instance_tree.nodes.new("GeometryNodeMeshCube")
    _set_input(cube, "Size", (0.2, 0.2, 0.2))
    instance_on_points = instance_tree.nodes.new("GeometryNodeInstanceOnPoints")
    instance_tree.links.new(_socket(points.outputs, "Mesh"), _socket(instance_on_points.inputs, "Points"))
    instance_tree.links.new(_socket(cube.outputs, "Mesh"), _socket(instance_on_points.inputs, "Instance"))

    instance_bridge = _group_node(instance_tree, "DH Audio Spectrum Bridge")
    _set_input(instance_bridge, "Store on Points", False)
    _set_input(instance_bridge, "Store on Instances", True)
    instance_tree.links.new(_socket(instance_on_points.outputs, "Instances"), _socket(instance_bridge.inputs, "Geometry"))
    instance_tree.links.new(instance_source, _socket(instance_bridge.inputs, "Spectrum"))
    instance_tree.links.new(instance_band, _socket(instance_bridge.inputs, "Band"))

    read_amp = instance_tree.nodes.new("GeometryNodeInputNamedAttribute")
    read_amp.data_type = "FLOAT"
    _set_input(read_amp, "Name", "dh_audio_amp")
    scale_vector = instance_tree.nodes.new("ShaderNodeCombineXYZ")
    for axis in ("X", "Y", "Z"):
        instance_tree.links.new(_socket(read_amp.outputs, "Attribute"), _socket(scale_vector.inputs, axis))
    scale_instances = instance_tree.nodes.new("GeometryNodeScaleInstances")
    instance_tree.links.new(_socket(instance_bridge.outputs, "Geometry"), _socket(scale_instances.inputs, "Instances"))
    instance_tree.links.new(_socket(scale_vector.outputs, "Vector"), _socket(scale_instances.inputs, "Scale"))
    realize = instance_tree.nodes.new("GeometryNodeRealizeInstances")
    instance_tree.links.new(_socket(scale_instances.outputs, "Instances"), _socket(realize.inputs, "Geometry"))
    instance_tree.links.new(_socket(realize.outputs, "Geometry"), _socket(instance_out.inputs, "Geometry"))

    instance_obj = _new_host("DH Test Spectrum Bridge Instance Host", instance_tree)
    instance_snapshot = _snapshot(instance_obj)
    vertices = instance_snapshot["vertices"]
    dimensions = []
    for instance_index in range(6):
        block = vertices[instance_index * 8:(instance_index + 1) * 8]
        dimensions.append(
            max(vertex[0] for vertex in block) - min(vertex[0] for vertex in block)
        )
    expected_dimensions = [value * 0.2 for value in sampled]
    realized_amp = instance_snapshot["attributes"].get("dh_audio_amp")
    expected_realized_amp = [
        value
        for value in sampled
        for _vertex in range(8)
    ]
    report.check(
        "Spectrum Bridge instance attributes drive instancer-context fields",
        close(dimensions, expected_dimensions),
        dimensions,
    )
    report.check(
        "Spectrum Bridge instance attributes propagate through Realize Instances",
        close(realized_amp, expected_realized_amp),
        realized_amp,
    )

    internal = bpy.data.node_groups["DH Internal - Store Spectrum Bridge Attributes"]
    writers = [
        node for node in internal.nodes
        if node.bl_idname == "GeometryNodeStoreNamedAttribute"
    ]
    expected_writer_count = len(SPECTRUM_ATTRIBUTES) + len(STEREO_ATTRIBUTES)
    report.check(
        "Spectrum Bridge internal writer covers both point and instance domains",
        len(writers) == expected_writer_count * 2
        and sum(node.domain == "POINT" for node in writers) == expected_writer_count
        and sum(node.domain == "INSTANCE" for node in writers) == expected_writer_count
        and all(_socket(node.inputs, "Selection").is_linked for node in writers),
        {
            "count": len(writers),
            "point": sum(node.domain == "POINT" for node in writers),
            "instance": sum(node.domain == "INSTANCE" for node in writers),
        },
    )


def _test_mesh_consumers(report):
    # Arbitrary point geometry: left-channel values drive a selected Z offset.
    deform_tree, _deform_in, deform_out = _new_geometry_tree("DH Test Mesh Deform")
    deform_source = _synthetic_spectrum_source(deform_tree)
    target = deform_tree.nodes.new("GeometryNodeMeshLine")
    target.mode = "OFFSET"
    _set_input(target, "Count", 6)
    _set_input(target, "Offset", (1.0, 0.0, 0.0))
    index = deform_tree.nodes.new("GeometryNodeInputIndex")
    modulo = deform_tree.nodes.new("FunctionNodeIntegerMath")
    modulo.operation = "MODULO"
    _set_input(modulo, 1, 4)
    selected = deform_tree.nodes.new("FunctionNodeCompare")
    selected.data_type = "INT"
    selected.operation = "LESS_THAN"
    _set_input(selected, "B", 5)
    deform_tree.links.new(_socket(index.outputs, "Index"), _socket(modulo.inputs, 0))
    deform_tree.links.new(_socket(index.outputs, "Index"), _socket(selected.inputs, "A"))

    deform = _group_node(deform_tree, "DH Audio Mesh Deform")
    _set_input(deform, "Audio Source", "Left Amplitude")
    _set_input(deform, "Use Normals", False)
    _set_input(deform, "Direction", (0.0, 0.0, 1.0))
    _set_input(deform, "Strength", 0.5)
    _set_input(deform, "Center", 1.0)
    _set_input(deform, "Store on Points", True)
    _set_input(deform, "Store on Instances", False)
    deform_tree.links.new(_socket(target.outputs, "Mesh"), _socket(deform.inputs, "Geometry"))
    deform_tree.links.new(deform_source, _socket(deform.inputs, "Spectrum"))
    deform_tree.links.new(_socket(modulo.outputs, "Value"), _socket(deform.inputs, "Band"))
    deform_tree.links.new(_socket(selected.outputs, "Result"), _socket(deform.inputs, "Selection"))
    deform_tree.links.new(_socket(deform.outputs, "Geometry"), _socket(deform_out.inputs, "Geometry"))

    deform_snapshot = _snapshot(_new_host("DH Test Mesh Deform Host", deform_tree))
    z_values = [round(vertex[2], 5) for vertex in deform_snapshot["vertices"]]
    report.check(
        "Mesh Deform maps stereo audio per point and respects Selection",
        z_values == [0.0, 0.5, 1.0, 1.5, 0.0, 0.0]
        and deform_snapshot["attributes"].get("dh_audio_left_amp") == [1.0, 2.0, 3.0, 4.0, 1.0, 0.0],
        {"z": z_values, "left": deform_snapshot["attributes"].get("dh_audio_left_amp")},
    )

    # Two face bands: normal extrusion, propagated attributes, anonymous fields,
    # then the alternate connected-region direction path.
    extrude_tree, _extrude_in, extrude_out = _new_geometry_tree("DH Test Mesh Extrude")
    extrude_source = _synthetic_spectrum_source(extrude_tree)
    grid = extrude_tree.nodes.new("GeometryNodeMeshGrid")
    _set_input(grid, "Vertices X", 3)
    _set_input(grid, "Vertices Y", 2)
    _set_input(grid, "Size X", 3.0)
    _set_input(grid, "Size Y", 1.0)
    face_index = extrude_tree.nodes.new("GeometryNodeInputIndex")
    extrude = _group_node(extrude_tree, "DH Audio Mesh Extrude")
    _set_input(extrude, "Use Normals", True)
    _set_input(extrude, "Strength", 2.0)
    extrude_tree.links.new(_socket(grid.outputs, "Mesh"), _socket(extrude.inputs, "Mesh"))
    extrude_tree.links.new(extrude_source, _socket(extrude.inputs, "Spectrum"))
    extrude_tree.links.new(_socket(face_index.outputs, "Index"), _socket(extrude.inputs, "Band"))

    current_geometry = _socket(extrude.outputs, "Mesh")
    for attr_name, output_name, data_type in (
        ("dh_test_extrude_top", "Top", "BOOLEAN"),
        ("dh_test_extrude_side", "Side", "BOOLEAN"),
        ("dh_test_extrude_displacement", "Displacement", "FLOAT"),
    ):
        store = extrude_tree.nodes.new("GeometryNodeStoreNamedAttribute")
        store.domain = "FACE"
        store.data_type = data_type
        _set_input(store, "Name", attr_name)
        extrude_tree.links.new(current_geometry, _socket(store.inputs, "Geometry"))
        extrude_tree.links.new(_socket(extrude.outputs, output_name), _socket(store.inputs, "Value"))
        current_geometry = _socket(store.outputs, "Geometry")
    extrude_tree.links.new(current_geometry, _socket(extrude_out.inputs, "Geometry"))

    extrude_obj = _new_host("DH Test Mesh Extrude Host", extrude_tree)
    normal_snapshot = _snapshot(extrude_obj)
    normal_z = [vertex[2] for vertex in normal_snapshot["vertices"]]
    top = normal_snapshot["attributes"].get("dh_test_extrude_top", [])
    side = normal_snapshot["attributes"].get("dh_test_extrude_side", [])
    face_amp = normal_snapshot["attributes"].get("dh_audio_amp", [])
    report.check(
        "Mesh Extrude normal mode creates audio-height faces",
        len(normal_snapshot["vertices"]) == 14
        and normal_snapshot["faces"] == 10
        and abs(max(normal_z) - 1.0) < 1e-5
        and sum(bool(value) for value in top) == 2
        and sum(bool(value) for value in side) == 8,
        {"vertices": len(normal_snapshot["vertices"]), "faces": normal_snapshot["faces"], "z_max": max(normal_z), "top": top, "side": side},
    )
    report.check(
        "Mesh Extrude propagates face-domain spectrum attributes",
        len(face_amp) == 10 and abs(min(face_amp) - 0.25) < 1e-5 and abs(max(face_amp) - 0.5) < 1e-5,
        face_amp,
    )

    _set_input(extrude, "Use Normals", False)
    _set_input(extrude, "Direction", (0.0, 1.0, 0.0))
    direction_snapshot = _snapshot(extrude_obj)
    direction_z = [vertex[2] for vertex in direction_snapshot["vertices"]]
    direction_y = [vertex[1] for vertex in direction_snapshot["vertices"]]
    report.check(
        "Mesh Extrude direction mode offsets the selected region",
        direction_snapshot["faces"] == 8
        and max(abs(value) for value in direction_z) < 1e-5
        and max(direction_y) > 1.4,
        {"faces": direction_snapshot["faces"], "z_max": max(direction_z), "y_max": max(direction_y)},
    )

    face_helper = bpy.data.node_groups["DH Internal - Store Spectrum Face Attributes"]
    writers = [node for node in face_helper.nodes if node.bl_idname == "GeometryNodeStoreNamedAttribute"]
    report.check(
        "Face transport writes the full mono/stereo schema on selected faces",
        len(writers) == len(SPECTRUM_ATTRIBUTES) + len(STEREO_ATTRIBUTES)
        and all(node.domain == "FACE" for node in writers)
        and all(_socket(node.inputs, "Selection").is_linked for node in writers),
        {"count": len(writers), "domains": sorted({node.domain for node in writers})},
    )


def _analyzer_points_chain(tree, sound):
    analyzer = _group_node(tree, "DH Audio Analyzer")
    _set_input(analyzer, "Sound", sound)
    points = _group_node(tree, "DH Audio Spectrum Points")
    tree.links.new(_socket(analyzer.outputs, "Spectrum"), _socket(points.inputs, "Spectrum"))
    return analyzer, points


def _test_visualizers(report, sound):
    points_tree, _points_in, points_out = _new_geometry_tree("DH Test Points")
    _analyzer, points = _analyzer_points_chain(points_tree, sound)
    points_tree.links.new(_socket(points.outputs, "Spectrum Points"), _socket(points_out.inputs, "Geometry"))
    points_obj = _new_host("DH Test Points Host", points_tree)
    points_snapshot = _snapshot(points_obj, 40)
    report.check("Spectrum Points topology", len(points_snapshot["vertices"]) == 32 and points_snapshot["edges"] == 31, {"vertices": len(points_snapshot["vertices"]), "edges": points_snapshot["edges"]})
    report.check("Spectrum Points attributes", all(name in points_snapshot["attributes"] for name in SPECTRUM_ATTRIBUTES), sorted(points_snapshot["attributes"]))

    bars_tree, _bars_in, bars_out = _new_geometry_tree("DH Test Bars")
    bars = _group_node(bars_tree, "DH Audio Spectrum Bars")
    _set_input(bars, "Sound", sound)
    realize = bars_tree.nodes.new("GeometryNodeRealizeInstances")
    bars_tree.links.new(_socket(bars.outputs, "Geometry"), _socket(realize.inputs, "Geometry"))
    bars_tree.links.new(_socket(realize.outputs, "Geometry"), _socket(bars_out.inputs, "Geometry"))
    bars_obj = _new_host("DH Test Bars Host", bars_tree)
    bars_snapshot = _snapshot(bars_obj, 40)
    report.check("Spectrum Bars default Box topology", len(bars_snapshot["vertices"]) == 256 and bars_snapshot["faces"] == 192, {"vertices": len(bars_snapshot["vertices"]), "faces": bars_snapshot["faces"]})
    report.check("Spectrum Bars realized attributes", all(name in bars_snapshot["attributes"] for name in SPECTRUM_ATTRIBUTES), sorted(bars_snapshot["attributes"]))

    instances_tree, _instances_in, instances_out = _new_geometry_tree("DH Test Instances")
    analyzer = _group_node(instances_tree, "DH Audio Analyzer")
    _set_input(analyzer, "Sound", sound)
    instances = _group_node(instances_tree, "DH Audio Spectrum Instances")
    cube = instances_tree.nodes.new("GeometryNodeMeshCube")
    _set_input(cube, "Size", (1.0, 1.0, 1.0))
    instances_tree.links.new(_socket(analyzer.outputs, "Spectrum"), _socket(instances.inputs, "Spectrum"))
    instances_tree.links.new(_socket(cube.outputs, "Mesh"), _socket(instances.inputs, "Instance"))
    _set_input(instances, "Realize Instances", True)
    instances_tree.links.new(_socket(instances.outputs, "Geometry"), _socket(instances_out.inputs, "Geometry"))
    instances_obj = _new_host("DH Test Instances Host", instances_tree)
    instances_snapshot = _snapshot(instances_obj, 40)
    report.check("Spectrum Instances cube topology", len(instances_snapshot["vertices"]) == 256 and instances_snapshot["faces"] == 192, {"vertices": len(instances_snapshot["vertices"]), "faces": instances_snapshot["faces"]})
    report.check("Spectrum Instances propagate attributes", all(name in instances_snapshot["attributes"] for name in SPECTRUM_ATTRIBUTES), sorted(instances_snapshot["attributes"]))

    curve_tree, _curve_in, curve_out = _new_geometry_tree("DH Test Curve")
    _curve_analyzer, curve_points = _analyzer_points_chain(curve_tree, sound)
    curve = _group_node(curve_tree, "DH Audio Spectrum Curve")
    curve_tree.links.new(_socket(curve_points.outputs, "Spectrum Points"), _socket(curve.inputs, "Spectrum Points"))
    curve_tree.links.new(_socket(curve.outputs, "Tube"), _socket(curve_out.inputs, "Geometry"))
    curve_obj = _new_host("DH Test Curve Host", curve_tree)
    curve_counts = {}
    for style in ("Raw", "Smooth", "Smooth + Resample"):
        _set_input(curve, "Curve Style", style)
        snapshot = _snapshot(curve_obj, 40)
        curve_counts[style] = len(snapshot["vertices"])
    report.check("Spectrum Curve style topology", curve_counts["Raw"] < curve_counts["Smooth"] and curve_counts["Smooth + Resample"] == 1024, curve_counts)

    _set_input(curve, "Curve Style", "Raw")
    _set_input(curve, "Tube Radius", 0.06)
    _set_input(curve, "Audio Radius", 0.0)
    constant_radius = max(abs(vertex[1]) for vertex in _snapshot(curve_obj, 40)["vertices"])
    _set_input(curve, "Audio Radius", 1.0)
    reactive_radius = max(abs(vertex[1]) for vertex in _snapshot(curve_obj, 40)["vertices"])
    report.check("Spectrum Curve Audio Radius changes thickness", reactive_radius > constant_radius * 1.05, {"constant": constant_radius, "reactive": reactive_radius})

    fill_tree, _fill_in, fill_out = _new_geometry_tree("DH Test Fill")
    _fill_analyzer, fill_points = _analyzer_points_chain(fill_tree, sound)
    fill = _group_node(fill_tree, "DH Audio Spectrum Fill")
    fill_tree.links.new(_socket(fill_points.outputs, "Spectrum Points"), _socket(fill.inputs, "Spectrum Points"))
    fill_tree.links.new(_socket(fill.outputs, "Mesh"), _socket(fill_out.inputs, "Geometry"))
    fill_obj = _new_host("DH Test Fill Host", fill_tree)
    fill_snapshot = _snapshot(fill_obj, 40)
    report.check("Spectrum Fill topology", len(fill_snapshot["vertices"]) == 64 and fill_snapshot["faces"] == 31, {"vertices": len(fill_snapshot["vertices"]), "faces": fill_snapshot["faces"]})

    report.observations["visualizer_topology"] = {
        "points": {"vertices": len(points_snapshot["vertices"]), "edges": points_snapshot["edges"]},
        "bars": {"vertices": len(bars_snapshot["vertices"]), "faces": bars_snapshot["faces"]},
        "instances": {"vertices": len(instances_snapshot["vertices"]), "faces": instances_snapshot["faces"]},
        "curve_vertices": curve_counts,
        "fill": {"vertices": len(fill_snapshot["vertices"]), "faces": fill_snapshot["faces"]},
    }


def _synthetic_source(name, heights):
    vertices = [(float(index), 0.0, float(height)) for index, height in enumerate(heights)]
    edges = [(index, index + 1) for index in range(len(heights) - 1)]
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    amplitude = mesh.attributes.new("dh_audio_amp", "FLOAT", "POINT")
    for item, height in zip(amplitude.data, heights):
        item.value = float(height)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _test_synthetic_fill_and_curve(report):
    heights = (1.0, 0.0, 1.5, 0.0, 1.0)

    fill_tree, fill_in, fill_out = _new_geometry_tree("DH Test Synthetic Fill", geometry_input=True)
    fill = _group_node(fill_tree, "DH Audio Spectrum Fill")
    fill_tree.links.new(_socket(fill_in.outputs, "Geometry"), _socket(fill.inputs, "Spectrum Points"))
    fill_tree.links.new(_socket(fill.outputs, "Mesh"), _socket(fill_out.inputs, "Geometry"))
    fill_obj = _synthetic_source("DH Test Synthetic Fill Host", heights)
    fill_obj.modifiers.new(name="DH Regression", type="NODES").node_group = fill_tree
    fill_snapshot = _snapshot(fill_obj)
    by_x = {}
    for x, _y, z in fill_snapshot["vertices"]:
        by_x.setdefault(round(x, 4), []).append(z)
    top = [max(by_x[key]) for key in sorted(by_x)]
    report.check("Fill preserves every quiet intermediate band", len(fill_snapshot["vertices"]) == 10 and fill_snapshot["faces"] == 4 and len(top) == 5 and abs(top[1]) < 1e-5 and abs(top[3]) < 1e-5, {"vertices": len(fill_snapshot["vertices"]), "faces": fill_snapshot["faces"], "top": top})

    curve_tree, curve_in, curve_out = _new_geometry_tree("DH Test Synthetic Curve", geometry_input=True)
    curve = _group_node(curve_tree, "DH Audio Spectrum Curve")
    curve_points = curve_tree.nodes.new("GeometryNodeCurveToPoints")
    curve_points.mode = "EVALUATED"
    points_to_vertices = curve_tree.nodes.new("GeometryNodePointsToVertices")
    curve_tree.links.new(_socket(curve_in.outputs, "Geometry"), _socket(curve.inputs, "Spectrum Points"))
    curve_tree.links.new(_socket(curve.outputs, "Curve"), _socket(curve_points.inputs, "Curve"))
    curve_tree.links.new(_socket(curve_points.outputs, "Points"), _socket(points_to_vertices.inputs, "Points"))
    curve_tree.links.new(_socket(points_to_vertices.outputs, "Mesh"), _socket(curve_out.inputs, "Geometry"))
    curve_obj = _synthetic_source("DH Test Synthetic Curve Host", heights)
    curve_obj.modifiers.new(name="DH Regression", type="NODES").node_group = curve_tree

    _set_input(curve, "Curve Style", "Raw")
    raw = _snapshot(curve_obj)
    _set_input(curve, "Curve Style", "Smooth")
    smooth = _snapshot(curve_obj)
    raw_min = min(vertex[2] for vertex in raw["vertices"])
    smooth_min = min(vertex[2] for vertex in smooth["vertices"])
    report.check("Raw curve stays on or above baseline", raw_min >= -1e-6, raw_min)
    report.check("Smooth curve remains evaluable", len(smooth["vertices"]) > len(raw["vertices"]), {"raw_vertices": len(raw["vertices"]), "smooth_vertices": len(smooth["vertices"])})
    report.observations["catmull_rom_baseline"] = {
        "input_min_z": min(heights),
        "raw_min_z": raw_min,
        "smooth_min_z": smooth_min,
        "overshoot_below_baseline": smooth_min < -1e-6,
        "policy": "Known native Catmull-Rom behavior; preserved for public-API compatibility.",
    }


def _remove_test_data():
    for obj in list(bpy.data.objects):
        if obj.name.startswith("DH Test"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for tree in list(bpy.data.node_groups):
        if tree.name.startswith("DH Test"):
            bpy.data.node_groups.remove(tree)
    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith("DH Test"):
            bpy.data.meshes.remove(mesh)


def _clean_release(repo_root, release_path):
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    release_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(release_path), check_existing=False)
    _run_generator(repo_root)
    bpy.ops.wm.save_as_mainfile(filepath=str(release_path), check_existing=False)
    first_signature = _tree_signature()
    catalog_path = release_path.parent / "blender_assets.cats.txt"
    first_catalog = catalog_path.read_bytes()

    _run_generator(repo_root)
    bpy.ops.wm.save_as_mainfile(filepath=str(release_path), check_existing=False)
    second_signature = _tree_signature()
    second_catalog = catalog_path.read_bytes()
    return {
        "path": str(release_path),
        "size": release_path.stat().st_size,
        "catalog_path": str(catalog_path),
        "catalog_sha256": hashlib.sha256(second_catalog).hexdigest(),
        "structural_signature": second_signature,
        "repeat_build_deterministic": first_signature == second_signature and first_catalog == second_catalog,
        "objects": len(bpy.data.objects),
        "node_groups": len(bpy.data.node_groups),
        "assets": sum(1 for tree in bpy.data.node_groups if tree.asset_data),
        "internal_assets": [name for name in INTERNAL_GROUPS if bpy.data.node_groups[name].asset_data],
    }


def run_validation(repo_root=None, release_path=None, report_path=None):
    repo_root = Path(repo_root or Path(__file__).resolve().parents[1]).resolve()
    release_path = Path(release_path).resolve() if release_path else None
    report_path = Path(report_path).resolve() if report_path else None
    report = Report()

    with tempfile.TemporaryDirectory(prefix="dh_audio_toolkit_") as temp_name:
        temp_dir = Path(temp_name)
        test_blend = temp_dir / "baseline.blend"
        test_wav = temp_dir / "regression.wav"

        bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(test_blend), check_existing=False)
        _run_generator(repo_root)
        first_signature = _tree_signature()
        first_catalog = (temp_dir / "blender_assets.cats.txt").read_bytes()

        _run_generator(repo_root)
        second_signature = _tree_signature()
        second_catalog = (temp_dir / "blender_assets.cats.txt").read_bytes()

        report.check("Repeated build structural signature", first_signature == second_signature, {"first": first_signature, "second": second_signature})
        report.check("Repeated build catalog bytes", first_catalog == second_catalog, hashlib.sha256(second_catalog).hexdigest())
        report.check("Exactly 32 generated groups", len([tree for tree in bpy.data.node_groups if tree.name in PUBLIC_GROUPS or tree.name in INTERNAL_GROUPS]) == 32, len(bpy.data.node_groups))
        handler_count = sum(1 for handler in bpy.app.handlers.save_post if getattr(handler, "__name__", "") == "_dh_audio_write_catalogs_on_save")
        report.check("Exactly one toolkit save handler", handler_count == 1, handler_count)

        report.section("Interface audit completed", lambda: _audit_interface(report))
        report.section("Shader Map tests completed", lambda: _test_shader_map(report))
        report.section("Shader UV Transform tests completed", lambda: _test_shader_uv_transform(report))

        _write_test_wav(test_wav)
        sound = bpy.data.sounds.load(str(test_wav), check_existing=False)
        bpy.context.scene.render.fps = 24
        bpy.context.scene.render.fps_base = 1.0

        report.section("Analyzer tests completed", lambda: _test_analyzer(report, sound))
        report.section("Stereo Analyzer tests completed", lambda: _test_stereo_analyzer(report, sound))
        report.section("Temporal Response tests completed", lambda: _test_temporal_response(report))
        report.section("Spectrum History tests completed", lambda: _test_spectrum_history(report))
        report.section(
            "Peak Hold Waterfall recipe completed",
            lambda: _test_peak_hold_waterfall_recipe(report, sound),
        )
        report.section("Radial Spectrum tests completed", lambda: _test_radial_spectrum(report))
        report.section("Named-band tests completed", lambda: _test_bands(report, sound))
        report.section("Sample Range and Band Query tests completed", lambda: _test_sample_range_and_query(report, sound))
        report.section("Spectrum Sample tests completed", lambda: _test_spectrum_sample(report))
        report.section("Spectrum Bridge tests completed", lambda: _test_spectrum_bridge(report))
        report.section("Mesh consumer tests completed", lambda: _test_mesh_consumers(report))
        report.section("Visualizer tests completed", lambda: _test_visualizers(report, sound))
        report.section("Synthetic fill and curve tests completed", lambda: _test_synthetic_fill_and_curve(report))
        _remove_test_data()

    if release_path:
        release = _clean_release(repo_root, release_path)
        report.observations["release"] = release
        report.check("Release contains no scene objects", release["objects"] == 0, release)
        report.check("Release contains 32 generated groups", release["node_groups"] == 32, release)
        report.check("Release contains 25 public assets", release["assets"] == 25, release)
        report.check("Internal groups are not assets", not release["internal_assets"], release["internal_assets"])
        report.check("Release catalog sidecar exists", Path(release["catalog_path"]).is_file(), release["catalog_path"])
        report.check("Release repeat-build is deterministic", release["repeat_build_deterministic"], release)

    result = report.result()
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf8")
    return result


def _parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path)
    parser.add_argument("--release", type=Path)
    return parser.parse_args(argv)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = _parse_args(argv)
    result = run_validation(args.repo, args.release, args.report)
    console_result = {
        "blender": result["blender"],
        "toolkit": result["toolkit"],
        "summary": result["summary"],
        "report": str(args.report.resolve()) if args.report else None,
    }
    print("DH_AUDIO_TOOLKIT_REGRESSION=" + json.dumps(console_result, sort_keys=True))
    if result["summary"]["failed"]:
        failures = [check for check in result["checks"] if not check["passed"]]
        print("DH_AUDIO_TOOLKIT_FAILURES=" + json.dumps(failures, sort_keys=True, default=str))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
