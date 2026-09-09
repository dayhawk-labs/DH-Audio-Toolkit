# DH Audio Toolkit Agent Guide

This guide is the operational starting point for people and agents changing
DH Audio Toolkit. GitHub main is the source of truth; a local checkout is a
working copy only.

## Source of truth

| Surface | Owns |
| --- | --- |
| src/dh_audio_toolkit.py | Public interfaces, defaults, panels, descriptions, node layouts, and implementation graphs |
| tests/blender_52_regression.py | The 25 public assets, 7 internal groups, behavior, interface invariants, and release generation |
| tools/public_node_previews.json | Allowlisted public exterior-node captures and filenames |
| docs/nodes/ | Generated user and agent node reference |
| docs/images/node-previews/ | Reviewed public-interface screenshots |

Do not treat generated preview images as authoritative interface data. The
generated Blender interface and regression suite are authoritative.

## Compatibility invariants

- Public group names are compatibility-sensitive.
- Standard dh_audio attributes are the transport contract between analysis,
  geometry, and materials.
- Internal DH Internal groups are implementation details and must not become
  public assets or user documentation targets.
- Keep Geometry Nodes and Shader Nodes domains separate. Material Reader and
  Shader groups need Shader Node hosts when captured or tested.
- Simulation nodes require sequential evaluation or baking. Do not document
  instant historical/temporal results after a frame jump.

## Change workflow

1. Inspect the affected public interface and its existing regression coverage.
2. Change the generator and extend the Blender regression before changing
   documentation.
3. Rebuild with Blender 5.2 and inspect the generated public interface.
4. Capture the changed public node on the VPS with the allowlisted capture tool.
5. Export interfaces and regenerate the node reference:

~~~bash
blender --background "temp/DH Audio Toolkit <version>.blend" \
  --python tools/export_public_node_interfaces.py -- \
  --output temp/public_node_interfaces.json --expect 25
python3 tools/build_public_node_reference.py \
  --interfaces temp/public_node_interfaces.json \
  --manifest tools/public_node_previews.json \
  --output-dir docs/nodes
~~~

6. Review the generated page, screenshot, README links, and exact diff.
7. Run static tests locally and let GitHub run Blender regression and generated
   asset validation. Do not create a release for documentation-only work.

## Visual review rules

- Public screenshots show one exterior group node, never its internal graph.
- Every input/output must be visible, including lower output panels on tall
  nodes.
- Keep a small, consistent border; reject blank, clipped, or splash-screen
  captures.
- Default-open panels should explain the primary workflow. Keep advanced
  controls collapsed unless a user needs them often.
- Use the screenshot to catch unhelpful width, clipping, excessive empty space,
  misleading grouping, or a control that should be surfaced in documentation.

## Useful system map

~~~text
Analyzer or Stereo Analyzer
  -> Spectrum Points or Stereo Points
  -> Curve, Fill, History, Radial Spectrum, Instances, custom geometry

Analyzer-compatible carrier
  -> Band Query or Spectrum Sample
  -> Spectrum Bridge, Mesh Deform, Mesh Extrude

Geometry attributes
  -> Material Reader
  -> Shader Response, Shader Map, Shader UV Transform
~~~

For user-facing socket details, use the [Public Node Reference](nodes/README.md).
