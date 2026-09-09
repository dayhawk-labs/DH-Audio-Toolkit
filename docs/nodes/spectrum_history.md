# DH Audio Spectrum History

![DH Audio Spectrum History](../images/node-previews/dh-audio-spectrum-history.png)

**Category:** Temporal<br>
**Blender domain:** GeometryNodeTree<br>
**Default node width:** 310 px

Accumulate positioned spectrum points into a bounded waterfall history. Optionally generates a decimated connected quad surface, preserves spectrum attributes, supports changing band counts and reset, and exposes dh_audio_history_index / dh_audio_history_pos. Requires sequential timeline evaluation or a simulation bake for complete history.

## Agent notes

- This is stateful: play sequentially or bake it. A frame jump into a fresh simulation has no earlier rows to retain.
- Surface is disabled by default. Enable it only for a connected waterfall mesh, then use Row Decimation to control density.

## Key choices

- **Surface:** off by default. Enable it to emit the connected waterfall mesh, then adjust Row Decimation for density.

## Interface panels

- **Source**: open by default; Positioned spectrum geometry to capture each frame
- **History**: open by default; Bounded simulation history and row spacing
- **Surface**: open by default; Optional connected mesh from retained spectrum rows
- **Outputs**: open by default; History geometry and normalized row-age fields

## Inputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Source | **Spectrum Points** | NodeSocketGeometry | none | Positioned spectrum geometry from DH Audio Spectrum Points or DH Audio Spectrum Bars |
| History | **Frames** | NodeSocketInt | 32 | Maximum number of spectrum rows retained, including the current row |
| History | **History Offset** | NodeSocketVector | (0, -0.15, 0) | Translation applied once per frame of row age |
| History | **Reset** | NodeSocketBool | off | Discard previous rows and restart history from the current spectrum |
| Surface | **Surface** | NodeSocketBool | off | Build a connected quad surface from the retained history rows |
| Surface | **Row Decimation** | NodeSocketInt | 1 | Use every Nth history row in the connected surface |

## Outputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Outputs | **History** | NodeSocketGeometry | none | Current spectrum plus bounded previous rows |
| Outputs | **Surface** | NodeSocketGeometry | none | Optional connected waterfall mesh; disabled by default |
| Outputs | **History Index** | NodeSocketInt | 0 | Row age in frames: current = 0, oldest = Frames - 1 |
| Outputs | **History Position** | NodeSocketFloat | 0 | Normalized row age from 0 at current to 1 at oldest |

## Verification source

This page was generated from the public Blender interface exported by
tools/export_public_node_interfaces.py against a fresh toolkit build. Update
the screenshot and regenerate this page whenever the public interface changes.
