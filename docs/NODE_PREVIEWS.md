# Public Node Previews

The images under `docs/images/node-previews/` document the exterior interfaces
of all 25 approved public Geometry Node and Shader Node groups. They are
intended for users deciding which node group to add and how to connect it; they
do not show internal node routing.

## Approved scope

[`tools/public_node_previews.json`](../tools/public_node_previews.json) is the
allowlist. It maps stable public-group IDs to their Blender group names and
checked-in PNG filenames. Do not add internal groups to this manifest.

## Capture workflow

Capture runs on the desktop-capable VPS using Blender 5.2 and the reusable
private tool at `dayhawk-labs/blender-node-previews`. GitHub Actions remains
the source of truth for code validation; it does not run Blender UI capture.

From a clean DH Audio Toolkit checkout, first rebuild a source `.blend` from
the current checkout. This uses the same generator/regression entry point as
the repository CI:

```bash
version="$(tr -d '\r\n' < VERSION)"
mkdir -p temp
/opt/dh-audio-tools/blender/blender --background --factory-startup \
  --python tests/blender_52_regression.py -- \
  --release "temp/DH Audio Toolkit ${version}.blend"
```

Then run the capture:

```bash
BLENDER=/opt/dh-audio-tools/blender/blender \
BLEND_FILE="/path/to/DH-Audio-Toolkit/temp/DH Audio Toolkit ${version}.blend" \
MANIFEST=/path/to/DH-Audio-Toolkit/tools/public_node_previews.json \
OUTPUT_DIR=/path/to/DH-Audio-Toolkit/docs/images/node-previews \
/path/to/blender-node-previews/examples/capture-manifest.sh
```

The reusable tool creates a temporary node tree containing one allowlisted
public group at a time in its matching Geometry Nodes or Shader Nodes domain.
It fullscreens the Node Editor, waits for the complete node bounds to settle,
then crops the final Blender-window capture with a small uniform margin.

## Regenerate the node reference

After captures are reviewed, export the public Blender interfaces and rebuild
the Markdown knowledge base:

~~~bash
/opt/dh-audio-tools/blender/blender --background \
  "temp/DH Audio Toolkit <version>.blend" \
  --python tools/export_public_node_interfaces.py -- \
  --output temp/public_node_interfaces.json --expect 25
python3 tools/build_public_node_reference.py \
  --interfaces temp/public_node_interfaces.json \
  --manifest tools/public_node_previews.json \
  --output-dir docs/nodes
~~~

The resulting [Public Node Reference](nodes/README.md) contains one page per
public node, with its captured image, verified inputs and outputs, panel
defaults, descriptions, and agent notes.

## Review before committing

For every changed image, verify:

- the complete node, including bottom outputs, is visible;
- labels and socket names are sharp and readable;
- border space is small and consistent;
- no internal graph, local path, scene content, or unrelated UI is visible.

Commit reviewed PNGs with the matching source/interface change. Do not treat
these captures as release assets until they have been reviewed in GitHub.
