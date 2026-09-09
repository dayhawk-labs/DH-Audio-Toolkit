# DH Audio Spectrum Points

![DH Audio Spectrum Points](../images/node-previews/dh-audio-spectrum-points.png)

**Category:** Mapping<br>
**Blender domain:** GeometryNodeTree<br>
**Default node width:** 285 px

Map DH Audio Analyzer carrier geometry into visible audio-height points. The output is compatible with Spectrum Bars' Spectrum Points, Spectrum Curve, and Spectrum Fill.

## Agent notes

- This is the normal bridge from Analyzer carrier geometry to visible, positioned points.
- Spectrum Points is the intended input for Curve, Fill, History, and many custom geometry workflows.



## Interface panels

- **Spectrum**: open by default; Map analyzer carrier points into visible audio-height points
- **Layout**: open by default; Height and horizontal placement
- **Outputs**: open by default

## Inputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Spectrum | **Spectrum** | NodeSocketGeometry | none | Use the Spectrum output from DH Audio Analyzer |
| Layout | **Height** | NodeSocketFloat | 3 | Height added at amplitude 1.0 |
| Layout | **Baseline** | NodeSocketFloat | 0 | Z value corresponding to zero amplitude |
| Layout | **Center Spectrum** | NodeSocketBool | on | Center the source carrier around X=0 before X Scale is applied |
| Layout | **X Scale** | NodeSocketFloat | 1 | Horizontal scale around the centered spectrum |
| Layout | **X Offset** | NodeSocketFloat | 0 | Horizontal offset after centering and scaling |

## Outputs

| Panel | Socket | Type | Default | Description |
| --- | --- | --- | --- | --- |
| Outputs | **Spectrum Points** | NodeSocketGeometry | none | Audio-height points carrying the original analyzer attributes. Compatible with DH Audio Spectrum Curve and DH Audio Spectrum Fill. |

## Verification source

This page was generated from the public Blender interface exported by
tools/export_public_node_interfaces.py against a fresh toolkit build. Update
the screenshot and regenerate this page whenever the public interface changes.
