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


TOOLKIT_VERSION = "3.4.0"

PUBLIC_GROUPS = {
    "DH Audio Analyzer": ("GeometryNodeTree", 330, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Bands": ("GeometryNodeTree", 330, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Sample Range": ("GeometryNodeTree", 315, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Frequency Map": ("GeometryNodeTree", 300, "bb4cca6c-c5d5-52c9-80fb-754adc068f91"),
    "DH Audio Frequency Selection": ("GeometryNodeTree", 280, "9b46dff4-fa9d-510f-b0ae-a8af6da87e3a"),
    "DH Audio Band Query": ("GeometryNodeTree", 285, "9b46dff4-fa9d-510f-b0ae-a8af6da87e3a"),
    "DH Audio Response": ("GeometryNodeTree", 285, "a4faf3f4-5a13-5f83-ae97-28993f20ac20"),
    "DH Audio Temporal Response": ("GeometryNodeTree", 310, "75e799e2-55ce-553a-8fdf-a74c5cf0de2c"),
    "DH Audio Spectrum Points": ("GeometryNodeTree", 285, "bb4cca6c-c5d5-52c9-80fb-754adc068f91"),
    "DH Audio Spectrum Bars": ("GeometryNodeTree", 350, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Spectrum Instances": ("GeometryNodeTree", 315, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Spectrum Curve": ("GeometryNodeTree", 310, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Spectrum Fill": ("GeometryNodeTree", 290, "de47b34b-1184-5bc8-84ac-3c5ada05f601"),
    "DH Audio Material Reader": ("ShaderNodeTree", 300, "1a181044-5483-5a07-ad44-2025bf0459e4"),
    "DH Audio Shader Response": ("ShaderNodeTree", 285, "1a181044-5483-5a07-ad44-2025bf0459e4"),
}

INTERNAL_GROUPS = {
    "DH Internal - Store Spectrum Attributes",
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

EXPECTED_PANELS = {
    "DH Audio Analyzer": {
        "Audio": False,
        "Spectrum": False,
        "Response": False,
        "Carrier": True,
        "Primary Outputs": False,
        "Frequency Metadata": True,
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

        nodes = sorted((node.name, node.bl_idname) for node in tree.nodes)
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


def _audit_interface(report):
    report.check("Blender 5.2 or newer", bpy.app.version >= (5, 2, 0), bpy.app.version_string)
    report.check("All public groups generated", all(bpy.data.node_groups.get(name) for name in PUBLIC_GROUPS))
    report.check("All internal groups generated", all(bpy.data.node_groups.get(name) for name in INTERNAL_GROUPS))

    asset_names = {tree.name for tree in bpy.data.node_groups if tree.asset_data}
    report.check("Exactly 15 public assets", asset_names == set(PUBLIC_GROUPS), sorted(asset_names))

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
        ("DH Audio Spectrum Bars", "Bar Profile"): "Box",
        ("DH Audio Spectrum Curve", "Curve Style"): "Smooth",
        ("DH Audio Response", "Gain"): 1.0,
        ("DH Audio Response", "Floor"): 0.0,
        ("DH Audio Response", "Ceiling"): 0.8,
        ("DH Audio Response", "Clamp to 1"): True,
        ("DH Audio Response", "Response"): 0.7,
        ("DH Audio Temporal Response", "Attack"): 0.05,
        ("DH Audio Temporal Response", "Release"): 0.25,
        ("DH Audio Shader Response", "Gain"): 1.0,
        ("DH Audio Shader Response", "Floor"): 0.0,
        ("DH Audio Shader Response", "Ceiling"): 0.8,
        ("DH Audio Shader Response", "Clamp to 1"): True,
        ("DH Audio Shader Response", "Response"): 0.7,
    }
    for (group_name, socket_name), expected in defaults.items():
        item = _interface_socket(bpy.data.node_groups[group_name], socket_name)
        actual = _default_value(item)
        equal = abs(actual - expected) < 1e-5 if isinstance(expected, float) else actual == expected
        report.check(f"{group_name}: {socket_name} default", equal, actual)

    boolean_inputs = {
        ("DH Audio Analyzer", "Use Scene Time"),
        ("DH Audio Analyzer", "All Channels"),
        ("DH Audio Analyzer", "Logarithmic"),
        ("DH Audio Analyzer", "Clamp to 1"),
        ("DH Audio Bands", "Store on Points"),
        ("DH Audio Bands", "Store on Instances"),
        ("DH Audio Spectrum Instances", "Realize Instances"),
        ("DH Audio Material Reader", "Use Instancer"),
        ("DH Audio Shader Response", "Clamp to 1"),
    }
    for group_name, socket_name in boolean_inputs:
        item = _interface_socket(bpy.data.node_groups[group_name], socket_name)
        report.check(f"{group_name}: {socket_name} is Boolean", item.socket_type == "NodeSocketBool", item.socket_type)


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
    tree.links.new(_socket(metadata.outputs, "Geometry"), _socket(temporal.inputs, "Spectrum"))
    output_store = _store_attribute(
        tree,
        _socket(temporal.outputs, "Spectrum"),
        _socket(temporal.outputs, "Amplitude"),
        "dh_test_temporal_output",
    )
    tree.links.new(_socket(output_store.outputs, "Geometry"), _socket(group_out.inputs, "Geometry"))

    obj = _new_host("DH Test Temporal Response Host", tree)
    values = {}
    metadata_preserved = True
    output_field_matches = True
    for frame in range(1, 31):
        snapshot = _snapshot(obj, frame)
        values[frame] = snapshot["attributes"]["dh_audio_amp"][0]
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

    sample_previous = bpy.data.node_groups["DH Audio Temporal Response"].nodes.get("Sample Previous Band")
    report.check(
        "Temporal Response does not clamp new band indices",
        sample_previous is not None and sample_previous.bl_idname == "GeometryNodeSampleIndex" and not sample_previous.clamp,
        None if sample_previous is None else sample_previous.clamp,
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
        "timeline_requirement": "Play sequentially or bake/cache; an uncached forward jump advances one simulation step.",
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
        report.check("Exactly 19 generated groups", len([tree for tree in bpy.data.node_groups if tree.name in PUBLIC_GROUPS or tree.name in INTERNAL_GROUPS]) == 19, len(bpy.data.node_groups))
        handler_count = sum(1 for handler in bpy.app.handlers.save_post if getattr(handler, "__name__", "") == "_dh_audio_write_catalogs_on_save")
        report.check("Exactly one toolkit save handler", handler_count == 1, handler_count)

        report.section("Interface audit completed", lambda: _audit_interface(report))

        _write_test_wav(test_wav)
        sound = bpy.data.sounds.load(str(test_wav), check_existing=False)
        bpy.context.scene.render.fps = 24
        bpy.context.scene.render.fps_base = 1.0

        report.section("Analyzer tests completed", lambda: _test_analyzer(report, sound))
        report.section("Temporal Response tests completed", lambda: _test_temporal_response(report))
        report.section("Named-band tests completed", lambda: _test_bands(report, sound))
        report.section("Sample Range and Band Query tests completed", lambda: _test_sample_range_and_query(report, sound))
        report.section("Visualizer tests completed", lambda: _test_visualizers(report, sound))
        report.section("Synthetic fill and curve tests completed", lambda: _test_synthetic_fill_and_curve(report))
        _remove_test_data()

    if release_path:
        release = _clean_release(repo_root, release_path)
        report.observations["release"] = release
        report.check("Release contains no scene objects", release["objects"] == 0, release)
        report.check("Release contains 19 generated groups", release["node_groups"] == 19, release)
        report.check("Release contains 15 public assets", release["assets"] == 15, release)
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
        raise SystemExit(1)


if __name__ == "__main__":
    main()
