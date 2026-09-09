# Public Node Reference

This reference is generated from public Blender interfaces. Each page
pairs a captured exterior view with verified sockets, defaults,
descriptions, and agent-facing workflow notes.

| Node | Category | Summary |
| --- | --- | --- |
| [DH Audio Analyzer](analyzer.md) | Analysis | General-purpose Blender 5.2 multi-band audio analyzer with FFT/window controls, linear/log spacing, response shaping, compact internal architecture, and named attributes. |
| [DH Audio Band Query](band_query.md) | Query | Retrieve one spectrum band's amplitude and frequency metadata from DH Audio Analyzer. |
| [DH Audio Bands](bands.md) | Analysis | Named musical frequency bands independent of spectrum band count. Uses one field-driven audio sampler, a compact indexed band mapper, direct scalar outputs, Band Data carrier geometry, and an integrated attribute bridge. |
| [DH Audio Frequency Map](frequency_map.md) | Utilities | Advanced utility: map a band index to linear or logarithmic frequency bounds. |
| [DH Audio Frequency Selection](frequency_selection.md) | Utilities | Select DH Audio spectrum elements by actual center-frequency range, with convenient amplitude and normalized pass-through fields. |
| [DH Audio Material Reader](material_reader.md) | Shaders | Single shader reader for all DH Audio spectrum, stereo, temporal, spectrum-history, and named-band attributes. Use Source = 0 for geometry/realized data and Source = 1 for GN instance attributes. |
| [DH Audio Mesh Deform](mesh_deform.md) | Transport | Displace arbitrary mesh or curve points from a reusable mono/stereo spectrum, with per-point band mapping and material-ready attributes. |
| [DH Audio Mesh Extrude](mesh_extrude.md) | Transport | Extrude mesh faces from a reusable mono/stereo spectrum with per-face band mapping, top scaling, and standard face-domain material attributes. |
| [DH Audio Radial Spectrum](radial_spectrum.md) | Mapping | Map DH Audio spectrum carrier geometry into circular, open-arc, or spiral layouts. Preserves spectrum attributes, supports radial audio displacement and source height, and outputs a correctly closed cyclic curve. |
| [DH Audio Response](response.md) | Utilities | Reusable Geometry Nodes response shaper for audio amplitude or any scalar field. |
| [DH Audio Sample Range](sample_range.md) | Analysis | Sample any custom frequency range directly, independent of spectrum band indexing. |
| [DH Audio Shader Map](shader_map.md) | Shaders | Remap, invert, clamp, and shape any DH Audio material value. Useful for amplitude thresholds, named-band controls, and Spectrum History fades. |
| [DH Audio Shader Response](shader_response.md) | Shaders | Shader-side audio response shaper matching DH Audio Response. |
| [DH Audio Shader UV Transform](shader_uv_transform.md) | Shaders | Transform shader UV or texture coordinates with an audio/history factor: pivot-centered scale and rotation plus animated offset. |
| [DH Audio Spectrum Bars](spectrum_bars.md) | Visualizers | Standalone spectrum bar visualizer built on DH Audio Analyzer. Includes Box/Round/Cone/Icosphere presets, custom curve cross-sections, custom geometry, top-edge spectrum points, and standardized audio attributes. |
| [DH Audio Spectrum Bridge](spectrum_bridge.md) | Transport | Map reusable spectrum bands across arbitrary geometry or instances, store the standard material attributes, and expose the sampled fields directly. |
| [DH Audio Spectrum Curve](spectrum_curve.md) | Visualizers | Convert positioned spectrum points into a raw, Catmull-Rom smooth, or resampled curve, with optional audio-reactive tube radius. |
| [DH Audio Spectrum Fill](spectrum_fill.md) | Visualizers | Build a filled quad strip below positioned spectrum points. Accepts DH Audio Spectrum Points, Stereo Points channel outputs, or Spectrum Bars' Spectrum Points while preserving stereo attributes. |
| [DH Audio Spectrum History](spectrum_history.md) | Temporal | Accumulate positioned spectrum points into a bounded waterfall history. Optionally generates a decimated connected quad surface, preserves spectrum and temporal peak attributes, supports changing band counts and reset, and exposes dh_audio_history_index / dh_audio_history_pos. Requires sequential timeline evaluation or a simulation bake for complete history. |
| [DH Audio Spectrum Instances](spectrum_instances.md) | Visualizers | Generic spectrum consumer: instance any geometry on analyzer bands and drive scale/position with amplitude. |
| [DH Audio Spectrum Points](spectrum_points.md) | Mapping | Map DH Audio Analyzer carrier geometry into visible audio-height points. The output is compatible with Spectrum Bars' Spectrum Points, Spectrum Curve, and Spectrum Fill. |
| [DH Audio Spectrum Sample](spectrum_sample.md) | Query | Sample reusable spectrum and paired stereo attributes with a per-element band field for arbitrary deformation, array, instance, and attribute workflows. |
| [DH Audio Stereo Analyzer](stereo_analyzer.md) | Analysis | Analyze left and right channels with one field-driven Sample Sound Frequencies node. Outputs combined and separate carriers with standard, channel, and paired L/R attributes. |
| [DH Audio Stereo Points](stereo_points.md) | Mapping | Map Stereo Analyzer Left and Right carriers into mirrored point rows around a shared baseline. Separate outputs remain compatible with Spectrum Curve, Fill, and History. |
| [DH Audio Temporal Response](temporal_response.md) | Temporal | Apply frame-rate-independent attack/release smoothing and optional peak hold/decay to Analyzer spectrum geometry. dh_audio_amp remains the live response; dh_audio_peak is a separate held marker. Requires sequential timeline evaluation or a simulation bake for complete history. |

## Regeneration

See Public Node Previews in the parent documentation. Rebuild the source
blend, export temp/public_node_interfaces.json, then run this script.
