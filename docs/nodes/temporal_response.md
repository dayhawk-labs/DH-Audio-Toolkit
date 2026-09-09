# DH Audio Temporal Response

![DH Audio Temporal Response](../images/node-previews/dh-audio-temporal-response.png)

**Category:** Temporal<br>
**Blender domain:** GeometryNodeTree<br>
**Default node width:** 310 px

Apply frame-rate-independent attack/release smoothing and optional peak hold/decay to Analyzer spectrum geometry. dh_audio_amp remains the live response; dh_audio_peak is a separate held marker. Requires sequential timeline evaluation or a simulation bake for complete history.

## Agent notes

- This is stateful: evaluate sequential timeline frames or bake the simulation before expecting complete temporal behavior.
- Peak Hold is enabled by default. dh_audio_amp remains live smoothed amplitude; dh_audio_peak and Peak are the held marker.

## Key choices

- **Peak Hold:** on by default. It exposes Peak Hold Time and Peak Decay, while Peak output stays separate from live Amplitude.

## Interface panels

- **Source**: open by default; Spectrum carrier geometry with the standard dh_audio_amp attribute
- **Timing**: open by default; Frame-rate-independent exponential smoothing times
- **Peak Hold**: open by default; Optional peak marker with a hold period and exponential decay
- **Outputs**: open by default; Smoothed spectrum carrier and amplitude field

## Inputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Source | **Spectrum** | NodeSocketGeometry | none | Spectrum carrier from DH Audio Analyzer |
| Timing | **Attack** | NodeSocketFloat | 0.05 | Seconds to approach rising amplitude. 0 follows rises immediately |
| Timing | **Release** | NodeSocketFloat | 0.25 | Seconds to approach falling amplitude. 0 follows falls immediately |
| Peak Hold | **Peak Hold** | NodeSocketBool | on | Track a held peak alongside the smoothed live amplitude |
| Peak Hold | **Peak Hold Time** | NodeSocketFloat | 0.2 | Seconds a falling peak remains fixed before it decays |
| Peak Hold | **Peak Decay** | NodeSocketFloat | 0.5 | Seconds for a released peak to exponentially approach live amplitude |

## Outputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Outputs | **Spectrum** | NodeSocketGeometry | none | Current spectrum geometry with smoothed dh_audio_amp |
| Outputs | **Amplitude** | NodeSocketFloat | 0 | Smoothed dh_audio_amp field |
| Outputs | **Peak** | NodeSocketFloat | 0 | Held and decaying dh_audio_peak field; equals Amplitude when Peak Hold is off |

## Verification source

This page was generated from the public Blender interface exported by
tools/export_public_node_interfaces.py against a fresh toolkit build. Update
the screenshot and regenerate this page whenever the public interface changes.
