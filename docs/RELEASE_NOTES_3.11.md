# DH Audio Toolkit 3.11

This release keeps the established public group names and standardized
attributes while adding reusable mesh and shader-coordinate effects.

## Added

- `DH Audio Mesh Deform`: point-domain deformation with per-element Band,
  Selection, normal/direction modes, stereo-aware Audio Source, diagnostic
  fields, and Spectrum Bridge attribute storage.
- `DH Audio Mesh Extrude`: face-domain normal or direction extrusion, audio
  top scaling, Top/Side fields, stereo-aware Audio Source, and propagation of
  the complete standard spectrum/stereo schema to generated faces.
- `DH Audio Shader UV Transform`: factor-driven offset, pivot scale, and Z
  rotation with effective-control outputs.
- A face-domain internal transport helper and expanded Blender 5.2 regression
  coverage for the new interfaces and release packaging.

## Compatibility

Requires Blender 5.2 or newer. Keep the released `.blend` beside
`blender_assets.cats.txt` in the same asset-library folder.

See [the quickstart](BETA_QUICKSTART.md) and [the recipe guide](RECIPES.md)
for usage examples.
