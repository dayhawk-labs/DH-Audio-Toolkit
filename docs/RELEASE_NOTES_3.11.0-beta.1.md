# DH Audio Toolkit 3.11.0-beta.1

This peer beta keeps the established public group names and standardized
attributes while adding the first reusable mesh and shader-coordinate effects.

## Added

- `DH Audio Mesh Deform`: point-domain deformation with per-element Band,
  Selection, normal/direction modes, stereo-aware Audio Source, diagnostic
  fields, and Spectrum Bridge attribute storage.
- `DH Audio Mesh Extrude`: face-domain normal or direction extrusion, audio
  top scaling, Top/Side fields, stereo-aware Audio Source, and propagation of
  the complete standard spectrum/stereo schema to generated faces.
- `DH Audio Shader UV Transform`: factor-driven offset, pivot scale, and Z
  rotation with effective-control outputs.
- A face-domain internal transport helper. It is implementation-only and is
  not exposed in the Asset Browser.
- Regression coverage for the new interfaces, field structures, menu defaults,
  mesh results, face attribute propagation, shader math, layout bounds, clean
  rebuilds, and release packaging.

## Blender 5.2 behavior that shapes the design

- A FLOAT Menu Switch does not preserve its enum when copied directly to a
  group interface. The generator uses a temporary GEOMETRY menu definition;
  the public menu still drives a FLOAT switch and defaults to Amplitude.
- Extrude Mesh cannot reliably accept both Offset and Offset Scale as dynamic
  alternatives on one node: a linked vector Offset wins. Mesh Extrude uses
  separate normal/individual and direction/region branches.
- Spectrum values are stored on the target face domain before extrusion so
  generated top and side faces inherit the same material-readable attributes.

## Known constraints

- Missing Sound is indistinguishable from silence inside Geometry Nodes.
- Left/Right Audio Source choices require a Stereo Analyzer carrier.
- Mesh Deform does not implicitly realize instances.
- Spectrum History and Temporal Response require sequential playback or a bake.
- Spectrum Fill consumes one ordered spectrum row; it does not connect History
  rows into a surface.
- Geometry Nodes fields have no direct general bridge into the Compositor. A
  future compositor layer needs explicit pass/image/scene-value transport.

See [BETA_QUICKSTART.md](BETA_QUICKSTART.md) for peer-testing workflows.
