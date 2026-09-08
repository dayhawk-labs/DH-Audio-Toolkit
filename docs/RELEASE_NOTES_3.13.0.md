# DH Audio Toolkit 3.13.0

## Added

- **DH Audio Spectrum History** now has an optional **Surface** output that
  connects retained spectrum rows into a quad waterfall mesh.
- Surface generation is disabled by default, so existing History point-row
  workflows remain unchanged.
- **Row Decimation** defaults to `1` and can retain every Nth history row when
  a lower-density surface is preferable.
- The Surface output retains the standard spectrum and history attributes, so
  it works with the existing Material Reader and downstream geometry tools.

## Compatibility

Requires Blender 5.2 or newer. Existing graphs using the **History** output
retain their original geometry, attributes, and bounded simulation behavior.
Play sequentially or bake Spectrum History before relying on a complete
waterfall surface.
