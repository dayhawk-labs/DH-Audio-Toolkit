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
  --release "releases/DH Audio Toolkit 3.4.0.blend"
```

The release file is rebuilt from `src/dh_audio_toolkit.py`; test node groups,
objects, and the generated WAV are not saved into it. The generator writes the
stable `blender_assets.cats.txt` sidecar beside the `.blend`.

The suite checks:

- clean and repeated rebuild determinism;
- public assets, internal non-assets, stable catalogs, widths, panels, sockets,
  Boolean types, and menu/default values;
- Analyzer time/channel behavior and spectrum movement across low, mid, and
  high-frequency sections;
- Temporal Response attack/release timing, zero-time behavior, topology-safe
  previous-band sampling, and metadata preservation;
- named bands, Sample Range, and Band Query clamping;
- Points, Bars, Instances, Curve, and Fill topology and attribute propagation;
- Audio Radius behavior;
- preservation of quiet intermediate fill bands;
- the documented Catmull-Rom smoothing undershoot without changing the public
  Curve Style behavior.
