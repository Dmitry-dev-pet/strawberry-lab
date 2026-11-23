# PR49 continuation: integrate existing owned v19/v20 core + broad halo into seed101 SDF

**23 Nov 2026 — research technical PASS for tested poses; visual FAIL. Not merged.**

This is the integration of **existing** owned Strawberry Lab research, not a new generic noise direction. It is stacked on [PR48](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/48), which still awaits review, and follows technical baseline [merged PR47](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/47). The previous shader-only / single-noise PR49 results are preserved under `experiments/sdf-rest-relief-2026-11-23/` as negative/comparison evidence. This implementation is *not* the commercial Frucht Strawberry model; no Frucht GPL/commercial nodes, binary data or preset values are reproduced.

## What is actually integrated

- Reuse **exact owned `v19_graph.py` and `fields.py` algorithms from PR46**, now rerasterized for the **264 current seed101 original-rest achene anchors**, not the older v20 seed population. Graph validation: one connected root, 28 carriers, 264 terminal branches, 264 attached twigs = **557** total; 264/264 endpoints exactly on the new saved anchors.
- Deterministic **192³** scalar volume: independent core R and broader influence H, with H = max(core, Gaussian-width×1.8). The authored graph is in **physical millimetres**: `xyz_mm = sdf_rest_position * scene_mm_per_BU + (0, 0, 27 mm)`; bounded by x/y=±25 mm, z=[−2,+52] mm. Coefficients ARTIST, not botanical measurements. New atlas packs R+H in a separate Non-Color RGB image (16×12 XY slices). The original 150³ packed material atlas, its channel meanings and source geometry are preserved.
- Reuse the **owned v8/v20 trilinear sampling algorithm** via `sampler.py`, creating all its native GN nodes directly from code. No old private v20 `.blend` dependency is required any more. Independent comparison against NumPy trilinear sampling at **150 real cut vertices** gave max abs R error **2.18×10⁻⁵**, H error **1.35×10⁻⁵**.
- On the existing native PR48 SDF body, add **a single cut-local Set Position** based on an original 3D Voronoi cell signal, smoothed by the chosen **narrow R vs broad H** field, plus the same narrow R vascular ridge. `sdf_use_broad_halo=0/1` isolates the effect of halo on cells; `sdf_tissue_gain=0/1` restores the exact baseline body. The source achene per-vertex cutter guard remains untouched. Max actual B-vs-baseline displacement on tested poses **0.1385 mm**, core-vs-halo difference up to **0.0229 mm**, source whole mode unchanged. Cell/ridge gains 0.045/0.18 mm are ARTIST. This reuses the prior architectural principle but is **not** a byte-identical transplant of the v20 surface/material: the source Blender graph differs.

## Evidence

- Blender **5.2.4 LTS**, headless CPU, saved scenes reopened with autoexec disabled. **10/10 sampled cases**: 0.32mm and 0.20mm × whole, plane, oblique plane, sphere, open-side sphere; full geometry QA independent A (no tissue), core and halo. All evaluated bodies: one connected component, **zero nonmanifold edges, strictly positive signed volume, no degenerate render triangles**; same underlying topology within each A/core/H state, and WHOLE positions identical. High-resolution poses were run in separate processes to avoid unbounded session memory.
- Seed/cutter test on saved scene: **whole 264, straight plane 130, oblique 114, open-side bite 202** retained achenes, zero retained vertices inside cutters in each tested pose. This is conservative hiding, not exact physical seed slicing or exhaustive triangle intersection.
- The original packed 150³ atlas and raw body mesh remain unchanged; H≥R. The generated 192³ field is **the same three-dimensional dataset** for every cutter pose, no camera-specific 2D cuts.
- Real Cycles **640×640, 16 samples, seed 1729**, matched camera, lighting, cut pose and color management: original PNGs for plane A/core/H, open-side bite A/core/H, macro A/H. Two field A/B variants show geometry and modest image changes. On plane core-vs-halo: **1.14%** of pixels change by >2/255; bite core-vs-halo: **2.27%**. These fractions indicate actual intervention **only**, not quality.
- **Visual FAIL versus author**: slight cut-flesh texture appears, but over-wide blurred pale pith and synthetic repeating cross-hatching in side bite remain; there is no independently modeled fluid/wet film. The independent v21 weak cell-color outline socket is **not present in PR48's different material graph**, so copying `Math.039` gain 0.10→0.02 would be changing the wrong signal. v21 is **not integrated** and must not be counted as achieved visual improvement.

## Reproduce from pinned inputs

Use the owner-private [`new-qa.blend` source from PR48](https://drive.google.com/drive/folders/1kP4wbsqjXW0zOvISaCUB4EUTlmer4SUC) with SHA256 `bfecf691df67cafff020971368f1afc877f4bac1165e851520bdcc1773f85ce1`, and Blender 5.2+. From the repo root:

```bash
B=/path/to/blender
SRC=inputs/pr48-new-qa.blend
OUT=build/v20-bridge/seed101.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-v20-bridge-seed101-20261123/build.py -- --source "$SRC" --output "$OUT"
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-v20-bridge-seed101-20261123/qa.py -- --scene "$OUT" --out build/v20-bridge/qa-032.json --voxel .32 --poses whole plane plane-oblique bite bite-edge
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-v20-bridge-seed101-20261123/qa.py -- --scene "$OUT" --out build/v20-bridge/qa-020-plane.json --voxel .20 --poses plane
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-v20-bridge-seed101-20261123/qa_seeds.py -- --scene "$OUT" --out build/v20-bridge/qa-seeds.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-v20-bridge-seed101-20261123/render.py -- --scene "$OUT" --outdir build/v20-bridge/renders --shot plane --variant halo
PYTHONPATH=experiments/sdf-v20-bridge-seed101-20261123 python -m unittest test_fields
```

The builder rejects wrong input SHA or an existing output; native GN controls and packed atlas remain editable in saved `.blend`. `qa_sampler.py` can compare its sampled R/H against the separately extracted `.npz` numerical field. Each saved render has a SHA-256 receipt. Do not use pixel differences as a quality score.

## Remaining required work, not new research detour

1. Audit v21 material color path on *this* PR48 cap, rather than copying its socket ID. Fix broad pith blur and the repetitive cut relief if an isolated A/B actually improves the image.
2. Then isolate the **separate wet/liquid geometry and material** hypothesis already identified in the accessible Frucht package. Build an original implementation, preserving the same rest-space field, and test it as a separate A/B. The commercial strawberry scene is not accessible; its final look and internal implementation are not known.
3. Compare camera/perspective/scale-aligned author frames (10–11s plane, 18–20s torn bite), original Cycles from all variants, and strict geometric/seed QA. Accept only if owner approves visual outcome.

**Leave this continuation stacked on PR48, do not merge into main automatically.** Historical PR46 source and PR49 negative tests stay intact.
