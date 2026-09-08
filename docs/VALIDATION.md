# Blender 5.2 validation

`tests/blender_52_regression.py` rebuilds the canonical generator from a
factory-empty file and exercises the toolkit with a deterministic stereo WAV.
It uses only Blender and Python's standard library.

Run it with Blender 5.2 or newer:

```powershell
& "C:\path\to\Blender 5.2\blender.exe" --background --factory-startup `
  --python tests/blender_52_regression.py -- `
  --report temp/blender_52_report.json
```

To create a clean asset-library build after the tests pass:

```powershell
& "C:\path\to\Blender 5.2\blender.exe" --background --factory-startup `
  --python tests/blender_52_regression.py -- `
  --report temp/blender_52_report.json `
  --release "releases/DH Audio Toolkit 3.11.0-beta.1.blend"
```

The release file is rebuilt from `src/dh_audio_toolkit.py`; test node groups,
objects, and the generated WAV are not saved into it. The generator writes the
stable `blender_assets.cats.txt` sidecar beside the `.blend`.

## Generated-assets branch

The `generated-assets` branch contains the latest validated `.blend` release
and catalog sidecar for convenient download and local testing. The GitHub
Actions **Generate Blender release assets** job rebuilds them from `main` on
pushes to `main` and can also be started manually with a source branch or tag.
Generated binaries are intentionally kept off `main`; source and tests remain
the canonical development surface there.

The suite checks:

- clean and repeated rebuild determinism;
- public assets, internal non-assets, stable catalogs, widths, panels, sockets,
  Boolean types, and menu/default values;
- deterministic node/frame placement and conservative non-overlap bounds for
  every generated public and internal node tree;
- Shader Map range, invert, clamp, and curve interface defaults;
- Shader UV Transform effective offset, pivot scale, and Z rotation;
- Analyzer time/channel behavior and spectrum movement across low, mid, and
  high-frequency sections;
- Stereo Analyzer one-sampler channel-field behavior, separate Left/Right
  carriers, paired L/R attributes, mirrored points, and Fill propagation;
- Temporal Response attack/release timing, zero-time behavior, topology-safe
  previous-band sampling, and metadata preservation;
- Spectrum History bounded growth, reset, one-frame history, normalized row
  age, attribute propagation, and changing source topology;
- Radial Spectrum unique cyclic spacing, exact open-arc endpoints, source
  height/center mapping, audio and spiral radius, cyclic curve closure, and
  one-band safety;
- named bands, Sample Range, and Band Query clamping;
- Spectrum Sample per-element field lookup, sampled band indices, paired
  left/right values, and safe carrier clamping;
- Spectrum Bridge point/instance storage, partial Selection, direct sampled
  fields, instancer-context lookup, and propagation through Realize Instances;
- Mesh Deform per-point stereo mapping, Selection, movement, and attribute
  storage;
- Mesh Extrude normal/individual and direction/region branches, Top/Side
  fields, full face schema propagation, and audio top-scale fields;
- Points, Bars, Instances, Curve, and Fill topology and attribute propagation;
- Audio Radius behavior;
- preservation of quiet intermediate fill bands;
- the documented Catmull-Rom smoothing undershoot without changing the public
  Curve Style behavior.
