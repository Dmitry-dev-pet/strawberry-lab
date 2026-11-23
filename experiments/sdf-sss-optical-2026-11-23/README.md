# Strawberry Lab — controlled cell/vascular field → SSS optical A/B (23 November 2026)

**Disposition:** ENGINEERING PASS for the specified saved-scene and raster states, **VISUAL FAIL** against the owner's Frucht video reference. No merge to `main`. Existing research Draft PR #49 on unmerged PR #48 is the intended destination. Original source and reference footage remain private.

## Why this is not another new noise / pith / geometry experiment

Prior in-project v8, v14, v17, v18, v19, v20, v21 and PR49 studies already tested cell relief, synthetic fibrils, pith-color remapping, shared vascular color, and film/menisci. The available Frucht Free 0.4.3 is an architectural reference only; the commercial Strawberry scene is unavailable. This small experiment isolates one **existing optical property**: original cut material used constant Principled `Subsurface Weight=0.08` even though its genuine evaluated GN output contains coherent `sdf_v20_core` and `sdf_v20_cell_suppression` fields. Geometry, color, rest-space, atlas, roughness and lighting remain unchanged.

## Exact provenance and intervention

- Input: owner-private PR49 `v20-bridge-portable.blend`, **SHA-256 `0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2`**, [restricted Drive](https://drive.google.com/drive/file/d/1huv9bwO4wcydPZEvnMbdBCIbfJCURvCa/view).
- Real Blender **5.2.4 LTS** x64, CPU; saved scene opens with **script autoexecution disabled**. The Blender runtime was restored independently from 17 owner Drive archive parts and verified against SHA `2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86`.
- Source material: `SDF | inherited 150^3 tissue + own multiscale wetness` (82 prior shader nodes, separate skin material). Existing Principled Subsurface Scale **0.012 Blender units ≈0.2667 mm**; radius **(1,0.2,0.1)**; weight constant **0.08**.
- Added nine *original* material shader nodes and one driver-backed body property `sdf_optical_gain`. Subsurface Weight becomes

  `SSS = 0.08 + 0.20 × sdf_optical_gain × sdf_v20_cell_suppression × (1 - 0.8 × sdf_v20_core)`

  **A:** gain 0, exactly source SSS 0.08. **B:** gain 1, point-attribute-estimated SSS 0.089–0.280 at voxel 0.20mm plane, average over all evaluated body vertices ≈0.235. All magnitudes **ARTIST, unmeasured**. Inputs are the actual existing **same persistent 192³ vascular and cellular attributes**, not a second raster map, camera-dependent color mask or any borrowed Frucht nodes. Only the Subsurface Weight socket changes; original Base Color, Roughness, Normal and all other Principled inputs (including radius/scale) are untouched.
- `build_optical_ab.py` produces separately editable `cell-optical-A.blend` and `cell-optical-B.blend`. No old source overwritten. The strict input SHA check and Blender 5.2.4 runtime gate fail closed.

## Independent Blender QA

The two saved `.blend` files were **reopened in separate Blender processes with `--disable-autoexec`**, using independent `qa_optical.py` (no builder import). Both passed **7/7 each** tested state combinations:

- 0.32mm: whole, straight plane, oblique plane, default sphere and open-edge sphere;
- 0.20mm: straight plane and open-edge sphere.

For each A/B pair, evaluated **body vertex-coordinate SHA**, face count, core attribute SHA, cell suppression attribute SHA, source mesh and packed original 150³ atlas SHA are identical; **zero nonmanifold edges** and positive signed body volume. The original whole fruit has no cut-material cap faces. New SSS material links are structurally checked, and B's optical values are finite/non-uniform. No arbitrary-cutter-wide or self-intersection proof is claimed. Peak sampled process RSS was ≈1.08GB (Linux `ru_maxrss` KiB), not isolated benchmark of the material.

## Genuine Blender Cycles A/B

Three A/B pairs were rendered in **fresh Blender processes**, 640×640, 16 samples, Cycles CPU, seed 1729, denoiser, and same camera, lights, cutter transforms and color management. `compare_render.py` checks all receipts and validates **A is pixel-for-pixel equal to the original PR49 v20 halo verified Cycles render in ALL THREE shots**:

| Scene | Pixels changed >2/255 A→B | Pixels changed >10/255 | Mean absolute RGB difference (of 255) | Time A / B |
|---|---:|---:|---:|---:|
| Plane | 4.98% | 0.0415% | 0.280 | 13.40s / 15.36s |
| Side bite | 2.26% | 0.0286% | 0.146 | 14.96s / 16.71s |
| Plane macro | 4.94% | 0.0381% | 0.280 | 15.82s / 14.88s |

These figures only show a **real shader intervention**, not a quality score. Visual inspection shows **no convincing new cellular detail, a still-broad pale central strip and a smooth bowl-like spherical bite**. Even region-adaptive SSS cannot resolve deficiencies of the existing source tissue and cutter; **the visual verdict is FAIL**. Do not continue simply increasing scattering strengths, wet glints or vessel tints.

## Qualitative Frucht reference — not reproduced or distributed here

Owner-private 38-second author video in [Drive](https://drive.google.com/file/d/1Aj17g8cIVZ-enECJAHUIXrDektWmVA-b/view). Original 10.5s cut has irregular red inner core with lit pale bundles; 18.5s bitten fruit has torn/folded attached flesh and strong localized highlights. These are **visual observations only**. The crop/pose/lighting/specimen do not match our Cycles geometry: no quantitative author fidelity comparison is possible. No author footage frames, copyrighted materials, or GPL node trees are included in this research ZIP/public PR.

## Reproduction

`B=/path/to/blender` (tested 5.2.4+), have exact owner input at `inputs/v20-bridge-portable.blend`:

```bash
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-sss-optical-2026-11-23/build_optical_ab.py -- --source inputs/v20-bridge-portable.blend --outdir build/sss-optical/scenes
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-sss-optical-2026-11-23/qa_optical.py -- --scene build/sss-optical/scenes/cell-optical-B.blend --label B --out build/sss-optical/qa-B.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-sss-optical-2026-11-23/render_optical.py -- --scene build/sss-optical/scenes/cell-optical-B.blend --shot plane --out build/sss-optical/plane-B.png --samples 16 --resolution 640
```

For a valid A/B compare, generate the same settings for A. Compare code uses verified source PNGs, which are part of the previous owner-private PR49 v20 bridge package. The artifact ZIP contains the new rendered PNGs and individual receipts, plus the original two editable `.blend` scenes. Source scene itself is **not** duplicated here. SHA-256 binary serialization may depend on Blender version/platform; trust independently reopened scene geometry and image provenance, not identical `.blend` binary across hosts.

**Decision:** preserve this independent result in existing Draft PR #49 as a measured SSS-only **negative**. Next meaningful visual hypothesis is a coordinated *cell-cut geometry + shading* change (or comparison of alternative real original material architectures), not isolated optical strength; remain within one anchored `rest_position` field. No merge to `main` without owner visual acceptance.
