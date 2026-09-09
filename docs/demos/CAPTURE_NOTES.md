# Demo capture notes

These are verified issues in the current Peak-Hold Waterfall demo captures.
They are documented separately from the recipe so a future capture pass can
resolve them without confusing capture defects with toolkit behavior.

## Current viewport capture

- The default Blender cube remains in the demo scene and is visible in the
  viewport.
- The image is a camera-view viewport capture, so Blender's camera passepartout
  overlay is visible.
- A large angular artifact appears where the cube intersects or overlaps the
  evaluated waterfall result. The exact geometry contribution still needs to be
  isolated.
- The current image should not be treated as a polished presentation render.

## Current wiring capture

- `peak-hold-waterfall-workflow.png` is cropped on the left.
- The Analyzer and Temporal Response stages are not fully visible.
- The `.blend` node tree is the authoritative source until a full-bounds
  capture is regenerated.

## Next capture requirements

1. Remove or hide unrelated startup objects from the showcase view.
2. Capture the evaluated result without camera passepartout UI chrome.
3. Isolate the artifact before changing materials or geometry behavior.
4. Frame the complete external node tree after layout, then crop only after
   confirming all four public stages are inside the image bounds.
