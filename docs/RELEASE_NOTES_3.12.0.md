# DH Audio Toolkit 3.12.0

## Added

- **DH Audio Temporal Response** now includes optional per-band **Peak Hold +
  Decay**. It writes `dh_audio_peak` and exposes a matching **Peak** output,
  while retaining `dh_audio_amp` as the attack/release-smoothed live value.
- Peak Hold defaults to enabled, with a practical `0.20` second hold and a
  `0.50` second exponential decay toward live amplitude. Disable **Peak Hold**
  to make the Peak output equal the live amplitude.
- **DH Audio Material Reader** now provides a Peak output under its collapsed
  **Temporal Response** panel for material-side peak markers.

## Compatibility

Requires Blender 5.2 or newer. Existing node graphs keep their current
attack/release behavior because `dh_audio_amp` is unchanged. `dh_audio_peak`
is an additive attribute produced by Temporal Response.

Play sequentially or bake the Temporal Response Simulation Zone before relying
on held peak history. See the [quickstart](BETA_QUICKSTART.md) and
[recipe guide](RECIPES.md) for usage examples.
