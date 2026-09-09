# DH Audio Material Reader

![DH Audio Material Reader](../images/node-previews/dh-audio-material-reader.png)

**Category:** Shaders<br>
**Blender domain:** ShaderNodeTree<br>
**Default node width:** 300 px

Single shader reader for all DH Audio spectrum, stereo, temporal, spectrum-history, and named-band attributes. Use Source = 0 for geometry/realized data and Source = 1 for GN instance attributes.

## Agent notes

- Use Instancer off for realized geometry and on when the shader reads attributes carried by Geometry Nodes instances.
- This is the material-side entry point for spectrum, stereo, temporal peak, history, and named-band schemas.



## Interface panels

- **Source**: open by default; Choose whether attributes are read from geometry or Geometry Nodes instancing
- **Spectrum Attributes**: open by default; Common per-band values written by DH Audio Analyzer
- **Frequency Metadata**: collapsed by default; Detailed spectrum frequency metadata
- **Stereo Attributes**: open by default; Left/right values and channel metadata written by DH Audio Stereo Analyzer
- **Spectrum History**: collapsed by default; Row age values written by DH Audio Spectrum History
- **Temporal Response**: collapsed by default; Peak value written by DH Audio Temporal Response when Peak Hold is enabled
- **Named Bands**: open by default; Named values written by DH Audio Bands

## Inputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Source | **Use Instancer** | NodeSocketBool | off | Off = Geometry/realized attributes; On = Geometry Nodes instancer attributes |

## Outputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Spectrum Attributes | **Amplitude** | NodeSocketFloat | 0 | Reads 'dh_audio_amp' |
| Spectrum Attributes | **Normalized** | NodeSocketFloat | 0 | Reads 'dh_audio_norm' |
| Spectrum Attributes | **Raw Amplitude** | NodeSocketFloat | 0 | Reads 'dh_audio_raw' |
| Spectrum Attributes | **Band Index** | NodeSocketFloat | 0 | Reads 'dh_audio_band_index' |
| Spectrum Attributes | **Band Position** | NodeSocketFloat | 0 | Reads 'dh_audio_band_pos' |
| Frequency Metadata | **Low Frequency** | NodeSocketFloat | 0 | Reads 'dh_audio_low_hz' |
| Frequency Metadata | **Center Frequency** | NodeSocketFloat | 0 | Reads 'dh_audio_center_hz' |
| Frequency Metadata | **High Frequency** | NodeSocketFloat | 0 | Reads 'dh_audio_high_hz' |
| Frequency Metadata | **Bandwidth** | NodeSocketFloat | 0 | Reads 'dh_audio_bandwidth_hz' |
| Stereo Attributes | **Left Amplitude** | NodeSocketFloat | 0 | Reads 'dh_audio_left_amp' |
| Stereo Attributes | **Right Amplitude** | NodeSocketFloat | 0 | Reads 'dh_audio_right_amp' |
| Stereo Attributes | **Left Normalized** | NodeSocketFloat | 0 | Reads 'dh_audio_left_norm' |
| Stereo Attributes | **Right Normalized** | NodeSocketFloat | 0 | Reads 'dh_audio_right_norm' |
| Stereo Attributes | **Channel** | NodeSocketFloat | 0 | Reads 'dh_audio_channel' |
| Stereo Attributes | **Channel Position** | NodeSocketFloat | 0 | Reads 'dh_audio_channel_pos' |
| Stereo Attributes | **Left Raw Amplitude** | NodeSocketFloat | 0 | Reads 'dh_audio_left_raw' |
| Stereo Attributes | **Right Raw Amplitude** | NodeSocketFloat | 0 | Reads 'dh_audio_right_raw' |
| Spectrum History | **History Index** | NodeSocketFloat | 0 | Reads 'dh_audio_history_index' |
| Spectrum History | **History Position** | NodeSocketFloat | 0 | Reads 'dh_audio_history_pos' |
| Temporal Response | **Peak** | NodeSocketFloat | 0 | Reads 'dh_audio_peak' |
| Named Bands | **Total Volume** | NodeSocketFloat | 0 | Reads 'dh_audio_total' |
| Named Bands | **Sub** | NodeSocketFloat | 0 | Reads 'dh_audio_sub' |
| Named Bands | **Bass** | NodeSocketFloat | 0 | Reads 'dh_audio_bass' |
| Named Bands | **Low Mid** | NodeSocketFloat | 0 | Reads 'dh_audio_low_mid' |
| Named Bands | **Mid Range** | NodeSocketFloat | 0 | Reads 'dh_audio_mid' |
| Named Bands | **High Mids** | NodeSocketFloat | 0 | Reads 'dh_audio_high_mids' |
| Named Bands | **Presence** | NodeSocketFloat | 0 | Reads 'dh_audio_presence' |
| Named Bands | **Brilliance** | NodeSocketFloat | 0 | Reads 'dh_audio_brilliance' |
| Named Bands | **Air** | NodeSocketFloat | 0 | Reads 'dh_audio_air' |

## Verification source

This page was generated from the public Blender interface exported by
tools/export_public_node_interfaces.py against a fresh toolkit build. Update
the screenshot and regenerate this page whenever the public interface changes.
