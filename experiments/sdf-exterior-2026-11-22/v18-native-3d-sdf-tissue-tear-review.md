# Strawberry Lab — v18 native 3D SDF tissue-tearing probe (23 Nov 2026)

**Engineering PASS, Frucht visual fidelity FAIL; research branch only.**

## Tested hypothesis

The earlier v16/v17 found only 1–2% of visible cap area sampled original high-strength vascular R, and raising R opacity alone did not repair the smooth bowl-like bite. v18 tests whether geometry driven by a **single persistent 3D rest-space tissue-cohesion field**, applied **before isosurface meshing**, can produce visible attached torn-flesh relief without generating disconnected decorative tubes or painting a new 2D map for each cut pose.

Original is verified v12 SHA-256 `300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7`. Three independently saved editable Blender 5.2.4 LTS native Geometry Nodes scenes from the exact same source and code:

- **v18A**: same SDF body/cutter resampling pipeline, field displacement gain `0` (controls the effect of changing the mesher alone).
- **v18B**: gain `1.0` (full original ARTIST 3D field, up to `+0.90 mm` local resistance and `-0.28 mm` soft erosion at full masks).
- **v18C**: exactly same algorithm with **only gain `0.28`**, a bounded low-amplitude control; no new algorithm or shader changes.

## Actual construction

In both native SDF cutter groups, body and live knife SDF grids are sampled at the same 3D voxel positions. An independently authored **ARTIST** volume function combines the original `v8` vascular rest-space R value and two anisotropically scaled 3D noise fields; it gives a signed soft-tissue displacement independent of camera or knife orientation. The implicit body-minus-cutter density is reconstituted by `Volume Cube → Volume to Mesh`, then the **unchanged** v12 material, rest-space attribute and cut-local micro-relief GN pipeline is evaluated. The original packed atlas is untouched in all three scenes; SHA-256 of the packed image file remains `38c8f94099425d634d09607a46c160bbcf54ff350b94d9439a3c9868985c6317`, equal to v12. Original body and seed/calyx data are not replaced. Field volume: X/Y [−19,+19] mm, Z [−5,+53] mm; grid 140×140×214 (~0.271 mm pitch). Cutting stays editable in Blender without Python autoexec.

**Not implemented:** physiological vascular solidity, 3D cell membranes, exact fiber fragment intersections, measuring histological strain, dynamic calyx clipping. The new 3D field is artist-authored scalar deformation, **not biological tissue reconstruction**, and no commercial Frucht assets or graphs are copied.

## Independent Blender QA

Reopened A/B/C saved .blend with autoexec disabled; five actual evaluated poses for each: whole, planar, bite, moved+rotated planar, moved+scaled bite. Every one of **15/15** body states had **0 non-manifold edges, positive signed volume and positive minimum face area**. Both edited and moved cutter poses generated different evaluated SDF geometry. Each cut showed material-index-2 flesh-cap faces and retained `fruit_rest`, `v8_vascular_intensity` and `v8_cell_height_mm` attributes.

| Original pose | A: vertices / volume (mm³) | B: vertices / volume (mm³) | C: vertices / volume (mm³) |
| --- | --- | --- | --- |
| Whole | 157250 / 21506.8 | 157250 / 21506.8 | 157250 / 21506.8 |
| Plane | 189804 / 6777.8 | 207442 / 6739.2 | 191322 / 6767.6 |
| Bite | 341932 / 18828.4 | 350546 / 18792.1 | 342454 / 18818.6 |
| Plane moved | 151000 / 4267.3 | 161508 / 4228.0 | 151398 / 4256.2 |
| Bite moved | 352718 / 16704.3 | 366438 / 16678.0 | 353950 / 16697.7 |

v18B sometimes creates very small nonzero face areas (down to 3.8e-8 mm² at an original pose); this may indicate awkward needle triangles, so manifold testing is not a visual-quality guarantee. Peak RAM during full QA was ~1.3 GB per native process; not a benchmark of isolated node update, and VRAM unmeasured.

**Separate v18C seed guard check:** actual evaluated meshes in two original and two moved cut poses contained **0 seed vertices strictly inside original cutter** out of **106,088 tested mesh vertices**. This is a nearest-triangle normal test on a watertight cutter, not exhaustive triangle–triangle intersection of arbitrary seed/cap solids. Same original material and 3D atlas provenance confirmed.

## Real Blender Cycles and outcome

Two matched 640×640, 24-sample CPU Cycles PNGs for **each** A/B/C, same camera, lighting, seed and original v12 reference renders. Combined contact sheet: `strawberry-v18-final-A-B-C-Cycles.png` (rows planar / bite / bite macro, columns original / A / B / C).

| Pixels with max RGB change >0.01 vs original v12 | Plane | Bite |
| --- | ---: | ---: |
| A (meshing-only control) | 1.638% | 4.530% |
| B (full fracture) | 12.505% | 9.811% |
| C (0.28× fracture) | 6.950% | 7.236% |

These are **change fractions**, not quality metrics. Visual manual review of genuine Cycles images: v18B introduces physically modeled protrusions and folds, but its planar cut looks like crumpled red material rather than wet strawberry cells; bite still looks too much like a scooped sphere. v18C reduces the false geometric folds but also weakens the desired torn fibers; it likewise is **not accepted**. New SDF meshing itself causes small differences vs baseline, measured by A. Color and subsurface material remain too smooth/monochrome; torn edge silhouette is not a close reference match.

**Decision:** preserve source v12; keep v18A/B/C as bounded research diagnostics and **do not merge to `main`**. This hypothesis proves a live 3D scalar field can change actual watertight SDF cut geometry, but it does **not** prove visually believable connected fibrous tissue. Next useful mechanism is a source-grounded persistent 3D branched cellular/vascular structural model with nontrivial fragment attachment physics, not yet another amplitude or gloss tweak. Any future test must again evaluate at least two noncollinear cutters, field consistency, actual Blender Cycles photos and strict positive-volume/no-nonmanifold gates.

## Reproduction and storage

Main implementation: `build_v18_sdf_torn.py` (Blender + original v12); QA `validate_v18.py`, `validate_v18_seeds.py`; 6 renders from `render_v18.py`. `compare_all.py` records per-pixel differences. See JSON build, validation and render receipts and bundled SHA256 manifest. The three .blend are **separate editable files** in this private archive, not put into public GitHub. A/B/C original source and comparative contact sheet stay private; **no Drive upload claimed**. The original `.blend` remains accessible through its owner-restricted Drive ID, as documented in PR #43.

The archive contains only our independent scripts, scenes and rendered images; no private Frucht source/video/image pixels or GPL Kiwi nodes are redistributed.
