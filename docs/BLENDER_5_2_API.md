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
- `Channel` also accepts and evaluates an integer field when `All Channels` is
  false. This was verified with a two-point stereo WAV probe: point 0 sampled
  channel 0 and point 1 sampled channel 1 through one node, producing the
  expected low-frequency amplitude ratio above 800,000:1. DH Audio Stereo
  Analyzer therefore uses one sampler across its joined Left/Right carriers.
- A joined two-row carrier keeps each Mesh Line's internal edges, but evaluated
  Join Geometry point order should not be treated as a public contract. Use the
  stored `dh_audio_channel` attribute to identify Left and Right downstream.

## Shader scalar mapping

- Map Range node identifier: `ShaderNodeMapRange`.
- With `data_type = "FLOAT"`, the scalar inputs are `Value`, `From Min`,
  `From Max`, `To Min`, `To Max`, and `Steps`; the scalar output is `Result`.
- Clamp remains the Boolean RNA property `node.clamp`, not an input socket.
  A node group that needs a field-linkable or checkbox-controlled clamp must
  therefore select between unclamped and clamped math explicitly.
- Blender 5.2's `ShaderNodeMath.operation` includes the identifiers
  `ABSOLUTE`, `SIGN`, and `POWER`. DH Audio Shader Map combines these as
  `sign(value) * pow(abs(value), curve)` so unclamped negative values remain
  defined with fractional response exponents.

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

## Domain Size

- Node identifier: `GeometryNodeAttributeDomainSize`
- The geometry component is selected through the writable `component` RNA
  property. DH Audio Radial Spectrum uses `component = "MESH"`.
- Input: `Geometry`.
- Mesh outputs: `Point Count`, `Edge Count`, `Face Count`, and
  `Face Corner Count`.
- `Spline Count`, `Instance Count`, and `Layer Count` are present but disabled
  when the component is `MESH`.
- For a cyclic N-point radial layout, divide point Index by `Point Count` to
  generate N unique angles. Dividing by `Point Count - 1` duplicates the first
  and last positions when Sweep Angle is 360 degrees.

## Set Spline Cyclic

- Node identifier: `GeometryNodeSetSplineCyclic`
- Inputs: `Curve`, `Selection`, and `Cyclic`; output: `Curve`.
- `Cyclic` is a Boolean input socket, not a node RNA toggle.
- In the eight-point radial prototype, a triangular-profile Curve to Mesh
  produced 24 faces with Cyclic enabled and 21 faces when open. This confirms
  that the node adds a real closing segment rather than merely overlapping
  endpoint positions.
- DH Audio Radial Spectrum first maps the carrier mesh, converts its edges with
  `GeometryNodeMeshToCurve`, then applies Set Spline Cyclic. The mapped mesh
  points remain available as a separate output.

## Radial spectrum endpoint policy

Use different denominators for cyclic layouts and open arcs:

- Cyclic: `Index / max(Point Count, 1)` gives unique positions around the
  sweep; Set Spline Cyclic supplies the final closing segment.
- Open: `Index / max(Point Count - 1, 1)` places the first and final points
  exactly on both requested angular endpoints.

The `max(..., 1)` guards keep a one-point carrier finite. Mesh-to-curve and
Set Position preserved the tested `dh_audio_amp`, `dh_audio_band_index`, and
`dh_audio_band_pos` attributes.

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

## Simulation Zones

- Node identifiers:
  - `GeometryNodeSimulationInput`
  - `GeometryNodeSimulationOutput`
- Pair the nodes with `simulation_input.pair_with_output(simulation_output)`.
- Blender 5.2 exposes the paired node through the read-only
  `simulation_input.paired_output` pointer. Older examples that inspect an
  `output_node_id` property do not apply; that property is absent in the
  tested runtime.
- Simulation state items are managed through
  `simulation_output.state_items`. A new output contains one `GEOMETRY` item
  by default. Items expose `name`, `socket_type`, and `attribute_domain`.
- Simulation Input exposes `Delta Time`, followed by the paired state outputs.
  Simulation Output exposes `Skip`, followed by the paired state inputs and
  outputs.
- A Simulation Zone works inside a nested reusable Geometry Node group used by
  a modifier. DH Audio Temporal Response uses this arrangement.
- Uncached forward timeline jumps advance one simulation step; they do not
  reconstruct every skipped frame. Sequential playback or a simulation bake
  is required for complete temporal history.
- When matching state by band index across changing carrier topology, use
  `GeometryNodeSampleIndex.clamp = False`. With clamping enabled, newly added
  bands inherit the previous final band's value. With clamping disabled,
  invalid previous indices evaluate to zero.
- `GeometryNodeJoinGeometry` with no connected inputs evaluates as empty
  geometry. DH Audio Spectrum History uses this as its initial simulation
  state so the first evaluated frame is not duplicated.
- A bounded history can store joined mesh rows directly in the geometry state.
  Offsetting the previous state, joining the current row, and deleting expired
  points preserves separate row edges even when the point count changes between
  frames.

## Delete Geometry

- Node identifier: `GeometryNodeDeleteGeometry`
- Inputs: `Geometry`, `Selection`; output: `Geometry`.
- `domain` and `mode` remain writable RNA properties in Blender 5.2; they are
  not menu input sockets in the tested runtime.
- Tested defaults: `domain = "POINT"`, `mode = "ALL"`.
- Tested domain values include `POINT`, `EDGE`, `FACE`, `CURVE`, `INSTANCE`,
  and `LAYER`.
- Tested mode values are `ALL`, `EDGE_FACE`, and `ONLY_FACE`.
- DH Audio Spectrum History uses `domain = "POINT"` and `mode = "ALL"` to
  remove every point whose stored age is greater than or equal to `Frames`.

## Named-attribute field evaluation context

Named Attribute fields are evaluated in the geometry context of the node that
consumes them. This matters when a graph reads an attribute, modifies it with
Store Named Attribute, and then reuses the earlier field expression downstream.

In the live Spectrum History prototype, reusing `old_index + 1` after storing
the new index caused it to evaluate against the already modified geometry and
increment a second time. The correct pattern is:

1. Read the old named attribute and calculate the new value for Store Named
   Attribute.
2. After that store, use a separate Named Attribute node to re-read the stored
   value for normalization, comparisons, and deletion.

This produced exact bounded ages `0 .. Frames - 1`, including the `Frames = 1`
case, and remained correct while the source topology changed.

## Node Editor context

- `SpaceNodeEditor` in the tested 5.2 runtime does not expose the older
  `geometry_nodes_type` property.
- Relevant properties include `tree_type`, `node_tree_sub_type`, `node_tree`,
  the read-only `edit_tree`, and `pin`.
- Setting an area to `NODE_EDITOR`, assigning `area.ui_type =
  "GeometryNodeTree"`, and making an object with the target Nodes modifier
  active was sufficient for `edit_tree` to resolve to that geometry group.

## Node dimensions and layout validation

- `Node.dimensions` is not a reliable generator-time layout source. In a
  background build, or before a tree has been displayed, it can be zero or
  stale.
- After assigning `SpaceNodeEditor.node_tree`, forcing a redraw populates the
  rendered dimensions. Those values are expressed at the current UI scale;
  `dimensions.x / width` was approximately `1.94444` in the validation UI.
- `Node.location_absolute` is useful for a live visual audit because it
  resolves frame-relative child locations. Sibling collision checks can then
  compare rendered dimensions after dividing by the observed UI scale.
- The canonical generator therefore uses conservative logical heights derived
  from visible socket rows and native-node minimums. It stores those bounds on
  generated nodes so the headless regression suite can enforce deterministic
  non-overlap. A connected-UI audit separately verifies the real drawn bounds.

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
- An instance-domain float stored immediately before Realize Instances
  propagated to every realized mesh vertex in the Blender 5.2 regression.
- A disabled point-domain Store Named Attribute chain implemented only by a
  false `Selection` can still create a zero-valued point attribute. That value
  shadows the same-named instance attribute after realization. A Geometry
  Switch must bypass the disabled writer chain completely when domain toggles
  are expected to preserve instance-to-realized propagation. DH Audio Spectrum
  Bridge uses this bypass design for both storage domains.
- DH Audio Bands defaults to storing named bands on both points and instances.
  With both enabled, named values remain available on realized point geometry
  and in the instancer context used by DH Audio Material Reader.

## Store Named Attribute domain controls

- Node identifier: `GeometryNodeStoreNamedAttribute`
- Verified RNA properties: `data_type` and `domain`.
- Relevant `domain` values include `POINT` and `INSTANCE`.
- Verified input sockets are `Geometry`, `Selection`, `Name`, and `Value`;
  the geometry output is named `Geometry`.
- Point and instance writers may store the same attribute name. The active
  field context determines how Band, Index, ID, and Selection evaluate on each
  domain.
- When both domains are enabled, a topology-dependent Band field can produce
  different values on points and instances. Use an explicit stable ID or band
  field when both copies must match element-for-element.

## Field-driven Sample Index lookup

- Node identifier: `GeometryNodeSampleIndex`
- Verified RNA properties: `data_type`, `domain`, and `clamp`.
- For spectrum carriers, use `domain = "POINT"` and `clamp = True`.
- A group interface integer socket with `structure_type = "FIELD"` can drive
  Sample Index's `Index` input from the downstream evaluation context.
- Sampled outputs also remain fields when their interface sockets use
  `structure_type = "FIELD"`.
- A live prototype sampled a four-point carrier over six target points with
  `Band = Index modulo 4`, producing the expected repeating sequence. This is
  the Blender 5.2 basis for `DH Audio Spectrum Sample`; it reuses carrier
  attributes and does not add another audio sampler.
- The same sequence was verified through `DH Audio Spectrum Bridge` on target
  points and on instances. Instance-domain values drove Scale Instances before
  realization and propagated to the realized mesh when the disabled point
  writer chain was bypassed with a Geometry Switch.

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
