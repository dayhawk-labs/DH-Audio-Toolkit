"""Build the checked-in public-node reference from Blender interface JSON.

The JSON input comes from export_public_node_interfaces.py running against a
freshly generated blend. This keeps sockets, defaults, panels, and descriptions
grounded in the actual Blender interface.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


GUIDANCE = {
    "DH Audio Analyzer": ("Analysis", [
        "Start modular geometry workflows here. Spectrum carries the standard dh_audio schema.",
        "Use Spectrum Points before Curve or Fill; use Spectrum Bars for a self-contained visualizer.",
    ]),
    "DH Audio Stereo Analyzer": ("Analysis", [
        "Use this when left and right channels need different behavior. Feed its separate outputs to Stereo Points or mono-compatible consumers.",
        "The combined Stereo Spectrum contains two carrier rows; it is not a single mono row.",
    ]),
    "DH Audio Bands": ("Analysis", [
        "Use named musical ranges when fixed musical regions are clearer than arbitrary band indices.",
        "Use its attribute bridge when values must survive into geometry or materials; use direct outputs for immediate fields.",
    ]),
    "DH Audio Sample Range": ("Analysis", [
        "Choose this for one custom frequency range rather than a full carrier. It is deliberately scalar-first.",
        "For many independently sampled bands, prefer Spectrum Sample over duplicating this node.",
    ]),
    "DH Audio Frequency Map": ("Utilities", [
        "Band Index is zero-based. Keep Min Frequency below Max Frequency and enable Logarithmic for perceptual spacing.",
        "Most users should let Analyzer handle this; use it directly only for a custom carrier or frequency-aware effect.",
    ]),
    "DH Audio Frequency Selection": ("Utilities", [
        "Requires spectrum geometry with dh_audio_center_hz, normally from Analyzer or a compatible carrier.",
        "Use Selection on downstream Selection inputs to target a physical frequency range without relying on band count.",
    ]),
    "DH Audio Band Query": ("Query", [
        "Band is zero-based and clamps safely to the available range.",
        "Use Spectrum Sample instead when Band must vary per point, face, curve point, or instance.",
    ]),
    "DH Audio Spectrum Sample": ("Query", [
        "Band is a field, so it can vary on the downstream evaluation domain.",
        "It reads fields but does not write attributes. Pair it with Spectrum Bridge when a material needs sampled values later.",
    ]),
    "DH Audio Spectrum Bridge": ("Transport", [
        "Use this to stamp standard mono and stereo attributes onto arbitrary geometry or instances.",
        "Choose storage domains deliberately. Material Reader needs attributes on the geometry or instancer path it reads.",
    ]),
    "DH Audio Mesh Deform": ("Transport", [
        "Band and Selection evaluate per point. Use Normals for surface-following displacement or Direction for an explicit vector.",
        "Enable storage only when downstream geometry or materials need standard attributes after deformation.",
    ]),
    "DH Audio Mesh Extrude": ("Transport", [
        "Band and Selection evaluate per face. Normal mode treats faces independently; Direction mode moves the connected selected region.",
        "Use Top and Side outputs to assign materials or process the extrusion result selectively.",
    ]),
    "DH Audio Response": ("Utilities", [
        "This is stateless scalar shaping. Use it wherever a positive value needs gain, normalization, clamp, and a power response.",
        "Use Temporal Response instead when frame-to-frame smoothing or peak state is required.",
    ]),
    "DH Audio Temporal Response": ("Temporal", [
        "This is stateful: evaluate sequential timeline frames or bake the simulation before expecting complete temporal behavior.",
        "Peak Hold is enabled by default. dh_audio_amp remains live smoothed amplitude; dh_audio_peak and Peak are the held marker.",
    ]),
    "DH Audio Spectrum History": ("Temporal", [
        "This is stateful: play sequentially or bake it. A frame jump into a fresh simulation has no earlier rows to retain.",
        "Surface is disabled by default. Enable it only for a connected waterfall mesh, then use Row Decimation to control density.",
    ]),
    "DH Audio Spectrum Points": ("Mapping", [
        "This is the normal bridge from Analyzer carrier geometry to visible, positioned points.",
        "Spectrum Points is the intended input for Curve, Fill, History, and many custom geometry workflows.",
    ]),
    "DH Audio Stereo Points": ("Mapping", [
        "It mirrors left and right around a shared baseline and preserves separate outputs for downstream consumers.",
        "Feed one channel at a time to mono-only consumers, or keep the combined result for a mirrored display.",
    ]),
    "DH Audio Radial Spectrum": ("Mapping", [
        "Use positioned Spectrum Points when source height should be retained; use a raw carrier for a clean radial layout.",
        "Cyclic closes the optional curve. Open arcs respect Start Angle and Sweep Angle endpoints.",
    ]),
    "DH Audio Spectrum Bars": ("Visualizers", [
        "This includes its own analyzer and is the fastest way to get a bar visualizer.",
        "Use its Spectrum Points output for Curve or Fill. Choose Bar Profile before supplying custom geometry.",
    ]),
    "DH Audio Spectrum Instances": ("Visualizers", [
        "Use this when every band should instance your own geometry. The input instance is reused, not automatically realized.",
        "Keep attributes on the instance domain when Material Reader must access them with Use Instancer enabled.",
    ]),
    "DH Audio Spectrum Curve": ("Visualizers", [
        "Feed ordered positioned points from Spectrum Points or Spectrum Bars.",
        "Smooth plus Resample changes point count; use it when even topology is more important than original per-band points.",
    ]),
    "DH Audio Spectrum Fill": ("Visualizers", [
        "Feed positioned, ordered Spectrum Points. It creates a quad strip down to Baseline.",
        "Use the output for a silhouette; use Curve when only a line or tube is needed.",
    ]),
    "DH Audio Material Reader": ("Shaders", [
        "Use Instancer off for realized geometry and on when the shader reads attributes carried by Geometry Nodes instances.",
        "This is the material-side entry point for spectrum, stereo, temporal peak, history, and named-band schemas.",
    ]),
    "DH Audio Shader Response": ("Shaders", [
        "This is the material-side, stateless counterpart to DH Audio Response.",
        "Feed a scalar such as Material Reader Amplitude, Peak, History Position, or a named band.",
    ]),
    "DH Audio Shader Map": ("Shaders", [
        "Set From Min and From Max to the meaningful source range before shaping. Clamp and Invert act on the normalized factor.",
        "Use this before Shader UV Transform when a raw audio value needs a controlled mapping range.",
    ]),
    "DH Audio Shader UV Transform": ("Shaders", [
        "Feed coordinates plus a scalar Factor. Base controls are always applied; Audio controls are multiplied by Factor.",
        "Use Effective outputs for debugging or for sharing the exact transformed values with other shader logic.",
    ]),
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interfaces", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/nodes"))
    return parser.parse_args()


def clean(value):
    return " ".join(("" if value is None else str(value)).replace("|", "\\|").split())


def default(value):
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "on" if value else "off"
    if isinstance(value, float):
        return f"{value:.4g}"
    return clean(value)


def slug_for(name, groups):
    for slug, group_name in groups.items():
        if group_name == name:
            return slug
    raise KeyError(f"node is not in manifest: {name}")


def sockets(node, direction):
    return [
        item for item in node["items"]
        if item["kind"] == "socket" and item["direction"] == direction
    ]


def socket_table(items):
    if not items:
        return "None."
    lines = [
        "| Panel | Socket | Type | Default | Description |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            "| {panel} | **{name}** | {kind} | {value} | {description} |".format(
                panel=clean(item["panel"] or "none"),
                name=clean(item["name"]),
                kind=clean(item["socket_type"]),
                value=default(item["default"]),
                description=clean(item["description"] or "none"),
            )
        )
    return "\n".join(lines)


def build_page(node, slug, filename):
    name = node["name"]
    category, notes = GUIDANCE[name]
    panels = [item for item in node["items"] if item["kind"] == "panel"]
    panel_lines = [
        f"- **{clean(panel['name'])}**: "
        f"{'collapsed by default' if panel['default_closed'] else 'open by default'}"
        + (f"; {clean(panel['description'])}" if panel["description"] else "")
        for panel in panels
    ]
    return f"""# {name}

![{name}](../images/node-previews/{filename})

**Category:** {category}<br>
**Blender domain:** {node['tree_type']}<br>
**Default node width:** {node['default_width']} px

{clean(node['description'])}

## Agent notes

{chr(10).join(f'- {note}' for note in notes)}

## Interface panels

{chr(10).join(panel_lines)}

## Inputs

{socket_table(sockets(node, 'INPUT'))}

## Outputs

{socket_table(sockets(node, 'OUTPUT'))}

## Verification source

This page was generated from the public Blender interface exported by
tools/export_public_node_interfaces.py against a fresh toolkit build. Update
the screenshot and regenerate this page whenever the public interface changes.
"""


def build_index(nodes, groups):
    lines = [
        "# Public Node Reference",
        "",
        "This reference is generated from public Blender interfaces. Each page",
        "pairs a captured exterior view with verified sockets, defaults,",
        "descriptions, and agent-facing workflow notes.",
        "",
        "| Node | Category | Summary |",
        "| --- | --- | --- |",
    ]
    for node in nodes:
        slug = slug_for(node["name"], groups)
        category, _notes = GUIDANCE[node["name"]]
        lines.append(
            f"| [{node['name']}]({slug}.md) | {category} | {clean(node['description'])} |"
        )
    lines.extend([
        "",
        "## Regeneration",
        "",
        "See Public Node Previews in the parent documentation. Rebuild the source",
        "blend, export temp/public_node_interfaces.json, then run this script.",
    ])
    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    interface_document = json.loads(args.interfaces.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    groups = manifest["groups"]
    files = manifest["files"]
    nodes = sorted(interface_document["nodes"], key=lambda node: node["name"])
    names = {node["name"] for node in nodes}
    if names != set(groups.values()):
        raise RuntimeError("interface export and public preview manifest disagree")
    if names != set(GUIDANCE):
        raise RuntimeError("agent guidance and exported nodes disagree")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for node in nodes:
        slug = slug_for(node["name"], groups)
        (args.output_dir / f"{slug}.md").write_text(
            build_page(node, slug, files[slug]), encoding="utf-8"
        )
    (args.output_dir / "README.md").write_text(build_index(nodes, groups), encoding="utf-8")
    print(f"DH_AUDIO_NODE_REFERENCE={{\"pages\": {len(nodes)}}}")


if __name__ == "__main__":
    main()
