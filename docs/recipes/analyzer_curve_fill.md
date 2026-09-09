# Analyzer to Curve or Fill

Use this modular path when you want to keep analysis separate from the visual
representation. One Analyzer can feed positioned points, a smooth curve, a
filled silhouette, or several downstream consumers at once.

## Build the graph

```text
DH Audio Analyzer [Spectrum]
  → DH Audio Spectrum Points [Spectrum]
  → DH Audio Spectrum Curve [Spectrum Points]
                         or [Spectrum Fill]
```

1. Create a Geometry Nodes modifier on a mesh.
2. Add **DH Audio Analyzer**, **DH Audio Spectrum Points**, and either
   **DH Audio Spectrum Curve** or **DH Audio Spectrum Fill**.
3. Connect Analyzer **Spectrum** to Spectrum Points **Spectrum**.
4. Connect Spectrum Points **Spectrum Points** to the selected visualizer.
5. Connect the Curve **Curve** or Fill **Mesh** output to Group Output.
6. Assign a Sound datablock to Analyzer **Sound** and press Play.

Reference pages: [Analyzer](../nodes/analyzer.md),
[Spectrum Points](../nodes/spectrum_points.md),
[Spectrum Curve](../nodes/spectrum_curve.md), and
[Spectrum Fill](../nodes/spectrum_fill.md).

## Starting values

| Node | Control | Value | Purpose |
| --- | --- | ---: | --- |
| Analyzer | Bands | `32` | General-purpose frequency density |
| Analyzer | Min / Max Frequency | `30 / 16000 Hz` | Practical audible range |
| Analyzer | FFT Size | `8192` | More frequency precision |
| Analyzer | Logarithmic | On | More useful musical spacing |
| Analyzer | Ceiling | `0.8` | Headroom before normalization clips |
| Spectrum Points | Height | `3.0` | Visible vertical response |
| Spectrum Points | Center Spectrum | On | Centers the row around X = 0 |
| Curve | Curve Style | Smooth | Readable Catmull–Rom line |
| Curve | Tube | Off | Start with a lightweight curve |
| Fill | Baseline | `0` | Silhouette returns to the origin plane |

Use **Curve** when you want a line or tube. Use **Fill** for a solid spectrum
silhouette. These are alternate consumers of the same positioned points; do not
connect both to the same Group Output unless you join their geometry.

## Curve options

- **Raw** preserves the original band-to-point structure.
- **Smooth** creates a Catmull–Rom curve while retaining the source ordering.
- **Smooth + Resample** produces even topology using **Resample Count** `128`.
- Enable **Tube** when a mesh is needed. Start with Tube Radius `0.02` and
  Tube Resolution `8`; set Audio Radius above zero for amplitude-reactive
  thickness.

## Attributes and composition

Spectrum Points preserves the Analyzer carrier attributes, including amplitude,
normalized amplitude, band index, band position, and frequency metadata. The
Curve and Fill outputs therefore remain usable with downstream material and
attribute workflows. Add [Material Reader](../nodes/material_reader.md) in a
material when the visual response should be controlled in the Shader Editor.

## Troubleshooting and agent notes

- No motion usually means Sound is unassigned or the timeline is not playing.
- A flat result usually means the Analyzer Ceiling is too high, Gain is too
  low, or the source is quiet.
- If the curve looks reversed or irregular, preserve the Analyzer ordering and
  do not sort or realize the carrier before Spectrum Points.
- Use [Spectrum Bars](spectrum_bars.md) when a self-contained first result is
  more useful than a modular graph.
