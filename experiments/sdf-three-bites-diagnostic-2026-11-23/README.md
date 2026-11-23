# Strawberry Lab — one spherical bite versus three overlapping bites (2026-11-23)

**Status:** real Blender 5.2.4 LTS experiment; structural SDF output PASS in tested states after a *scoped* seed-guard correction; visual Frucht target still **FAIL**. Research only in existing draft PR #49 stacked on draft PR #48. **Do not merge into `main`.**

## What was actually observed

The owner's licensed private Frucht reference video at ~18.5 s shows the interface **Bites=2**, ~19.5 s **Bites=3**, with a much less circular opening than the current single-bite render. The public/free Frucht 0.4.3 `schnitte.py` includes authored spherical bite construction and shape perturbation, but the full commercial Strawberry `.blend` was **not inspected**; the exact commercial cutter graph is unknown. No external Frucht media, GPL source or node trees are redistributed in this study.

Independent Blender inspection of current SHA-pinned cell-coherent Strawberry scene found `SDF | editable sphere bite`: **6,050 mesh vertices all on unit radius (CV≈0)**. This is an actual mathematically smooth sphere, despite many previous attempts to roughen only the *cut flesh*. Thus our previous 'smooth bowl' comparison held a major visual variable constant that the author visibly changes: number/shape of bites.

## One bounded controlled A/C test

Source: owner-private [cell-coherent-B.blend](https://drive.google.com/file/d/1tDM4Gf3qd01fmWAG95aIVCyoHfbXJh0G/view), SHA256 `4732b465b103f9a0b4ab262dfeae51e26a8865aa586c3779d472d86eed845399`.

- **A**: exactly the source single perfect sphere, unchanged cell texture, roughness, SSS, original body, 264 original achenes, 150³ color atlas and separate 192³ vascular core/halo atlas.
- **B (deliberately broken regression control)**: three **new original smooth spheres** with local centres `[(-.39,-.04,.22),(.36,.07,.11),(-.05,-.02,-.42)]`, radius `.78`; native Blender EXACT mesh Boolean UNION, then *baked* once into the same editable SDF cutter object. Pre-bake live Boolean was unnecessarily costly when repeated across seed evaluations. Connected resulting cutter: **10,681 vertices / 10,561 faces, 0 nonmanifold**, local volume **4.232934 BU³**, only **1.054%** above source unit-sphere volume. Geometry and its movement remain native Blender, without invoking a saved script.
- **C**: exactly the **same cutter B**, but correct the per-seed analytic sphere-intersection mask for this specific three-ball union using the minimum of three unit-space centre distances; supports cutter *uniform scaling and rotation* in that analytic expression, but **NOT arbitrary cutter meshes**. Only the shared seed GN group changes 21 → 32 nodes, all 264 seed object sources unmodified.

These are **ARTIST** geometry coordinates, not measurements or a source-specific reconstruction of Frucht's paid model. **Only number/distribution of smooth bites** was changed in the controlled visual comparison; the author's separately perturbed cutter shape was not reproduced.

## Independent actual saved-Blender QA — geometry and seeds

A and C: script execution disabled during load; raw fruit source, 264 seed meshes, both original packed atlases, body GN group and cut shader confirmed **SHA-identical**. For C: independent native evaluated SDF test reports from the saved scene:

| Pose / voxel | Body vertices | Body manifold | Seeds visible / expected from actual cutter BVH | Retained seed vertices inside cutter |
|---|---:|---|---:|---:|
| Whole, 0.32 mm | 91,046 | PASS | n/a | n/a |
| Plane, 0.32 mm | 59,400 | PASS | n/a | n/a |
| Side bite, 0.32 mm | **92,848** | PASS | **207 / 207** | **0** |
| Side bite, 0.20 mm | **238,088** | PASS | **207 / 207** | **0** |
| Moved bite, 0.32 mm (translation only) | 92,110 | PASS | **199 / 199** | **0** |
| Moved + rotated bite, 0.32 mm | 90,004 | PASS | **196 / 197** | **0** |

The moved+rotated case illustrates **conservative over-culling of one achene**, likely due to analytic sphere versus polygonal Boolean boundary. It is NOT an exact visibility PASS. No penetration was observed, but arbitrary transformations and arbitrary cutter topology remain unproved. The original perfect-sphere A side bite, both resolutions, retained 202/202 seeds and zero intrusions. Source WHOLE and PLANE body vertex-coordinate SHA is identical between A and C.

**Important discovered limitation in existing PR #48:** its original seed GN actually evaluates `Length(seed_vertex_position - cutter_location) < cutter_scale`, i.e. an **analytical perfect sphere** (one shared 21-node group), while the body uses **the evaluated cutter mesh** as a general SDF. When cutter mesh changes to B's three-ball union, the body stays manifold, but the seed mask **fails**: **202 shown vs 207 expected**, and **1,310 retained seed vertices** lie in the *actual* cutter. The defect was rechecked using BVH on the genuine evaluated cutter triangles, not only a mathematical sphere. Source `qa_baked_fast.py`/`qa-bite-032.log` shows the failing assertion. Scoped C repair makes 207/207 and zero actual cutter-vertex penetrations at both resolutions.

Portable reproduction `build_portable.py` re-built A, B and C from the exact original source in a fresh output directory. Independent native QA on re-built C reproduced the **same evaluated body-coordinate SHA** and 207/207 seed guard at both `.32/.20` mm. `.blend` binary serialization hash varies with save paths; evaluated mesh and field provenance are the cross-run acceptance gates.

## Original matched Blender Cycles A/C

One SDF side-bite view per variant, **480×480 /12 samples, CPU Cycles, RNG seed1729**, identical camera, cutter transform, lights, scene colour management, same tissue material and 3D atlases. No ImageGen or retouching. The true original PNGs and JSON receipts are preserved.

| Metric A vs C | Measured |
|---|---:|
| Pixel change >2 RGB/255 | **18.194%** |
| Pixel change >10 RGB/255 | **15.257%** |
| A/C render elapsed (not controlled multirun benchmark) | 13.6 / 19.3 s |

**Visual verdict:** C gives a less circular upper edge and locally intersecting lobes, but still shows a **broad blurred pale core, smooth red hollow and insufficient wet ruptured microstructure**. It does not approach the author's 19.5-s visual target. The reference frame has a different perspective, shape, colour management and lighting; pixel-to-pixel author similarity is NOT measured.

## Reproduce and provenance

With Blender 5.2.4 LTS installed and the verified private source scene:

```bash
BLENDER=/path/to/blender
ROOT=experiments/sdf-three-bites-diagnostic-2026-11-23
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/build_portable.py" -- --source inputs/cell-coherent-B.blend --outdir build/three-bites/scenes
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/qa_native.py" -- --scene build/three-bites/scenes/bite-C-three-fixed.blend --pose bite-032 --out build/three-bites/qa-C-032.json
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/qa_native.py" -- --scene build/three-bites/scenes/bite-C-three-fixed.blend --pose bite-020 --out build/three-bites/qa-C-020.json
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/render.py" -- --scene build/three-bites/scenes/bite-C-three-fixed.blend --out build/three-bites/bite-C-480.png --shot bite --resolution 480 --samples 12
```

For the baseline image repeat render with `bite-A-one.blend`; invoke `compare_cutter.py --a <A.png> --c <C.png> --out <contact.png> --report <comparison.json>`. Material, shader and actual cutter parts are independent original project work. The **public repo** contains only this README, own build/QA/render/compare scripts and numerical findings. Full owner-private `.blend`, Blender Cycles PNG and SHA manifest live in Drive.

**Next priority based on evidence:** before more cellular-fibre inventions, make a **single generic actual-cutter seed-visibility contract**, ideally reusing the SDF source/derived signed distance already sampled by the body rather than re-rasterizing an expensive per-seed cutter. Test general closed cutter meshes, rotations and precise conservative solid-intersection policy. Separately improve bite surface optical/material look by region, not endless scalar tear or SSS tuning. Do **not** merge A/B/C into `main` or edit PR48's implementation under an implicit approval.
