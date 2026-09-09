# Next Steps

This is the short handoff list after the 25-node reference and first verified
recipe milestone. GitHub `main` remains the source of truth.

## Recommended order

1. Add a second recipe for the fast path: `Spectrum Bars` as a self-contained
   visualizer, including sensible audio and material defaults.
2. Expand the verified Peak-Hold Waterfall Demo before creating demos for the
   other recipes.
3. Re-run the visual capture and interface export whenever a public group,
   panel default, socket, or description changes.
4. Cut the next versioned release only after the recipe and demo validation are
   complete.

## Current guardrails

- Public names and `dh_audio_*` attributes are compatibility-sensitive.
- The 25 pages under `docs/nodes/` and their PNGs are generated/reviewed
  documentation, not the source of interface truth.
- Temporal and history recipes must evaluate Simulation Zones sequentially.
- Visual captures run on the prepared VPS environment; GitHub CI remains the
  authoritative code, Blender regression, and release gate.

## Useful durable processes

- [Agent Guide](AGENT_GUIDE.md) owns change order, invariants, and review rules.
- [Node preview process](NODE_PREVIEWS.md) owns the capture and regeneration
  procedure.
- [Peak-Hold Waterfall recipe](recipes/peak_hold_waterfall.md) is the verified
  exemplar for stateful workflows and regression-backed documentation.
