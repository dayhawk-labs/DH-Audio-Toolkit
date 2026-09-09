# Demo files

## Peak-Hold Waterfall Demo

[Download the demo blend](DH%20Audio%20Toolkit%20Peak%20Hold%20Waterfall%20Demo.blend)

Open in Blender 5.2+ and play from frame 1. The file includes a short synthetic
Sound datablock packed into the file and assigned to the Analyzer, so the demo
is immediately playable. Replace it with your own Sound if desired. The file
also includes a deterministic waterfall preview mesh, material, camera, and
lights for a quick viewport/render check.

The verified Analyzer → Temporal Response → Spectrum Points → Spectrum History
Surface workflow has labeled stages and an in-file usage note. Simulation Zones
still need sequential playback or baking before judging the final animation.

Rebuild it with `tools/create_peak_hold_waterfall_demo.py` if the toolkit
interface changes.
