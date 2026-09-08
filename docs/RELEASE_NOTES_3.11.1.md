# DH Audio Toolkit 3.11.1

This patch release makes the 3.11 distribution reproducible from its tagged
source. It contains no node-group or attribute-schema changes.

## Fixed

- Release ZIPs exclude Blender `.blend1` and later recovery backups.
- Packaging validates the exact asset-library archive manifest before upload.
- Releases include a SHA-256 checksum for the ZIP download.

## Compatibility

Requires Blender 5.2 or newer. Existing 3.11 node graphs remain compatible.
Keep the released `.blend` beside `blender_assets.cats.txt` in the same
asset-library folder.

See the [quickstart](BETA_QUICKSTART.md) and [recipe guide](RECIPES.md) for
usage examples.
