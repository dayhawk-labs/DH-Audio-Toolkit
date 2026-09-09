# DH Audio Spectrum Bars

![DH Audio Spectrum Bars](../images/node-previews/dh-audio-spectrum-bars.png)

**Category:** Visualizers<br>
**Blender domain:** GeometryNodeTree<br>
**Default node width:** 350 px

Standalone spectrum bar visualizer built on DH Audio Analyzer. Includes Box/Round/Cone/Icosphere presets, custom curve cross-sections, custom geometry, top-edge spectrum points, and standardized audio attributes.

## Agent notes

- This includes its own analyzer and is the fastest way to get a bar visualizer.
- Use its Spectrum Points output for Curve or Fill. Choose Bar Profile before supplying custom geometry.

## Key choices

- **Bar Profile:** Box, Round, Cone, Icosphere, Custom Profile, or Custom Geometry.
- **Custom Profile / Custom Geometry:** supply the corresponding geometry input after choosing the matching profile.

## Interface panels

- **Audio**: open by default; Sound, time, channel and FFT controls
- **Spectrum**: open by default; Frequency distribution
- **Response**: open by default; Audio normalization and response
- **Bars**: open by default; Bar geometry and layout
- **Profile**: open by default; Built-in or custom bar shape
- **Outputs**: open by default; Geometry and the per-band fields used most often
- **Advanced Outputs**: collapsed by default; Raw analyzer carrier and detailed frequency metadata

## Inputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Audio | **Sound** | NodeSocketSound | none | Required: Sound data-block to analyze. An unassigned Sound produces zero amplitude, which is indistinguishable from silent audio inside Geometry Nodes |
| Audio | **Use Scene Time** | NodeSocketBool | on | Use Scene Time. Disable to use the custom Time input |
| Audio | **Time** | NodeSocketFloat | 0 | Custom time in seconds when Use Scene Time is disabled |
| Audio | **Time Offset** | NodeSocketFloat | 0 | Seconds added to the selected time source |
| Audio | **Window Function** | NodeSocketMenu | Hann | FFT window function |
| Audio | **FFT Size** | NodeSocketMenu | 8192 | FFT analysis size. Higher values improve frequency resolution but reduce time resolution |
| Audio | **All Channels** | NodeSocketBool | on | Mix all channels before sampling |
| Audio | **Channel** | NodeSocketInt | 0 | Channel used when All Channels is disabled |
| Spectrum | **Bands** | NodeSocketInt | 32 | none |
| Spectrum | **Min Frequency** | NodeSocketFloat | 30 | none |
| Spectrum | **Max Frequency** | NodeSocketFloat | 1.6e+04 | none |
| Spectrum | **Logarithmic** | NodeSocketBool | on | none |
| Response | **Gain** | NodeSocketFloat | 1 | Multiplier applied before normalization |
| Response | **Floor** | NodeSocketFloat | 0 | Post-gain amplitude mapped to zero |
| Response | **Ceiling** | NodeSocketFloat | 0.8 | Post-gain amplitude mapped to one |
| Response | **Clamp to 1** | NodeSocketBool | on | Clamp normalized amplitude to a maximum of one |
| Response | **Response** | NodeSocketFloat | 0.7 | Power curve. Below 1 emphasizes quieter values; above 1 emphasizes peaks |
| Bars | **Bar Width** | NodeSocketFloat | 0.2 | none |
| Bars | **Bar Depth** | NodeSocketFloat | 0.2 | none |
| Bars | **Gap** | NodeSocketFloat | 0.05 | none |
| Bars | **Min Height** | NodeSocketFloat | 0.02 | none |
| Bars | **Max Height** | NodeSocketFloat | 3 | none |
| Bars | **Baseline** | NodeSocketFloat | 0 | none |
| Bars | **Center Spectrum** | NodeSocketBool | on | none |
| Profile | **Bar Profile** | NodeSocketMenu | Box | Choose a built-in shape or provide a custom profile/geometry |
| Profile | **Profile Resolution** | NodeSocketInt | 12 | Round/Cone radial resolution |
| Profile | **Custom Profile** | NodeSocketGeometry | none | 2D curve cross-section used by Custom Profile. Center it around the origin and size it roughly 1 × 1. |
| Profile | **Custom Geometry** | NodeSocketGeometry | none | Full custom bar geometry. For predictable baseline behavior, make it approximately 1 unit tall and centered on Z=0. |
| Profile | **Material** | NodeSocketMaterial | none | Material applied to every bar |

## Outputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Outputs | **Geometry** | NodeSocketGeometry | none | Audio-reactive bar instances |
| Outputs | **Spectrum Points** | NodeSocketGeometry | none | Points positioned at the TOP of each bar |
| Outputs | **Amplitude** | NodeSocketFloat | 0 | none |
| Outputs | **Normalized** | NodeSocketFloat | 0 | none |
| Outputs | **Band Index** | NodeSocketInt | 0 | none |
| Outputs | **Band Position** | NodeSocketFloat | 0 | none |
| Advanced Outputs | **Raw Spectrum** | NodeSocketGeometry | none | Unpositioned analyzer carrier geometry |
| Advanced Outputs | **Raw Amplitude** | NodeSocketFloat | 0 | none |
| Advanced Outputs | **Low Frequency** | NodeSocketFloat | 0 | none |
| Advanced Outputs | **Center Frequency** | NodeSocketFloat | 0 | none |
| Advanced Outputs | **High Frequency** | NodeSocketFloat | 0 | none |
| Advanced Outputs | **Bandwidth** | NodeSocketFloat | 0 | none |

## Verification source

This page was generated from the public Blender interface exported by
tools/export_public_node_interfaces.py against a fresh toolkit build. Update
the screenshot and regenerate this page whenever the public interface changes.
