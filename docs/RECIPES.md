# DH Audio Toolkit recipes

Practical node-graph patterns for Blender 5.2+. Each recipe assumes the DH
Audio node groups have been generated and loaded into the current file.

## Featured, verified recipe

[**Peak-Hold Waterfall Surface**](recipes/peak_hold_waterfall.md) is the
complete reference build: Analyzer → Temporal Response → Spectrum Points →
Spectrum History Surface, with verified links, sensible values, a peak-aware
material option, and topology checks in the Blender regression suite.

[**Spectrum Bars: First Result**](recipes/spectrum_bars_first_result.md) is the
shortest path from a Sound datablock to a visible audio-reactive result.

[**Analyzer to Curve or Fill**](recipes/analyzer_curve_fill.md) is the canonical
modular carrier workflow for reusable spectrum geometry.

## Quick chooser

| Goal | Start with |
| --- | --- |
| Fastest first result | [**Spectrum Bars**](recipes/spectrum_bars_first_result.md) |
| A reusable audio graph | [**Analyzer → Curve or Fill**](recipes/analyzer_curve_fill.md) |
| A custom visualizer | **Analyzer → Spectrum Instances** |
| A single reactive value | **Band Query** or **Sample Range** |
| Audio on existing geometry | **Spectrum Bridge** |
| Audio-driven materials | **Material Reader** |

## 1. Standalone bars

```text
DH Audio Spectrum Bars → Group Output
```

Choose a sound and press Play. Useful controls include Bands, Min/Max
Frequency, FFT Size, Window Function, Ceiling, Bar Profile, Width, Depth, Gap,
and Height.

Bar Profile options are **Box**, **Round**, **Cone**, **Icosphere**, **Custom
Profile**, and **Custom Geometry**. A custom profile should be a 2D curve
cross-section centered near the origin. Custom geometry should be normalized
around Z = 0 and roughly one unit tall for predictable size controls.

## 2. Analyzer to visible spectrum points

```text
DH Audio Analyzer [Spectrum]
    → DH Audio Spectrum Points [Spectrum]
```

Spectrum Points controls are Height, Baseline, Center Spectrum, X Scale, and X
Offset. This is the canonical “audio graph as geometry” representation and
preserves amplitude, band, and frequency attributes for downstream consumers.

## 3. Mirrored left/right spectrum

```text
DH Audio Stereo Analyzer [Left Spectrum / Right Spectrum]
    → DH Audio Stereo Points [Left Spectrum / Right Spectrum]
```

Left rises above zero and Right mirrors below it. Keep the rows separate for
Curve, Fill, and History. For filled stereo, send each row through its own
Spectrum Fill and join the resulting meshes.

## 4. Attack/release smoothing

```text
DH Audio Analyzer [Spectrum]
    → DH Audio Temporal Response [Spectrum]
    → Spectrum Points / Instances / another consumer
```

Defaults are Attack `0.05` seconds and Release `0.25` seconds. Set either to
zero for an immediate response in that direction. This group uses a Simulation
Zone, so play the timeline sequentially or bake it for complete history.

The **Peak Hold** panel is open and enabled by default. It holds each band's
smoothed peak for `0.20` seconds, then decays it exponentially toward the live
amplitude over `0.50` seconds. Use the **Peak** output or `dh_audio_peak` for a
separate marker; **Amplitude** and `dh_audio_amp` remain the live value. Turn
off **Peak Hold** when a consumer should receive the live value on both outputs.

## 5. Spectrum waterfall history

```text
DH Audio Analyzer → DH Audio Spectrum Points → DH Audio Spectrum History
```

Spectrum Bars can also feed Spectrum History directly. Defaults are Frames
`32` and History Offset `(0, -0.15, 0)`. **History** contains separate mesh
rows. Enable the open **Surface** panel to emit a connected quad waterfall
from the matching **Surface** output. Start with Row Decimation `1`; increase
it only when a long history needs fewer rows. Surface is disabled by default,
so existing row workflows are unchanged. Reset discards previous rows in one
evaluated frame.

## 6. Radial or spiral spectrum

```text
DH Audio Analyzer → DH Audio Radial Spectrum
```

For radial layout plus vertical audio height:

```text
DH Audio Analyzer → DH Audio Spectrum Points → DH Audio Radial Spectrum
```

Useful defaults are Radius `3.0`, Audio Radius `1.5`, Sweep Angle `360°`, and
Cyclic On. Negative Sweep Angle reverses direction. Cyclic mode creates a true
closing segment; Open mode preserves exact arc endpoints.

## 7. Smooth spectrum curve

```text
DH Audio Analyzer → DH Audio Spectrum Points → DH Audio Spectrum Curve
```

Spectrum Bars can provide the Spectrum Points input as well. Curve Style
defaults to Smooth. For a denser editable curve, use **Smooth + Resample** with
Resample Count `128`. The group outputs Curve and Tube; Tube also exposes Tube
Radius, Audio Radius, Tube Resolution, and Material.

## 8. Filled spectrum silhouette

```text
DH Audio Analyzer → DH Audio Spectrum Points → DH Audio Spectrum Fill
```

Spectrum Bars can feed Fill directly. The fill follows every input point and
creates a bottom edge at Baseline. It works well for emissive silhouettes,
masks, ribbons, stylized terrain, and downstream deformation.

## 9. Instance anything

```text
DH Audio Analyzer → DH Audio Spectrum Instances
```

Connect any geometry to Instance. A useful starting point is Base Scale
`(1, 1, 1)`, Amplitude Scale `(0, 0, 3)`, and Amplitude Offset `(0, 0, 2)`.
This works for lights represented by meshes, logos, crystals, particles,
abstract sculptures, text converted to geometry, and collections.

## 10. Select a frequency region

```text
DH Audio Frequency Selection
```

For example, set Low Frequency to `60 Hz` and High Frequency to `250 Hz`. Send
Selection to Spectrum Instances, Set Position, Delete Geometry, or Set
Material. The selection uses `dh_audio_center_hz`, so it remains correct when
the analyzer band count changes.

## 11. Query one numbered band

```text
DH Audio Analyzer [Spectrum] → DH Audio Band Query [Spectrum]
```

Set Band to a numbered band such as `6`. Outputs include Band Index, Amplitude,
Normalized, Raw Amplitude, and Band Position. Detailed frequency metadata is
collapsed by default.

## 12. Sample a different band per element

```text
DH Audio Analyzer [Spectrum] → DH Audio Spectrum Sample [Spectrum]
```

Connect an integer field to Band, such as Index, ID, a face group, or Index
modulo Analyzer Bands. Use Amplitude or Normalized to drive Set Position,
Extrude Mesh Offset Scale, Scale Instances, rotation, or Store Named Attribute.
Stereo Analyzer carriers also expose paired Left and Right fields.

## 13. Map spectrum bands onto arbitrary geometry

```text
DH Audio Analyzer [Spectrum] → DH Audio Spectrum Bridge [Spectrum]
Any mesh, curve, or instances [Geometry] → DH Audio Spectrum Bridge [Geometry]
```

Connect an integer field such as Index modulo Analyzer Bands to Band. The
Geometry output carries standard spectrum, frequency, and stereo attributes.

Use **Store on Points** for real or realized geometry and **Store on Instances**
for un-realized instances. If Band uses Index on target instances, enable only
Store on Instances unless prototype-point mapping is intentional.

## 14. Sample one custom frequency range

Use **DH Audio Sample Range** when you want one reaction value rather than a
complete spectrum. Examples include kick/sub motion (`40–120 Hz`), vocal
presence, or cymbal shimmer.

## 15. Named musical bands

Use **DH Audio Bands** for Total Volume, Sub, Bass, Low Mid, Mid Range, High
Mids, Presence, Brilliance, and Air. These ranges are independent of Analyzer
Bands count and use one field-driven Sample Sound Frequencies node internally.

## 16. Put named bands on your own geometry

```text
Your Geometry → DH Audio Bands → Attribute Bridge → Geometry
```

Leave Store on Points and Store on Instances enabled when both domains may be
consumed. The output carries `dh_audio_total`, `dh_audio_sub`,
`dh_audio_bass`, `dh_audio_low_mid`, `dh_audio_mid`, `dh_audio_high_mids`,
`dh_audio_presence`, `dh_audio_brilliance`, and `dh_audio_air`.

## 17. Audio-driven materials

Inside a material, add **DH Audio Material Reader**. Set Use Instancer On for
geometry still living as Geometry Nodes instances, and Off for ordinary or
realized geometry.

Typical graph:

```text
DH Audio Material Reader [Amplitude]
    → DH Audio Shader Response
    → Emission Strength
```

For history fades:

```text
DH Audio Material Reader [History Position]
    → DH Audio Shader Map
    → Color Ramp / Alpha / Emission Strength
```

For a newest-to-oldest fade, try From Min `0`, From Max `1`, Invert On, Clamp
On, and Curve between `1` and `3`.

## Troubleshooting notes

- If temporal or history output looks empty, play the timeline sequentially or
  bake the Simulation Zone.
- If materials do not react on instances, check Use Instancer on Material
  Reader.
- If a selection changes when band count changes, select by frequency with
  Frequency Selection rather than by band number.
- If size controls behave unexpectedly for custom geometry, normalize it around
  Z = 0 and approximately one unit tall.
