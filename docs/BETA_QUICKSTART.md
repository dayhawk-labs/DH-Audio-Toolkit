# DH Audio Toolkit 3.12.0 quick start

Requires Blender 5.2 or newer. Keep the release `.blend` and its adjacent
`blender_assets.cats.txt` together in one Blender Asset Library folder.

## First working spectrum

1. Add `DH Audio Analyzer` in Geometry Nodes.
2. Select a Sound datablock and play the timeline.
3. Connect `Spectrum` to `DH Audio Spectrum Points`, then connect its
   `Spectrum Points` output to Curve, Fill, History, or a custom consumer.
4. For ready-made bars, use `DH Audio Spectrum Bars` directly; its
   `Spectrum Points` output remains compatible with Curve, Fill, and History.

No Sound produces zero amplitude. Blender does not expose a reliable
Geometry Nodes distinction between a missing sound and intentional silence,
so the toolkit cannot show an in-graph missing-sound warning.

## Drive your own mesh

Use one Analyzer carrier for many consumers.

- `DH Audio Mesh Deform` samples Band on points. Connect your geometry and the
  Analyzer `Spectrum`; use `Index modulo Bands` for repeating point mapping.
  Use Normals is on by default, or turn it off and supply Direction.
- `DH Audio Mesh Extrude` samples Band on faces. Normal mode extrudes each
  selected face independently. Direction mode extrudes the connected selected
  region along Direction. Top and Side outputs are anonymous selections for
  immediate Set Material or downstream operations.
- Both groups have an Audio Source menu. Left/Right choices require a carrier
  from `DH Audio Stereo Analyzer`; they read zero on a mono carrier.

Mesh Deform works on real point geometry. Realize instances before it if their
vertices must deform. For transforms on un-realized instances, use
`DH Audio Spectrum Instances` or Spectrum Bridge with Store on Instances.

## Materials and named bands

`DH Audio Material Reader` reads attributes already present on the shaded
geometry. Analyzer by itself is only a separate carrier—it does not broadcast
attributes globally.

- Visualizers preserve the standard numbered-spectrum attributes.
- `DH Audio Bands` is still the source for the named musical attributes such
  as Sub, Bass, Mid Range, Presence, Brilliance, and Air. Connect the geometry
  to its Attribute Bridge, or pass geometry carrying those attributes into a
  later visualizer.
- Use Instancer off for real or realized geometry. Turn it on for attributes
  stored on un-realized instances.

For texture animation, connect Texture Coordinate to
`DH Audio Shader UV Transform`, and drive Factor with Material Reader followed
by Shader Map. Offset occurs after pivot-centered scale and Z rotation.

## History

The reliable chain is:

`Analyzer → Spectrum Points → Spectrum History`

History outputs separate retained rows. Feed that result into Spectrum Fill
only when each row is processed separately; Fill expects one ordered spectrum
row and does not build surfaces between history rows. History and Temporal
Response contain Simulation Zones, so play sequentially or bake before
expecting a complete cached result.

## Band fields and storage domains

Band and Selection evaluate on the target domain. `Index` means point index in
Mesh Deform, face index in Mesh Extrude, and instance index for instance-domain
storage. Enable both Store on Points and Store on Instances only when both
copies are intentional; a topology-dependent Band field can differ by domain.

## Beta feedback checklist

Please report the Blender version, node chain, selected Sound/channel, frame,
whether playback was sequential or baked, and whether geometry was instanced
or realized. A small `.blend` reproducer and a screenshot of the group
interface are especially useful.
