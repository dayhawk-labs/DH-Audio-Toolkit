# DH Audio Analyzer

![DH Audio Analyzer](../images/node-previews/dh-audio-analyzer.png)

**Category:** Analysis<br>
**Blender domain:** GeometryNodeTree<br>
**Default node width:** 330 px

General-purpose Blender 5.2 multi-band audio analyzer with FFT/window controls, linear/log spacing, response shaping, compact internal architecture, and named attributes.

## Agent notes

- Start modular geometry workflows here. Spectrum carries the standard dh_audio schema.
- Use Spectrum Points before Curve or Fill; use Spectrum Bars for a self-contained visualizer.

## Key choices

- **Window Function** and **FFT Size** use Blender 5.2's native Sample Sound Frequencies menus; their defaults are Hann and 8192.

## Interface panels

- **Audio**: open by default; Sound, time, channel and FFT controls
- **Spectrum**: open by default; Frequency distribution and band count
- **Response**: open by default; Normalize and shape sampled amplitudes
- **Carrier**: collapsed by default; Advanced spacing of the internal carrier points
- **Primary Outputs**: open by default; The outputs used most often for geometry and modulation
- **Frequency Metadata**: collapsed by default; Detailed per-band frequency information

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
| Spectrum | **Bands** | NodeSocketInt | 32 | Number of frequency bands |
| Spectrum | **Min Frequency** | NodeSocketFloat | 30 | Lowest analyzed frequency |
| Spectrum | **Max Frequency** | NodeSocketFloat | 1.6e+04 | Highest analyzed frequency |
| Spectrum | **Logarithmic** | NodeSocketBool | on | Logarithmic frequency spacing when enabled; linear Hz spacing when disabled |
| Response | **Gain** | NodeSocketFloat | 1 | Multiplier applied before normalization |
| Response | **Floor** | NodeSocketFloat | 0 | Post-gain amplitude mapped to zero |
| Response | **Ceiling** | NodeSocketFloat | 0.8 | Post-gain amplitude mapped to one |
| Response | **Clamp to 1** | NodeSocketBool | on | Clamp normalized amplitude to a maximum of one |
| Response | **Response** | NodeSocketFloat | 0.7 | Power curve. Below 1 emphasizes quieter values; above 1 emphasizes peaks |
| Carrier | **Spacing** | NodeSocketFloat | 1 | X spacing between internal carrier points |

## Outputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Primary Outputs | **Spectrum** | NodeSocketGeometry | none | One carrier vertex per frequency band with standardized named attributes |
| Primary Outputs | **Amplitude** | NodeSocketFloat | 0 | Processed response field |
| Primary Outputs | **Normalized** | NodeSocketFloat | 0 | Normalized response before power curve |
| Primary Outputs | **Band Index** | NodeSocketInt | 0 | Zero-based band index |
| Primary Outputs | **Band Position** | NodeSocketFloat | 0 | Normalized 0-1 position across bands |
| Frequency Metadata | **Raw Amplitude** | NodeSocketFloat | 0 | Native sampled amplitude |
| Frequency Metadata | **Low Frequency** | NodeSocketFloat | 0 | Lower frequency bound |
| Frequency Metadata | **Center Frequency** | NodeSocketFloat | 0 | Center frequency |
| Frequency Metadata | **High Frequency** | NodeSocketFloat | 0 | Upper frequency bound |
| Frequency Metadata | **Bandwidth** | NodeSocketFloat | 0 | Band width in Hz |

## Verification source

This page was generated from the public Blender interface exported by
tools/export_public_node_interfaces.py against a fresh toolkit build. Update
the screenshot and regenerate this page whenever the public interface changes.
