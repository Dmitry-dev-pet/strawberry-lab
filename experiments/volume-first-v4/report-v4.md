# Volume First V4 — Local terminal direction: verified negative visual result

**Date:** 2026-11-21. **Blender:** 5.2.4 LTS. **Grounded by:** our V3 28 carriers at sag 0.25, our own V2 seed anchor set, privately supplied author video ~00:15.

## Hypothesis and control

The previous V3 network was visually unlike the author because almost all branches were forced into similar downward terminal slopes. The controlled experiment keeps every upstream quantity fixed, changes only each branch's final 21 samples and tests a locally different arrival direction with a smooth tangential bump. No change to global sag or main carriers is allowed. This is more discriminating than regenerating the entire network.

| Terminal strength | Median final tangent change | 90th percentile | Endpoints preserved | Central carriers |
|---|---:|---:|---|---:|
| 0.35 | 9.39° | 16.20° | 539/539 exact | 28 unchanged |
| 0.85 | 25.04° | 43.23° | 539/539 exact | 28 unchanged |
| 1.50 | 46.01° | 60.50° | 539/539 exact | 28 unchanged |

The first **43 points** of all 539 branches, all per-point tube radii, all V3 central carriers and 539 markers are identical at float32 precision. The new positions derive from the same fixed random seed and the same incoming source curves for all strengths; algorithmic output regenerates bit-for-bit. New editable Blender object splines reproduce the stored 3D NPZ values exactly after `.blend` reopen.

## Render evidence

- Four Cycles `only` views, 840×942, 12 samples, same camera, identical lighting, materials and seed-marker geometry. A `ghost` medium-strength preview shows tissue context but does not rebuild cut geometry.
- `outputs/ab-v3-v4-full.jpg` and `outputs/ab-v3-v4-terminal-crop.jpg` show authentic screenshots; same original render pixels (except the crop/rescale) — no generated pictures or visual reconstruction.
- Original vs V4 1.50: mean absolute RGB difference ~4.35/255 across the frame; ~8.22% of pixels change by more than 8 in at least one channel. This measures changed render, **not increased realism**; no perceptual benchmark was established.
- The new hooks are visible near certain seed markers, but the entire network remains a compact, oversymmetric bundle. Our endpoint constraint means tips remain just beneath the whole static berry skin.
- Frucht ~00:15 shows seemingly exposed fibers outside its visible tissue, distinct central structure and loose terminal arcs. Because camera and geometry animation/cut UI states differ, the promo still cannot serve as a pixel-equal morphology target. It may be a transient/exploded display state. That is **an inference, not a verified Frucht mode**.

## Decision

**Do not merge V4 as the default fruit generator.** It solves a localized geometric control but does not explain the central Frucht difference. Before additional curve geometry or a 256³ atlas, analyze the author clip chronologically to distinguish normal fruit morphology from animation/exposed-fiber geometry. The next controlled comparison must use equivalent *display states*, not just equal curve counts.

**Rights:** our code and test records may go to GitHub; author source, private video frame, all binary Blender/NPZ and Cycles renders remain restricted to owner Drive. No code from GPL Frucht source was copied.
