# Material response: live amplitude and peak

This recipe drives a material from the same attributes used by the geometry
workflow. It is intentionally small: build the geometry anywhere, assign a
material, then read the carried attributes in the Shader Editor.

## Graph

```text
DH Audio Analyzer [Spectrum]
    → DH Audio Temporal Response [Spectrum]
    → your geometry / visualizer

DH Audio Material Reader [Amplitude or Peak]
    → DH Audio Shader Response
    → Emission Strength (or Color Ramp / Mix Shader)
```

The Temporal Response node belongs in Geometry Nodes. Material Reader and
Shader Response belong in the material's Shader Node Tree.

## Build it

1. Add [DH Audio Analyzer](../nodes/analyzer.md) and choose a Sound datablock.
2. Connect **Spectrum** to [DH Audio Temporal Response](../nodes/temporal_response.md).
3. Start with Attack `0.05 s`, Release `0.25 s`, Peak Hold enabled, Hold `0.20 s`,
   and Decay `0.50 s`. These values are responsive without flicker.
4. Connect Temporal Response **Spectrum** to a visualizer such as Spectrum
   Points, Bars, Curve, or Instances.
5. Assign a material to the resulting geometry. Open the Shader Editor and add
   [DH Audio Material Reader](../nodes/material_reader.md) plus [DH Audio
   Shader Response](../nodes/shader_response.md).
6. Leave Material Reader **Use Instancer** off for realized/ordinary geometry.
   Turn it on when the shader is reading attributes on Geometry Nodes
   instances.
7. Connect **Amplitude** or **Peak** from Material Reader to Shader Response
   **Value**, then connect **Gained** to Emission Strength.

## Choosing the signal

| Reader output | Attribute | Best use |
| --- | --- | --- |
| **Amplitude** | `dh_audio_amp` | Immediate, smooth brightness or color response |
| **Peak** | `dh_audio_peak` | A readable marker that holds and decays after transients |
| **Normalized** | `dh_audio_norm` | Stable 0–1 control for ramps and masks |
| Named band | `dh_audio_bass`, `dh_audio_mid`, etc. | Targeted musical regions |

For a crisp transient marker, use **Peak** with Shader Response Gain `1`, Floor
`0`, Ceiling `1`, Clamp on, and Response `0.7`. For a calmer overall glow, use
**Amplitude** with the default Ceiling `0.8`.

## Common variants

### Color response

Reader **Peak** → Shader Response **Normalized** → ColorRamp **Fac** → Base
Color or Emission Color. Put darker colors at the low end and a bright accent at
the high end.

### Instance materials

Keep attributes on the instance domain in the Geometry Nodes visualizer and set
Material Reader **Use Instancer** on. If the material stays flat, realize the
geometry and turn the option off, or preserve the instance path consistently.

### History fade

For Spectrum History, Reader **History Position** → Shader Map → ColorRamp or
Emission Strength. This is separate from Peak and is useful for waterfall age
fades.

## Verification and agent notes

- `dh_audio_amp` remains the live Temporal Response value; Peak is additive.
- Temporal Response needs sequential timeline evaluation or a simulation bake.
- Material Reader does not analyze audio. It only reads attributes already
  carried by geometry or instances.
- Keep Geometry Nodes and Shader Nodes in their respective editors.
- Verify the material's attribute domain before changing node behavior.

The public interfaces and defaults are verified in the node reference pages and
the Blender 5.2 regression suite.
