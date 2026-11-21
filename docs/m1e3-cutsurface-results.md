# M1e3 — real Blender CutSurface geometry (independent prototype)

**Date:** 2026-11-21. **Status:** source-based Geometry Nodes implementation, saved-scene checks PASS, real Cycles renders reviewed. **Not** a reproduction of the commercial Frucht strawberry. No Frucht binary, GPL node tree, proprietary asset or histological measurement is copied into this work.

## Purpose and new geometry

Starting from the [verified M1e2 source-volume + live-knife experiment](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/16), M1e3 adds a distinct, editable `CutSurface` stage **after** `Grid to Mesh` and the original material attribution. M1e2's separate true 3D cavity and cutter remain unchanged.

- Identify the *actual exposed cut faces* with a `GeometryNodeMaterialSelection` field targeting the existing wet flesh material; identify *actual cavity-wall faces* independently using its cavity material.
- Refine the evaluated mesh with `GeometryNodeSubdivideMesh` (`Fast` = 1 level, `Exact` = 2 levels). This adds real vertices/edges/faces; it is not a bump texture. The current implementation subdivides **all** mesh faces; see important performance limit below.
- Evaluate **continuous 3D** Voronoi cell boundaries in the fruit's `fruit_rest` coordinate attribute, lightly warped by 3D noise, combined with separate spatial intermediate and high-frequency fields. Generated values do not depend on camera or frame.
- Displace **only selected cut vertices** along true surface normals, with smooth proximity fades at the original skin and the cavity. The untouched exterior retains original coordinates.
- Distinct 3D noise and a fade to zero at the moving knife control the cavity-wall relief.
- The source SDF volume remains built as *outer body minus persistent cavity* and is then cut by the separate moving knife. All pre-existing achene masks remain tied to the same cutter.

**This is real geometry on a cut face, not a tissue-cell packing reconstruction:** individual Voronoi cells remain implicit, not separate closed cell volumes. The synthetic pattern is an artistic design, not measured strawberry histology.

## Independent Blender 5.2.4 checks

The validator reopened each saved scene, evaluated the dependency graph at frames 1/15/30, checked face material labels, 3D rest coordinates, component topology, non-manifold edges, and confirmed nonzero geometric motion on cut/cavity but no changes on untouched skin using 2,500 reproducible samples for each region. Both Fast and Exact pass.

| Frame | M1e2 original vertices | M1e3 Fast vertices | M1e3 Exact vertices | Non-manifold edges (both) | Surface components |
|---:|---:|---:|---:|---:|---:|
| 1 (cavity sealed) | 44,474 | 177,884 | 711,524 | 0 | 2 |
| 15 (cavity opened) | 31,482 | 125,922 | 503,682 | 0 | 1 |
| 30 (deeper cut) | 20,894 | 83,570 | 334,274 | 0 | 1 |

At frame 15, the independent nearest-vertex test finds:

- **Untouched skin** — max distance = 0.0 Blender units across 2,500 sampled baseline skin-only vertices.
- **Exposed cut** — 1,254/2,500 sample positions differ by more than 0.001 BU; max nearest distance ≈ 0.02453 BU.
- **Cavity walls** — 1,921/2,500 sample positions differ by more than 0.001 BU; max nearest distance ≈ 0.00871 BU.

These tests check actual computed mesh deformation, not just node existence. Surface connectivity and non-manifold edges are topological checks; they do **not** prove no geometric self-intersections at all scales or full photoreal fidelity.

### Performance at frame 15 (current CPU, isolated evaluations)

| Mode | Calculated vertices | Evaluated mesh time | Full 720px Cycles render, 16 samples |
|---|---:|---:|---:|
| Baseline M1e2 | 31,482 | not comparably measured here | ~15.72 s |
| M1e3 Fast | 125,922 | ~0.42 s | ~16.52 s |
| M1e3 Exact | 503,682 | ~1.75 s | ~17.57 s |

Fast has 4× fewer mesh vertices than Exact. These are per-run samples on one machine, **not** universal benchmarks or a proven end-to-end real-time frame rate. A smaller 520px / 6-sample macro Cycles render also completed; a 900px 18-sample macro attempt exceeded the execution limit.

## Visual result

Compared under the **same** camera, lighting, resolution (720px), renderer and samples (16):

- M1e2: visually nearly smooth pink cut / inner wall.
- Fast: visible geometric cell-like relief on the cut and fine unevenness inside the cavity.
- Exact: smaller, more resolved irregular relief, without changing the surrounding uncut skin.
- At close range this still looks like an **artistic stippled/polygonal porous surface**, not the author's high-fidelity strawberry; neither material shading nor a full 3D vessel/strand network was rebuilt here.

The macro image uses a changed camera and fewer samples, so it must not be used as a controlled A/B brightness comparison.

## Reproduction

With Blender 5.2+ and the **M1e2 .blend** source from the owner-private Drive folder or manifest:

```bash
blender -b strawberry-m1e2-staged-volume.blend --python src/build_cutsurface_m1e3.py -- \
  --subdiv 1 --out /tmp/strawberry-m1e3-fast.blend
blender -b strawberry-m1e2-staged-volume.blend --python src/build_cutsurface_m1e3.py -- \
  --subdiv 2 --out /tmp/strawberry-m1e3-exact.blend
blender -b /tmp/strawberry-m1e3-exact.blend --python src/validate_cutsurface_m1e3.py -- \
  --baseline strawberry-m1e2-staged-volume.blend --out /tmp/m1e3-validation.json
blender -b /tmp/strawberry-m1e3-exact.blend --python src/render_staged_volume_m1e2.py -- \
  --frame 15 --samples 16 --resolution 720 --out /tmp/m1e3-cycles.png
```

The separate `render_staged_volume_m1e2.py` helper lives in [PR #16](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/16).

## Important next steps (not completed)

1. **Local/adaptive refinement:** eliminate the 4×/16× whole-fruit polygon multiplier, refine only the exposed cut with seam-preserving topology; compare elapsed times and RAM.
2. **3D strand/vascular geometry:** coherent curves/fields through pulp, correctly clipped and materialized on cuts; no invented biological measurements.
3. **More mature visual appearance:** cross-region color, wetness/SSS, less uniform cells, coherent seeds/pits, and calyx/stem under the same cutter.
4. **True source-volume caching:** current M1e2 SourceVolume is *staged but not baked*, so moving the knife may still trigger expensive graph evaluation.
5. **M1e3 cut appearance is artistic, not anatomical:** do not treat this as measured cell walls or histological tissue.

### Provenance

All source under `src/`, technical report under `docs/`, and verified SHA-256 asset manifest under `assets/` in a GitHub PR. `.blend` files, original real Cycles PNG and validation logs live in an owner-restricted versioned Google Drive folder. The M1e2 source, Frucht reference and old milestones remain unchanged.
