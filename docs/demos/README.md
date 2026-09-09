# Demo files

## Peak-Hold Waterfall Demo

[Download the demo blend](DH%20Audio%20Toolkit%20Peak%20Hold%20Waterfall%20Demo.blend)

Open in Blender 5.2+ and play from frame 1. The file includes a short synthetic
Sound datablock packed into the file and assigned to the Analyzer, so the demo
is immediately playable. Replace it with your own Sound if desired. The file
also includes a camera, lights, and material applied by the actual Geometry
Nodes chain for a quick viewport/render check.

The verified Analyzer → Temporal Response → Spectrum Points → Spectrum History
Surface workflow has labeled stages and an in-file usage note. Simulation Zones
still need sequential playback or baking before judging the final animation.

### Wiring and result

The complete, labeled external wiring from the demo file. This is the graph to
inspect or extend; the **History Surface** output is the final geometry.

![Peak-Hold Waterfall complete wiring](images/peak-hold-waterfall-workflow.png)

The viewport result at the evaluated demo frame. It is the same waterfall
workflow with the packed synthetic Sound; play sequentially from frame 1 (or
bake) before evaluating a later frame.

![Peak-Hold Waterfall viewport result](images/peak-hold-waterfall-viewport.png)

### Individual node captures

These are the public node exteriors used by the demo, captured from Blender 5.2
at documentation scale:

| Stage | Node |
| --- | --- |
| Analyze | ![DH Audio Analyzer](../images/node-previews/dh-audio-analyzer.png) |
| Smooth and peak | ![DH Audio Temporal Response](../images/node-previews/dh-audio-temporal-response.png) |
| Position bands | ![DH Audio Spectrum Points](../images/node-previews/dh-audio-spectrum-points.png) |
| Retain and connect | ![DH Audio Spectrum History](../images/node-previews/dh-audio-spectrum-history.png) |

The `.blend` contains the labeled node-tree layout and the preview scene;
open it in Blender to inspect the complete wiring and viewport setup.

Rebuild it with `tools/create_peak_hold_waterfall_demo.py` if the toolkit
interface changes.
