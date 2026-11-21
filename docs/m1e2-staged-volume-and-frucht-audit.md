# Frucht 3D geometry audit → Strawberry Lab M1e2 staged volumetric foundation

**Date:** 2026-11-21. **Intent:** return to a programmable 3D fruit generator rather than imitating the author's still frames or expanding unsupported cell biology. **Source:** exact owner-provided *Frucht Free Kiwi 0.4.3* archive + `daten/kiwi.blend`, opened in Blender 5.2.4 LTS; our own saved M1e scene and new Blender results. Frucht's paid strawberry `.blend` is **not** available.

## What the author's software actually contains

### A. Directly verified in free `kiwi.blend`

- The main `KIWI • Frucht komplett` Geometry Nodes graph (38 nodes) assembles a body mesh, seed geometry, hairs and calyx, and a cut. A `Mesh Boolean` in `DIFFERENCE` mode consumes a separate `KIWI • Schnitthalbraum` cut/half-space mesh. The result passes into an independent edge-repair group, `KIWI • Schnittkante aus einem Guss`.
- `KIWI • Zellen am Schnitt` (244 nodes) returns **Geometry**, joined separately into the output of the main graph. It contains **3 Mesh Grid**, **5 Volume Cube**, **4 Store Named Grid** / **4 Get Named Grid** and calls `KIWI • Zellfarbe`, `KIWI • Zelltypen` and `KIWI • Leitbündel`. This is a mixture of actual generated mesh surfaces, 3D volume fields and vessel geometry, not merely an image shader.
- `KIWI • Zelltypen` (154 nodes) uses **5 Voronoi Texture** nodes (3 in 3D and 2 in 4D), with additional math/noise. `KIWI • Gewebe` (301 nodes) yields 19 scalar fields describing regions; they are fields, not 19 prebuilt isolated cell-mesh populations. `KIWI • Leitbündel` (408 nodes) uses three independent curve-to-mesh pipelines for geometry.
- **Important limit:** Kiwi's top-level `Mesh Boolean` is not proof of a universal SDF cutter across all fruits. The codebase also contains SDF-based procedures, and the author's strawberry explanation describes SDF, but the exact paid strawberry Geometry Nodes graph has not been inspected.

### B. Strawberry-specific mechanisms present in the free Python archive

These are inspected *source-level* functions: they cannot be claimed as a successfully executed paid-strawberry scene without its `.blend`.

- `leitbuendel.py` declares a procedural cavity-mesh builder; the cavity is an **actual 3D mesh**, not a dark spot in a 2D cut texture.
- `schnitte.py` uses an outer body + tagged cavity geometry, and a Geometry Nodes **Bake** for stored/restored source geometry. It constructs a named 3D SDF grid of `body − cavity`, then separately subtracts the cutter and converts the result back to a surface mesh.
- Cut-face type is treated as data: the source uses named attributes to distinguish the outer skin, newly exposed cut and inner cavity wall, and assigns materials accordingly. A dedicated source surface layer handles cut-edge treatment.
- `zellen.py` has a separate modifier for **real geometry on cut faces**: it selects faces by cut material, subdivides only these faces, displaces them using cell fields and the precomputed vascular image, and recombines them with untouched geometry. It exposes independent `Cell Size`, `Height`, `Strand Relief`, `Edge Fade`, and `Detail` controls.
- `saft.py` and related material groups add wet surface/under-surface appearance separately from geometry. This does not imply that every histological cell exists as a watertight mesh throughout the entire fruit.

**Engineering interpretation:** there is a durable **3D substrate**, plus a **cut geometry pipeline**, plus **on-demand mesoscopic surface geometry**, plus **visual look-development**. These are complementary; none alone reproduces Frucht.

## Our implemented M1e2 (independent code, no vendor nodes copied)

New `.blend` built **from existing Strawberry Lab M1e**, leaving the original unchanged:

1. `SourceVolume`: convert previously saved watertight body and independent cavity objects to signed-distance grids, subtract cavity and preserve the output under the named 3D grid `fruit_solid`.
2. `Live Cut`: use a distinct evaluated source object; `Get Named Grid('fruit_solid')` → subtract the animated knife SDF → `Grid to Mesh` → original M1e rest-coordinate, material and displacement logic.
3. Seed masking remains linked to the same live knife, independently of the new source-volume group.

This is **staged but NOT baked/cached** yet; its runtime performance is not claimed to be faster. Importantly, the result preserves the same mesh and look as M1e, so this experiment isolates architecture, not aesthetics.

### Independent tests on saved `.blend` reopened in Blender 5.2.4

| Frame | Topological interpretation | Evaluated body vertices | Surface components | Non-manifold edges | Evaluated seed vertices |
|---:|---|---:|---:|---:|---:|
| 1 | intact outer shell + sealed internal cavity | 44,474 | 2 | 0 | 90,552 |
| 15 | knife intersects and opens the cavity | 31,482 | 1 | 0 | 56,448 |
| 30 | deeper cut; cavity exposed | 20,894 | 1 | 0 | 38,304 |

There are **2** body/cavity SDF mesh conversion nodes and **1** SDF difference in `SourceVolume`; the separate live-cut group has **1** knife SDF conversion, **1** SDF difference and **1** `Get Named Grid`. The scene was saved, reopened and validated. The real CPU Cycles frame 15 (640 px, 10 samples) rendered successfully. Its pixels were **bitwise identical** to the same frame from the former M1e implementation (PIL pixel difference bounding box: `None`, three-channel average absolute error = 0). This is deliberately not a visual-quality victory.

### Reproduce with local Blender 5.2+

```bash
blender -b strawberry-m1e-cavity-and-knife.blend \
  --python src/build_staged_volume_m1e2.py -- \
  --out /tmp/strawberry-m1e2-staged-volume.blend

blender -b /tmp/strawberry-m1e2-staged-volume.blend \
  --python src/validate_staged_volume_m1e2.py -- \
  --out /tmp/staged-validation.json

blender -b /tmp/strawberry-m1e2-staged-volume.blend \
  --python src/render_staged_volume_m1e2.py -- \
  --frame 15 --samples 10 --out /tmp/frame15-cycles.png
```

**Source M1e:** `strawberry-m1e-cavity-and-knife.blend` from our previously completed local M1e experiment. Keep its SHA and storage location separate from Frucht's original `kiwi.blend`. No Frucht ZIP, GPL code, vendor node tree, images or commercial asset have been added to the public repository.

## What our generator still lacks — prioritized engineering gates

1. **Actual `CutSurface` geometry module** working exclusively on cut faces: local subdivision, multi-scale procedural cell domes/pores, seam-safe displacement, cavity-specific detail. Use a shared 3D rest-space field, not one texture per camera/cut. The current cut is flat and this is the largest immediate visual gap.
2. **3D filament/vascular features, visible when the cut opens the cavity**, built as curves/implicit fields and clipped consistently; separate from simulated photographic color. Avoid invented physiological claims.
3. **Independent `Body/Seed/Pit/Calyx` geometry**, sharing the same shape parameters and cutter. In M1e the calyx is hidden and achenes are clipped by point centers, not full solid intersection.
4. **Bake/LOD/performance contract** for the stable source field. Until source is actually baked and change invalidation tested, splitting nodes is not a speed optimization. Benchmark memory, time per cutter motion, and mesh size.
5. **Deterministic visual acceptance tests**: true Cycles whole, sliced, bitten and cavity macro renders at fixed camera/light. Compare with original author film by feature, not by number of Blender nodes. Support 'Fast' vs 'Exact' if empirically useful.

The current stage proves that the architecture can be separated without changing output. It **does not** assert Frucht parity, micro-histological accuracy or precomputed cache performance. It also does not establish that the paid strawberry uses exactly the observed Kiwi node graph.
