# Split surface interface and rest coordinates — 24 November 2026

Research continuation of Draft PR50 at `d8aeb44352a1c52e3cd4fb724cac1f9b2993df66`. **Inverse rest-coordinate transport PASS for tested poses. Near-rim correction improves sampled proximity, but full interface/visual acceptance NOT met.** No main merge. No vessels, cells, cavity, juice, new skin geometry or production material. All new distances ARTIST, not anatomical measurements.

## Reference and bounded design

Reopened the owner-provided Frucht Free Kiwi 0.4.3 ZIP (SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`). Shared code `schnitte.py:1027–1128` combines a named flesh grid with outer/cavity reference geometry, stores outer distance, classifies using cutter SDF, and recesses outer flesh under skin. `schnitte.py:1180–1199` applies a separate reverse rest map to strawberry flesh in the relevant live path; `formen.py:724–763` defines that attribute modifier. The full commercial strawberry graph remains unavailable. The current implementation is our own approximation of separate-surface registration, NOT the author's exact seam algorithm. No source code, nodes, assets or numeric settings from Frucht included.

Input is our immutable split scene `6c614f51d9879589d8c57efbf1cb48cbd3dffb7d96b273d5c14e6c2ecdd6f839`. Verify owned `build_split.py` Git blob `1fd07748a0bc668b81715d037e3ee5db8b6cad20`. Join the already deformed source envelope mesh into the named grid source geometry (one new node); retain existing flesh cutter and recession. Add one 62-node native modifier on visible flesh. The original skin and achene paths are untouched. Optional bounded local correction samples nearest original envelope and actual cutter normals; computes signed normal distance to envelope, projects correction into cutter tangent plane, targets +0.035 mm local overlap, clamps signed offset to ±0.20 mm and tapers over envelope distance .10–.60 mm and cutter distance .06–.38 mm. This is a position correction, not a topological weld, not guaranteed to resolve thin/near-tangent intersections. Existing cap face classification remains unchanged. No new signed cutter-grid classification or cavity-wall path in this experiment.

The same modifier stores `sl_rest_position` (analytic inverse of the existing common-gaussian-map-v1 at the final physical surface), `sl_edge_distance_mm` (unsigned distance to original deformed hull, not geodesic distance to rim), `sl_reference_position`, `sl_reference_normal` (pre-cell surface), and `sl_interface_offset_mm` (signed applied scalar before movement). No independently randomized tissue coordinate. Saved `interface.blend` SHA-256 `b46cc7492e3b42a5125147564c2aaabe42cd4e713e3c66c0de54ba43c32ab8e9`, Blender 5.2.4 LTS cd5dc428cce1. Default `interface_gain=0` on the existing controller; gain 1 enables the experimental correction. Inverse rest and other attributes computed for both gains. Original integrated research control SHA-256 `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215` rechecked unchanged.

## Observed independent QA

Four reopened baseline poses, then eight gain/pose states in saved candidate: whole, plane, tilted with changed shape, bite, all at .32 mm. Coordinates, triangle connectivity and tested source attributes of skin and seed meshes exactly match original in every candidate. Gain 0 also reproduces original flesh coordinates and triangles exactly. Gain 1 preserves polygon vertex indices but render triangulation changes with moved vertices (expected for nonplanar quads). All cut flesh meshes remain closed with consistent winding, positive signed volume and zero degenerate triangles. Whole has no visible flesh. Gain 1 max displacement plane .196653, tilted .198860, bite .199056 mm. All six nonempty candidate states: every rest coordinate independently verified with NumPy inverse, maximum component error 2.044e-6 mm; reference positions equal evaluated coordinates, unit normal length within floating-point tolerance; 1024 vertex-distance checks per cut state (6144 total) against BVH of actual original loop triangles agree to reported precision. This verifies coordinate transport, not a new anatomical field, full shape-domain proof, or exact inverse of the commercial generator.

| Pose | Rim samples | Max nearest cap mm A → B | Rim signed outside >.03 mm A → B | +.05 mm kept-side probes outside >.03 A → B | +.15 mm kept-side probes outside >.03 A → B |
|---|---:|---:|---:|---:|---:|
| Plane | 2592 | .062457 → .062900 | 64 → 0 | 0 → 0 | 0 → 0 |
| Tilted | 2556 | .147851 → .084360 | 585 → 75 | 324 → 5 | 303 → 330 |
| Bite | 1548 | .173745 → .089288 | 490 → 30 | 336 → 10 | 326 → 585 |

All 6696 rim vertex/midpoint samples per candidate across the three cuts are within .10 mm of a tagged cap triangle at gain 1. This is local unsigned distance. Signed nearest-normal probes use the closed flesh boundary: positive means outward relative to the nearest triangle, negative inward. These are **approximate sign probes**, not an exact point-in-solid proof or continuous gap-volume measurement. The .05/.15 mm probes move along the retained-side analytic cutter normal, and are not filtered by containment in the original hull; therefore positive values at displaced probes need not be actual physical gaps. Nonetheless the worsened deep-probe counts and remaining near-rim outward excursions preclude claiming complete contact. Sampled outer flesh away from cutter (>1.5 mm) has no >.03 mm outward excursions in A or B. Near cutter, >.10 mm outward excursions relative to original hull decrease 140→57 (plane), 125→62 (tilted), 68→42 (bite), but do not vanish. No rigorous self-intersection, complete seam seal, new fine voxel, arbitrary cutter or shape envelope QA. Minimum analytic cutter margin on evaluated flesh is about -.10 mm before and after correction; this is existing remesh error, not exact cutter clipping. Preserve this negative evidence.

Initial import error corrected in QA only. Initial edge-distance mismatch came from BVH construction on quads versus Blender's actual loop triangulation; switching reference BVH to exact evaluated triangles gives matching distances at the original threshold. Initial equality assertion on render triangles for displaced quads was inappropriate; corrected to polygon connectivity equality for gain 1, retaining exact triangle equality for gain 0. Logs of all three failures retained. No geometry changes or gate threshold relaxation after original candidate build.

Four actual matched Workbench frames (700², .32 mm), two poses × gains, same respective camera and settings. Tilted difference >2/255 affects .998% pixels, bite macro 3.817%; >10/255 .366% and 1.729%. These are image differences, not visual quality scores. Tilted cut fringe locally improved; bite still has conspicuous faceted fringe. **Do not promote correction to default or merge on numerical proximity alone.** Keep coordinate transport as validated interface prerequisite. Next isolate the exterior-cap classification/edge treatment from the existing SDF cutter error, guided by reference `schnitte.py` and `gliederung.py`; no repeated arbitrary gain tuning. Before tissues: verify signed gap/overlap with hull-aware probes and coherent cap provenance. No visual parity or scientific calibration.

## Reproduction

Use exact previous split scene and original helper files from `experiments/reference-split-surface-2026-11-24/`, fresh output paths. 4 CPU threads, autoexec disabled. Logs include complete process RSS and QA time (not pure interactivity benchmark).

```sh
B=/path/to/blender
L=/path/to/this/experiment
S=/path/to/previous/split/experiment
D=/path/to/new/output
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_interface.py" -- "$S/split.blend" "$S/build_split.py" "$D/interface.blend"
for pose in whole plane tilted bite; do
 /usr/bin/time -v "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_interface.py" -- "$S/split.blend" "$D/interface.blend" "$pose" .32 "$S/qa_split.py" "$D/qa-$pose.json"
done
for pose in tilted bite; do
 for gain in 0 1; do
  "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_interface.py" -- "$D/interface.blend" "$S/qa_split.py" "$pose" "$gain" "$D/$pose-$gain.png"
 done
done
```

Private Drive stores saved scene, evidence archive and comparison; repository stores original experiment code and receipts. Binary serialization may depend on save path. No reference media/assets in this deliverable.
