# DH Audio Toolkit

**Audio-reactive Geometry Nodes and Shader Nodes for Blender 5.2+**

**Current release:** `3.11`
**Status:** Blender 5.2 release

DH Audio Toolkit is a modular toolkit built around Blender 5.2's **Sample Sound
Frequencies** node. It turns audio into reusable spectrum data, geometry,
instances, materials, and shader controls.

> **Compatibility note:** public node-group names and `dh_audio_*` attributes
> are compatibility-sensitive. Start with the [quickstart](docs/BETA_QUICKSTART.md)
> and review the [release notes](docs/RELEASE_NOTES_3.11.md).

## Start here

1. Download the [DH Audio Toolkit 3.11 Blender file](releases/DH%20Audio%20Toolkit%203.11.blend)
   and [catalog sidecar](releases/blender_assets.cats.txt).
2. Put both files in the same Blender Asset Library folder.
3. Load the node groups from the **DH Audio** asset catalog.
4. Pick a workflow from the [recipe guide](docs/RECIPES.md).

You do not need to run the Python generator to use the released asset. The
generator and tests remain available for development and custom rebuilds.

For a portable asset release, share the `.blend` file and its
`blender_assets.cats.txt` file in the same asset-library folder.

## The toolkit in one diagram

```text
ANALYZE  →  MAP  →  CONSUME
   │          │        ├─ bars
   │          │        ├─ curves
   │          │        ├─ fills
   │          │        └─ instances
   ├─ QUERY      retrieve one scalar band
   ├─ TRANSPORT  named attributes for geometry and materials
   └─ SHADE      read and reshape attributes in materials
```

## Public node groups

### Analysis and sampling

| Group | Purpose |
| --- | --- |
| **DH Audio Analyzer** | Core N-band FFT analyzer with standardized spectrum attributes. |
| **DH Audio Stereo Analyzer** | One field-driven sample node for combined, left, and right spectra. |
| **DH Audio Frequency Map** | Linear or logarithmic frequency-bound mapping. |
| **DH Audio Band Query** | Samples one numbered analyzer band. |
| **DH Audio Spectrum Sample** | Samples a different band per point, face, curve, or instance. |
| **DH Audio Sample Range** | Samples one custom low-to-high frequency range. |
| **DH Audio Bands** | Named musical ranges from Total through Air. |
| **DH Audio Frequency Selection** | Selects bands by actual center-frequency bounds. |

### Mapping and geometry

| Group | Purpose |
| --- | --- |
| **DH Audio Spectrum Points** | Converts a flat spectrum carrier into visible points. |
| **DH Audio Stereo Points** | Mirrors left and right carriers around a shared baseline. |
| **DH Audio Spectrum Bridge** | Applies spectrum data to arbitrary mesh, curve, or instance geometry. |
| **DH Audio Spectrum Bars** | Standalone visualizer with built-in analyzer and multiple profiles. |
| **DH Audio Spectrum Curve** | Creates raw, smoothed, resampled, and tube curves. |
| **DH Audio Spectrum Fill** | Builds a filled spectrum silhouette. |
| **DH Audio Spectrum Instances** | Instances arbitrary geometry once per spectrum band. |
| **DH Audio Radial Spectrum** | Maps a spectrum into circles, arcs, or spirals. |
| **DH Audio Mesh Deform** | Displaces arbitrary mesh or curve points. |
| **DH Audio Mesh Extrude** | Extrudes mesh faces from reusable spectrum data. |
| **DH Audio Spectrum History** | Accumulates spectrum points into a bounded waterfall stack. |

### Response and materials

| Group | Purpose |
| --- | --- |
| **DH Audio Response** | Gain, normalization, clamp, and response shaping for geometry. |
| **DH Audio Temporal Response** | Frame-rate-independent attack/release smoothing. |
| **DH Audio Material Reader** | Reads spectrum, stereo, history, and named-band attributes. |
| **DH Audio Shader Response** | Material-side response shaping. |
| **DH Audio Shader Map** | Range mapping, clamping, inversion, and power curves. |
| **DH Audio Shader UV Transform** | Audio-driven offset, pivot scale, and Z rotation. |

## Compatibility model

The toolkit shares a stable attribute schema across analyzers, geometry, and
materials. This lets you swap consumers without rebuilding the analysis stage.

### Spectrum attributes

`dh_audio_amp` · `dh_audio_norm` · `dh_audio_raw` · `dh_audio_band_index` ·
`dh_audio_band_pos` · `dh_audio_low_hz` · `dh_audio_center_hz` ·
`dh_audio_high_hz` · `dh_audio_bandwidth_hz`

### Stereo attributes

`dh_audio_channel` (`0 = Left`, `1 = Right`) · `dh_audio_channel_pos` (`-1 =
Left`, `+1 = Right`) · `dh_audio_left_amp` · `dh_audio_right_amp` ·
`dh_audio_left_norm` · `dh_audio_right_norm` · `dh_audio_left_raw` ·
`dh_audio_right_raw`

### History attributes

`dh_audio_history_index` · `dh_audio_history_pos`

Named-band outputs include `dh_audio_total`, `dh_audio_sub`, `dh_audio_bass`,
`dh_audio_low_mid`, `dh_audio_mid`, `dh_audio_high_mids`,
`dh_audio_presence`, `dh_audio_brilliance`, and `dh_audio_air`.

## Asset catalogs

The generator writes stable catalog UUIDs to `blender_assets.cats.txt` and
organizes assets under:

```text
Geometry Nodes / DH Audio / Analysis
Geometry Nodes / DH Audio / Mapping
Geometry Nodes / DH Audio / Query
Geometry Nodes / DH Audio / Visualizers
Geometry Nodes / DH Audio / Utilities
DH Audio / Shaders
```

Keep the catalog file beside the `.blend` when sharing or moving the asset
library. The UUIDs are intended to remain stable across releases.

## Design notes

- Larger FFT sizes improve frequency precision but respond more slowly.
- The stock ceiling is `0.8`; this avoids clipping ordinary mastered music.
- Smooth curves use Catmull–Rom interpolation. Smooth + Resample produces an
  evenly sampled curve for downstream modeling.
- Temporal Response and Spectrum History use Simulation Zones. Play the timeline
  sequentially or bake the simulation when complete history is required.
- Spectrum Points and Spectrum Bars emit compatible point data for Curve and
  Fill workflows.
- Public groups intentionally hide repetitive internal attribute plumbing.

## Further documentation

- [Recipes and examples](docs/RECIPES.md)
- [Quickstart](docs/BETA_QUICKSTART.md)
- [Release notes](docs/RELEASE_NOTES_3.11.md)
- [Source](src/dh_audio_toolkit.py)
- [Regression tests](tests/blender_52_regression.py)

## Roadmap ideas

Potential extensions include peak hold and decay, connected waterfall surfaces,
radial bars, stereo named bands, rolling normalization, onset/beat triggers,
frequency-based rotation, and standard shader color helpers.
