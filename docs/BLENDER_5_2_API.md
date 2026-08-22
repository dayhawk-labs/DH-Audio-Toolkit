# Blender 5.2 API Notes

Runtime baseline: Blender 5.2.0 LTS, `blender-v5.2-release`.

These notes record API details verified in a live Blender 5.2 instance while
building and functionally testing `src/dh_audio_toolkit.py`. Prefer these exact
identifiers and values over older Geometry Nodes examples.

## Sample Sound Frequencies

- Node identifier: `GeometryNodeSampleSoundFrequencies`
- Output: `Amplitude` (`NodeSocketFloat`)
- Inputs, in order:
  - `Sound` (`NodeSocketSound`)
  - `Time` (`NodeSocketFloatTimeAbsolute`)
  - `All Channels` (`NodeSocketBool`)
  - `Channel` (`NodeSocketInt`)
  - `Low` (`NodeSocketFloatFrequency`)
  - `High` (`NodeSocketFloatFrequency`)
  - `FFT Size` (`NodeSocketMenu`)
  - `Window Function` (`NodeSocketMenu`)
- Valid FFT menu values:
  - `128`, `256`, `512`, `1024`, `2048`, `4096`, `8192`, `16384`, `32768`
- Valid window menu values:
  - `Hann`, `Hamming`, `Blackman`, `Rectangular`
- FFT Size and Window Function are input sockets, not writable RNA properties
  on the node.
- `Low` and `High` accept fields. A single Sample Sound Frequencies node can
  therefore evaluate different frequency ranges on different carrier points.
  DH Audio Analyzer and DH Audio Bands both use this field-driven behavior.

## Runtime menu sockets and group interfaces

Blender 5.2 menu definitions are runtime data. Create a real source node, then
copy its menu socket into the group interface:

```python
source_socket.default_value = "Smooth"
interface_socket = tree.interface.new_socket(
    name="Curve Style",
    in_out="INPUT",
    socket_type="NodeSocketMenu",
)
interface_socket.from_socket(source_node, source_socket)
```

Important behavior verified in 5.2:

- Set the source node socket's `default_value` before calling `from_socket()`.
- Setting `GeometryNodeMenuSwitch.active_index` does not set the Menu input
  socket's default value.
- Assigning a custom interface menu default after `from_socket()` can silently
  produce an empty string, even when the intended label is valid.
- Always instantiate a group node during validation and inspect the actual
  `NodeSocketMenu.default_value`. Inspecting only the interface object can miss
  a blank menu shown to users.

The toolkit's verified defaults are:

- FFT Size: `8192`
- Window Function: `Hann`
- Bar Profile: `Box`
- Curve Style: `Smooth`

## Menu Switch

- Node identifier: `GeometryNodeMenuSwitch`
- Set `data_type` before adding items.
- Custom items are managed through `node.enum_items`.
- The selector is the `Menu` input (`NodeSocketMenu`).
- For the geometry variant, each custom item adds a geometry input and a
  Boolean item output; the selected geometry is returned through `Output`.

## Resample Curve

- Node identifier: `GeometryNodeResampleCurve`
- Blender 5.2 exposes the resampling mode as the `Mode` menu input.
- Use the exact menu value `Count` for count-based resampling.
- Inputs present in the tested build: `Curve`, `Selection`, `Mode`, `Count`,
  and `Length`.
- Do not use older examples that assign a `mode` RNA property. The tested node
  has no writable `mode`; it does retain the RNA property `keep_last_segment`.

## Curve to Mesh

- Node identifier: `GeometryNodeCurveToMesh`
- Inputs: `Curve`, `Profile Curve`, `Scale`, and `Fill Caps`.
- `Scale` is a float field. DH Audio Spectrum Curve uses it for per-point
  audio-reactive tube thickness.
- `Fill Caps` is a Boolean input socket in the tested build.

## Sample Index

- Node identifier: `GeometryNodeSampleIndex`
- `data_type`, `domain`, and `clamp` remain writable RNA properties.
- `clamp = True` clamps negative and out-of-range indices to the nearest valid
  element. DH Audio Band Query was verified with `-5`, `7`, and `999`.

## Curve Line

- Node identifier: `GeometryNodeCurvePrimitiveLine`
- `mode` remains a writable RNA property in 5.2.
- `mode = "POINTS"` enables the `Start` and `End` inputs and disables
  `Direction` and `Length`.

## Curve evaluation in regression tests

- Curve components returned directly from a Geometry Nodes modifier on a mesh
  object are not represented as vertices by `bpy.data.meshes.new_from_object`.
- To inspect evaluated curve positions as mesh data, use:
  - `GeometryNodeCurveToPoints` with `mode = "EVALUATED"`
  - `GeometryNodePointsToVertices`
- `GeometryNodeCurveToPoints` outputs `Points`, `Tangent`, `Normal`, and
  `Rotation`. Its tested inputs are `Curve`, `Count`, and `Length`.
- `GeometryNodePointsToVertices` accepts `Points` and `Selection`, and outputs
  `Mesh`.
- This explicit conversion is used by the regression suite to measure native
  Catmull-Rom baseline undershoot without adding a tube profile that would
  distort the measured minimum Z value.

## Mesh Grid indexing

- Node identifier: `GeometryNodeMeshGrid`
- With `Vertices Y = 2`, vertex indices advance in Y first.
- For a two-row strip:
  - source band index: `Index // 2`
  - row index: `Index % 2`
  - row `0` is the bottom row and row `1` is the top row
- A five-point test with top heights `[1, 0, 1.5, 0, 1]` produced ten grid
  vertices paired by X and retained both quiet intermediate top points.

## Interface socket subtypes

`NodeTreeInterface.new_socket(socket_type=...)` accepts base socket identifiers.
For float presentation/unit types, create `NodeSocketFloat` and set `subtype`.
Verified examples:

- `subtype = "TIME_ABSOLUTE"` -> group nodes expose
  `NodeSocketFloatTimeAbsolute`
- `subtype = "FREQUENCY"` -> `NodeSocketFloatFrequency`
- `subtype = "DISTANCE"` -> `NodeSocketFloatDistance`

## Attributes, fields, and instances

- Analyzer attributes stored on the carrier point domain propagate through
  Instance on Points and remain present after Realize Instances.
- Store Named Attribute on the `INSTANCE` domain creates values that are
  readable in the instancer context before realization. This was verified by
  reading a stored value with Named Attribute and using it to scale instances.
- An instance-domain value alone should not be expected to become the same
  point-domain value after Realize Instances; it evaluated as zero in that
  specific test.
- DH Audio Bands defaults to storing named bands on both points and instances.
  With both enabled, named values remain available on realized point geometry
  and in the instancer context used by DH Audio Material Reader.

## Other verified Blender 5.2 identifiers

- Eevee render engine enum: `BLENDER_EEVEE`
- Geometry Nodes tree: `GeometryNodeTree`
- Shader Nodes tree: `ShaderNodeTree`
- Geometry group node: `GeometryNodeGroup`
- Shader group node: `ShaderNodeGroup`
- Asset catalog assignment: `node_tree.asset_data.catalog_id`
- Default group-node width: `node_tree.default_group_node_width`

## Baseline observations

- Scene Time, custom Time, Time Offset, All Channels, and individual stereo
  channel selection all changed Sample Sound Frequencies results as expected.
- Linear and logarithmic frequency maps produced contiguous boundaries ending
  at the requested maximum frequency.
- Catmull-Rom smoothing can overshoot below a flat baseline around sharp quiet
  valleys. This is native smoothing behavior, not a sampling or topology loss.
- Opening a saved test file required a frame change before the audio-dependent
  dependency graph refreshed in the connected test session.
