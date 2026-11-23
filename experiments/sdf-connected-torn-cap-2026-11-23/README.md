# Strawberry Lab — connected cap-face pull-out (research negative), 23 Nov 2026

**Engineering: PASS only for the small A/B variant and seven tested cutter/voxel states. Visual Frucht acceptance: FAIL. More aggressive versions FAIL topology.** This is a bounded follow-up in research PR #49 stacked on unmerged PR #48, NOT a main-branch change.

## Parent and reason for this experiment

Owner-private source: [cell-coherent-B.blend](https://drive.google.com/file/d/1tDM4Gf3qd01fmWAG95aIVCyoHfbXJh0G/view), exact SHA-256 `4732b465b103f9a0b4ab262dfeae51e26a8865aa586c3779d472d86eed845399`. Source itself was created from owned seed101 SDF + v20 fields on 264 original achenes, 150³ inherited color atlas and separate 192³ vascular R/H grids. This source is *already visually unaccepted* owing to uniform tiny-cell dimples.

Read earlier original [v14 tear review](https://github.com/Dmitry-dev-pet/strawberry-lab/blob/experiment/strawberry-v19-rooted-graph-20261123/experiments/sdf-exterior-2026-11-22/v14-nonperiodic-branching-and-torn-edge-review.md) and [v18 volume displacement review](https://github.com/Dmitry-dev-pet/strawberry-lab/blob/experiment/strawberry-v19-rooted-graph-20261123/experiments/sdf-exterior-2026-11-22/v18-native-3d-sdf-tissue-tear-review.md). Both previous experiments already tried normal displacement or SDF-field erosion, which did not yield convincing torn pulp. The present experiment tests **physical topological face extrusion** with newly formed side walls **on the same evaluated cut mesh**, not another normal bump, detached vessel curve or overlay film.

No commercial/GPL Frucht node trees, shaders, meshes, reference images or author video were copied. All new sizes and selection parameters are **ARTIST**, not measured strawberry histology.

## Precise original method

`build.py` opens the SHA-pinned owner source with Blender 5.2.4 and script autoexecution OFF. It adds 25 native GN nodes **after** existing cut-local SDF cell/coherence relief, with one controlled `sdf_torn_extrude_gain=0/1`. Only sphere-bite mode can activate the extrusion; WHOLE and both tested plane cuts pass through the source geometry exactly. The branch reads the **existing `sdf_rest_position` and `sdf_v20_halo`**, separates skin/material-index-2 cap with live evaluated geometry and calculates the actual cap-to-skin proximity. The candidate mask uses sparse independent 3D Noise with threshold **0.665**, scale **5**, within **2.7 mm** of the skin but at least **0.18 mm** from the seam, and vascular halo >0.08. `Extrude Mesh` in FACE mode (not individual faces) raises selected, mutually attached groups along the sampled cap normal by **0.62 mm**. The extrusion is not supposed to be anatomically accurate tissue damage.

- A: gain 0; no additional pulled-out faces; pre-existing cell-coherence B is preserved.
- B: gain 1; real connected extruded cap side-wall geometry.

Original body mesh, all 264 seed source objects, two packed atlases, cap shader, SSS, cameras, lights and cutter objects are **unchanged**. This was independently checked by `qa_provenance.py` (original raw source mesh, original packed 150³ and 192³ atlases and material-node count all byte-identical). The GN graph grows from 87 to 112 nodes.

## Actual Blender 5.2.4 QA and boundaries

`qa.py` independently reopens each saved scene without script execution. A and B each passed **7/7** evaluated poses: 0.32 mm WHOLE, plane, oblique plane, normal sphere and open-side sphere, plus 0.20 mm plane and open-side sphere. Every body has **exactly one connected component**, all edges manifold, positive signed volume and positive per-face area. On all seven A controls the evaluated vertex SHA-256 is **identical** to the archived owner-source cell-coherent B, not just equal in approximate shape. In both plane states and WHOLE, B coordinates equal A exactly.

At the original side bite, B gains **60 vertices and 60 faces at 0.32 mm**, or **80 vertices and 80 faces at 0.20 mm**, on the already evaluated closed SDF fruit mesh. The ordinary spherical bite gains 36 at 0.32 mm. The result is a connected edit of the existing body, **not a separately intersecting object**. `qa_live.py` independently verified gain `1→0→1` restores byte-identical evaluated geometry, moving the sphere recomputes the mesh, and plane mode remains unaffected. PR48 per-vertex live achene guard was retested with 264/130/114/202 visible seeds (whole/plane/oblique/side-bite) and **0 remaining seed vertices inside the cutter**. The latter is *not* an exhaustive triangle/triangle intersection proof.

**More aggressive physical-face extrusion is unsafe:**

- 3D Noise threshold 0.615, 0.82mm height, 3.3mm skin band: 3 non-manifold edges in the coarse 0.32mm side bite.
- Spaced macro 3D Voronoi centres (scale 5.0, 0.78mm height, 3.3mm skin band, 0.7mm seam exclusion): threshold 0.26 passed coarse (0 bad) but failed 0.20mm side bite (**1 non-manifold edge**); threshold 0.23 and 0.18 failed that fine pose (**2 non-manifold edges** each). Debugging confirms some edges have **four adjacent extruded faces**, i.e. stronger face masks are not topologically valid.

Do not present a non-manifold variant as a candidate merely because a lower-resolution mesh happens to pass. The small B result is validated only for the seven tested poses, not for arbitrary cutter motion or guaranteed absence of surface self-intersections.

## Original matched Blender Cycles and verdict

Fresh CPU Blender Cycles renders with identical cutter, camera, lights, color management and RNG seed 1729 **within each A/B pair**:

| Shot | Original render settings | A→B pixels >2/255 | A→B pixels >10/255 | Interpretation |
|---|---|---:|---:|---|
| Open-side sphere bite | 480×480, 16 samples | **0.2205%** | 0.1007% | Changes are barely visible at normal framing |
| Close bite camera | 320×320, 4 samples | **1.0117%** | 0.4033% | A few local bumps, NOT convincing torn wet pulp |

The reference author's video was inspected separately in prior studies (~18.5 seconds), but our camera/lighting/specimen are **not pixel aligned** with it. The material still shows a broad pale pith, fairly uniform red cell impressions and a smooth scooped cavity. **Visual target FAIL**. Image difference is not a quality metric. A high-resolution 640×16 close-up was attempted but did not finish in the bounded command; 320×4 is a diagnostic image, not high-fidelity validation. No ImageGen images are used as Blender evidence.

## Reproduction

Download owner-source `.blend` linked above and use Blender 5.2.4 LTS, disable autoexec. From a checkout of PR49, for instance:

```bash
BLENDER=/path/to/blender
ROOT=experiments/sdf-connected-torn-cap-2026-11-23
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/build.py" -- --source inputs/cell-coherent-B.blend --outdir build/torn-cap/scenes
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/qa.py" -- --scene build/torn-cap/scenes/torn-B.blend --out build/torn-cap/qa-B.json --poses whole plane oblique bite edge plane-fine edge-fine
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/qa_live.py" -- --scene build/torn-cap/scenes/torn-B.blend --out build/torn-cap/qa-live.json
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/qa_provenance.py" -- --source inputs/cell-coherent-B.blend --scene-dir build/torn-cap/scenes --out build/torn-cap/qa-prov.json
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/render.py" -- --scene build/torn-cap/scenes/torn-B.blend --shot bite --out build/torn-cap/bite-B-480.png --resolution 480 --samples 16
```

For seed QA, reuse the already-versioned PR49 [`experiments/sdf-v20-bridge-seed101-20261123/qa_seeds.py`](https://github.com/Dmitry-dev-pet/strawberry-lab/blob/experiment/sdf-rest-relief-20261123/experiments/sdf-v20-bridge-seed101-20261123/qa_seeds.py). Source hashes of saved `.blend` output can change with file paths/serialization, so independent evaluated geometry is the reproduction target. Builders refuse a wrong source SHA or overwriting output folders; QA refuses to overwrite report files.

## Private original evidence and disposition

[Owner-private Drive folder](https://drive.google.com/drive/folders/1o0ABKDPWXiGmmk3jX5crvj3NepAXIJmm), includes editable A/B saved Blender 5.2.4 scenes, original native Cycles PNGs, contact sheet, source, independent QA, negative trial report, SHA256 manifest and full ZIP. Assets are not public GitHub files.

**Decision:** preserve the topology experiment as *negative visual evidence* and do NOT copy it to the generator or merge it to `main`. Small connected extrusion is real but too inconspicuous; stronger versions are topologically invalid. The next actual major fidelity hypothesis should be a **region-aware multilayer tissue representation before/at isosurface construction**, not more random face extrusion or extra white lines, droplets or SSS gain. Retain one common rest-space domain and correct PR48 seed guard, and benchmark real Cycles against the owner reference; don't re-run the failed threshold sweep.
