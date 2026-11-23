# Strawberry Lab — bounded central tissue color distribution A/B (2026-11-23)

**Result: shader-only engineering PASS, visual fidelity FAIL.** Research added to the existing stacked draft PR #49 (dependent on draft PR #48). **Do not merge this cosmetic intervention to main.**

## Prior work checked (no repeated research claim)

We reviewed previous experiments **v9** (pale spindle enlarged: rejected), **v19** (separate pith B and bundle ring in a different older v12 scene: geometry PASS / visual fail), **v14** (seed-linked branch field plus rim noise: bite still cup-like), **v18** (volume-field tissue tear: crumpled result), and **v20/v21** (narrow vascular core/wide cell-suppressing halo, color-outline path specific to an older material). This experiment does **not** re-implement any of these as a claimed new structural discovery. Its narrower test is current **seed101 v20-bridge scene's legacy 150³ color sampling**, which was not addressed by the old v19 B-channel edit.

## Actual scene and one-factor intervention

Source: owner-private editable PR49 v20-bridge `v20-bridge-portable.blend`, SHA-256 `0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2`.

`build_pith.py` modifies **only** the input to the existing cap-color `Separate XYZ` node (which ultimately drives the source RGB 150³ image samplers): a local 3D rest-space XY remapping scaled up to 1.55× near the central axis, smoothly faded out by radius 0.38 Blender units. The source image bytes, original 192³ vascular fields/Geometry Nodes, skin, 264 achenes, cutter, tissue microtexture Voronoi paths and all source geometry are unchanged. Cap `sdf_rest_position` persists; three shader microtexture nodes still sample **unwarped** coordinates.

A and B are identical saved Blender node graphs and source scenes, with exactly one driver-backed control different: `sdf_pith_color_compact_gain`: **A=0 (original sampled color)**, **B=1 (local radial re-sample)**. The conversion from scene units to physical mm is unchanged. This is an **ARTIST spatial color manipulation**, not a true narrowed anatomical pith or measured organ geometry.

## Independent tests

- Blender **5.2.4 LTS**, Linux CPU, scripts disabled on saved-scene reopen: **5/5 matched geometry states** at the tested voxel size / pose combinations: 0.32 mm whole, planar, open-edge sphere; 0.20 mm planar and open-edge sphere. A and B have **identical evaluated vertex-coordinate SHA, original mesh SHA and source 150³ packed atlas SHA**, zero nonmanifold edges and positive signed volume.
- Genuine Cycles matched two shots (plane and open-side bite), each A and B separately rendered at **640×640, 16 samples, seed 1729**, identical camera, lights, cutter and color management. A image pixels are **exactly identical to the previously signed baseline v20-bridge halo renders** for both shots (maximum byte channel difference **0**).
- A vs B: plane **11.59%** pixels change by more than 2/255 in at least one RGB channel, **8.11%** by more than 10/255; open-side bite **7.09%** and **3.57%**. These numbers measure a difference, **not perceptual realism**.
- Initial sequential 640px B rendering hung under a bounded command; a clean isolated rerun completed (~15.5s on plane). The final two B PNGs were produced and verified. Do not claim a Blender crash root cause or performance benchmark.

## Visual verdict

The pale central streak is somewhat narrower at the planar cut, but top-center white blur remains substantial, and the open spherical bite still looks like a smooth scooped bowl. A slight improvement on one region **does not pass owner/Frucht visual acceptance**. It demonstrates that the present color atlas contributes materially to the broad pale center, but also that color remapping alone cannot deliver the missing attached torn tissue structure.

**Stop this parameter sweep.** Next meaningful isolated mechanism is an *actual* coherent branching tissue / torn-edge **geometry** experiment grounded in pre-existing v14/v18 negatives and v20 source fields, not additional pith brightness/radius tweaks, and must be compared to the owner-provided 10s and 18–20s Frucht reference with explicit non-matched camera caveat.

## Reproduction (all source is original project code)

```bash
B=/path/to/blender  # tested 5.2.4
SRC=inputs/v20-bridge-portable.blend  # SHA256 pinned in build_pith.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-pith-color-2026-11-23/build_pith.py -- --source "$SRC" --outdir build/pith-ab
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-pith-color-2026-11-23/qa_pith.py -- build/pith-ab/pith-color-A.blend build/pith-ab/pith-color-B.blend build/pith-ab/qa.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python experiments/sdf-pith-color-2026-11-23/render_pith.py -- --scene build/pith-ab/pith-color-B.blend --shot plane --out build/pith-ab/plane-B.png --resolution 640 --samples 16
```

Do not overwrite existing files. Blender binary SHA may vary by serialization; validate reopened evaluated geometry and actual Cycles receipts. None of the copyrighted Frucht frames/source are included in this package or public GitHub.
