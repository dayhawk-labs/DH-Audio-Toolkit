# Spectrum Bars: First Result

Use **DH Audio Spectrum Bars** for the quickest audio-reactive result. It
contains its own Analyzer, so this recipe needs one public node and one Group
Output.

## Build the graph

```text
DH Audio Spectrum Bars → Group Output
```

1. Create a Geometry Nodes modifier on a mesh.
2. Add [DH Audio Spectrum Bars](../nodes/spectrum_bars.md).
3. Connect **Geometry** to **Group Output → Geometry**.
4. Assign a Sound datablock to **Sound** and press Play.

The default profile is **Box**, with 32 logarithmically distributed bands. The
node also outputs top-edge **Spectrum Points** for a second visual treatment.

## Sensible first adjustments

| Control | Starting value | Why |
| --- | ---: | --- |
| Bands | `32` | Good general-purpose density |
| Min Frequency | `30 Hz` | Includes bass without excessive subsonic noise |
| Max Frequency | `16 kHz` | Covers the audible range for most material |
| FFT Size | `8192` | Clear frequency separation; lower it for faster response |
| Ceiling | `0.8` | Leaves useful headroom before normalization clips |
| Max Height | `3.0` | Visible scale for a unit-sized starting object |
| Gap | `0.05` | Separates neighboring bars without large holes |
| Bar Profile | `Box` | Fastest and cheapest profile to preview |

For a more responsive display, try FFT Size `4096`. For a softer visual,
reduce **Response** below `1`; for stronger quiet-band motion, raise Gain or
lower Ceiling carefully.

## Choose a bar shape

**Bar Profile** supports Box, Round, Cone, Icosphere, Custom Profile, and
Custom Geometry. Custom profiles should be centered near the origin and roughly
1 × 1 in size. Custom geometry should be approximately 1 unit tall and
centered around Z = 0 for predictable height controls.

Assign **Material** on the node to shade every bar. For a separate
material-driven response, pass the geometry to Set Material and use
[DH Audio Material Reader](../nodes/material_reader.md) in the material.

## Use the top-edge points

The **Spectrum Points** output is positioned at each bar's top edge. Connect it
to [DH Audio Spectrum Curve](../nodes/spectrum_curve.md) or
[DH Audio Spectrum Fill](../nodes/spectrum_fill.md) to add a line or filled
silhouette. It carries per-band amplitude, normalized amplitude, band index,
and band position fields.

## Troubleshooting and agent notes

- No motion usually means no Sound datablock is assigned, or the timeline is
  not playing.
- If the result clips, increase Ceiling or reduce Gain.
- If it is too dense, reduce Bands or increase Gap.
- Preserve **Spectrum Points** when testing downstream consumers.
- The node owns its Analyzer; do not connect a separate Analyzer to it.
