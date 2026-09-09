# Peak-Hold Waterfall Surface

Build a modular waterfall surface that smooths audio, retains a per-band peak
marker, and preserves the shared DH Audio attributes for shading.

This is the reference recipe for a stateful Geometry Nodes workflow. It uses
two Simulation Zones, so evaluate the timeline sequentially or bake it before
judging the result.

## What you will build

An inspectable starter file is available as the **Peak-Hold Waterfall Demo**.
Run `tools/create_peak_hold_waterfall_demo.py` from Blender 5.2+ to create it;
the file contains this graph, labeled stages, and a short in-file usage note.

~~~text
Sound
  -> DH Audio Analyzer
  -> DH Audio Temporal Response
  -> DH Audio Spectrum Points
  -> DH Audio Spectrum History [Surface]
  -> Group Output

Surface attributes -> Material Reader -> Shader Response -> Emission Strength
~~~

At frame 4 with the recipe defaults, the verified graph has 32 vertices and
21 quad faces: 8 bands across 4 retained rows.

## Add the geometry nodes

Create a Geometry Nodes modifier on any mesh and add these public assets:

1. [DH Audio Analyzer](../nodes/analyzer.md)
2. [DH Audio Temporal Response](../nodes/temporal_response.md)
3. [DH Audio Spectrum Points](../nodes/spectrum_points.md)
4. [DH Audio Spectrum History](../nodes/spectrum_history.md)

Make these exact geometry connections:

| From | To | Why |
| --- | --- | --- |
| Analyzer **Spectrum** | Temporal Response **Spectrum** | Supplies the standard per-band carrier. |
| Temporal Response **Spectrum** | Spectrum Points **Spectrum** | Uses the smoothed live **dh_audio_amp** carrier. |
| Spectrum Points **Spectrum Points** | Spectrum History **Spectrum Points** | Gives History positioned rows to retain. |
| Spectrum History **Surface** | Group Output **Geometry** | Emits the connected waterfall mesh. |

Do not use Spectrum Bars in this chain. Spectrum Bars is intentionally
standalone and owns its own Analyzer; this recipe demonstrates the reusable,
modular carrier workflow.

## Set the useful defaults

The toolkit's default values already create a safe starting point. Set only
the values below first:

| Node | Control | Value | Reason |
| --- | --- | --- | --- |
| Analyzer | Sound | Your Sound datablock | No Sound produces zero amplitude. |
| Analyzer | Bands | **8** | Keeps the first waterfall readable while validating the graph. |
| Temporal Response | Attack | **0.05 s** | Smooths rises without making them feel delayed. |
| Temporal Response | Release | **0.25 s** | Lets falling amplitudes settle more slowly. |
| Temporal Response | Peak Hold | On | Stores a separate held/decaying peak. |
| Temporal Response | Peak Hold Time | **0.20 s** | Makes peaks readable without a long freeze. |
| Temporal Response | Peak Decay | **0.50 s** | Returns held peaks smoothly toward live amplitude. |
| Spectrum Points | Height | **3.0** | Gives the waterfall useful vertical scale. |
| Spectrum Points | Center Spectrum | On | Centers the band row around the origin. |
| Spectrum History | Frames | **4** | Creates a small, easy-to-inspect surface. |
| Spectrum History | History Offset | **(0, -0.15, 0)** | Moves older rows backward along Y. |
| Spectrum History | Surface | On | Enables the connected quad output. |
| Spectrum History | Row Decimation | **1** | Uses every retained row. |

The **Peak Hold** and **Surface** panels are open by default so these controls
are visible without hunting through the interface. Peak Hold writes
**dh_audio_peak**; it does not replace live **dh_audio_amp**.

## Play, then inspect

1. Press Play from frame 1 through at least frame 4.
2. Confirm the surface grows from one row into a connected grid.
3. At frame 4, with 8 Bands and 4 Frames, expect **32 vertices** and
   **21 quad faces**.
4. Pause on a loud transient. The surface uses live smoothed amplitude while
   the separate **dh_audio_peak** attribute lingers for the configured hold and
   decay period.

If you jump directly to a later frame in a fresh file, the Simulation Zones
have no previous state. That is expected, not an audio-analysis failure.

## Add an optional peak-aware material

Assign a material after the History node using Blender's **Set Material** node.
Inside that material:

~~~text
DH Audio Material Reader [Peak]
  -> DH Audio Shader Response [Value]
  -> Emission Strength
~~~

Start with Material Reader **Use Instancer** off because the waterfall surface
is realized geometry. Use its **Amplitude** output for live motion or **Peak**
for the held marker. The recipe preserves **dh_audio_amp**, **dh_audio_peak**,
**dh_audio_history_index**, and **dh_audio_history_pos** on the Surface.

For an age fade, use:

~~~text
Material Reader [History Position]
  -> DH Audio Shader Map
  -> Color Ramp / Alpha / Emission Strength
~~~

Set Shader Map From Min to **0**, From Max to **1**, Clamp on, and Invert on to
make the newest row brightest.

## Scale it up

Once the four-row graph behaves as expected:

- Increase Analyzer **Bands** to **32** for a typical spectrum.
- Increase History **Frames** gradually, then use **Row Decimation** to bound
  surface density.
- Increase History Offset magnitude to spread rows farther apart.
- Bake or cache both Simulation Zones for dependable final renders.

## Verification

This recipe is exercised by the Blender 5.2 regression suite as **Peak Hold
Waterfall recipe connects a temporal spectrum to a surface**. The test creates
the exact public-node links above and verifies the frame-4 topology and
preserved attributes.
