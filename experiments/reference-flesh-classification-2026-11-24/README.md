# Reference-consistent flesh classification and pre-recess edge field

24 November 2026. Continuation of draft PR50 at `fe5f562c0ef6373b7284ff243b5b28ff5c923c54`. **Technical provenance/coordinate/closed-flesh checks PASS at the sampled poses; interface gate FAIL.** No main merge or visual acceptance. No new cells, vessels, juice, cavity, skin, crown, materials or cutter tuning. No Frucht code, graph, assets or numerical presets transferred. All modelling distances remain ARTIST.

## Source-grounded mechanism

Reopened exact owner-provided Frucht Free Kiwi 0.4.3 archive SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`, `schnitte.py:985–1024,1027–1128`. As independently established in `reference-edge-audit-2026-11-24`, shared code exposes an uncut outer SDF isosurface beside the named volume, samples the signed cutter grid, stores reference distance before recessing the exterior tissue, and moves only the eligible exterior vertices. The paid Strawberry template is unavailable. We retain our independent exact exterior clip as a control, not a demonstrated default of author Strawberry Fast. The earlier source/runtime audit showed that original Kiwi Fast has a different exterior deletion path. No commercial implementation or parameters copied.

## Implementation

Pinned previous `interface.blend` SHA-256 `b46cc7492e3b42a5125147564c2aaabe42cd4e713e3c66c0de54ba43c32ab8e9`, with its optional tangential correction off. Saved `reference-flesh.blend` SHA-256 `4cee7f472d5ebe8a9ee48b39f760ee87a5d16f3c1e2db0ee5aaffe4fcdcd0ff3`. Blender 5.2.4 LTS build `cd5dc428cce1`, CPU, 4 requested threads, scripts disabled.

- The source group exposes the zero isosurface of the same uncut named grid, instead of joining the original dense skin. No change to the volume subtraction or common shape map. No persistent bake/cache hit demonstrated.
- Preserve the previous threshold width (.8 voxel) for signed cutter sample classification; eligible exterior = NOT cut AND reference-surface distance < one voxel. These are independent experimental choices, not author coefficients. Keep existing recession magnitude .20 mm, replace smooth unsigned-distance ramp with explicit eligible-point normal recession. The existing clay cut/outer face materials are used; the point mask is explicitly adapted to the face domain before movement. This is a compound change to classification, reference and recession policy, not proof of an isolated cause of any visual change.
- Store `sl_pre_recess_position`, `sl_pre_recess_normal`, `sl_cutter_signed_mm`, `sl_edge_distance_mm` (before movement), `sl_cut_point`, `sl_outer_recess_point`. No subsequent overwrite of the edge field. Remove the old optional tangential registration, preserve the exact analytic inverse from the previous modifier; `sl_rest_position` and final `sl_reference_position`/`sl_reference_normal` still describe the final pre-cell geometry. Group sizes 7/40/31. Skin/seed groups and source mesh untouched.
- Candidate saved whole. This independent scene is not promoted to a new accepted baseline. Keep previous interface and integrated control.

## Independent observed checks

Six matched A/B poses: whole/plane/tilted with deformation/bite at .32 mm; tilted/bite at .20 mm. In all six, evaluated skin and seed coordinates, triangle connectivity and tested original attributes match control exactly. All five closed flesh meshes have zero invalid/wire/nonmanifold/boundary edges, inconsistent winding and degenerate triangles; positive volume. Whole emits no visible flesh. Pre-recess coordinates match independent control with recession set to zero exactly; polygon topology unchanged. All 108,945 cut-classified vertices across the five nonempty states stayed exactly fixed; all moved vertices satisfy the stored normal-offset equation within 1.908e-6 mm. Max inverse error 2.256e-6 mm; 20,480 sampled pre-recess reference distances match actual triangle BVH exactly at reported precision. Near cutter, independently computed analytic plane/sphere signed distances differ from sampled grid by at most .010334 mm (includes faceted sphere and discretization), within .25 voxel in tested narrow band. This is not an independent reconstruction of every grid voxel. All clearly exterior face probes and available clear-cap probes show zero wrong labels for both variants; label differences arise in the remaining transition region. No physical correctness claim for every ambiguous face. At .20 mm the original .4-voxel clear-cap diagnostic selects no faces because of the existing cutter-grid offset: report not applicable (null), and report a second .75-voxel interior-cap band separately. Initial failed import, node-label lookup and empty fine diagnostic logs retained; no candidate geometry changed after final builder. Coarse records predate the added wide-band diagnostic, and use the original valid .4-voxel probe. A/B both calculated in fresh Blender processes; no generalized self-intersection, arbitrary cutter, shape-range or new seed-contact tests.

| Pose / voxel mm | Max rim→cap triangle distance A/B mm | Rim samples >.10 mm A/B | Eligible .05/.15 mm interior probes outside flesh >.03 mm A/B |
|---|---:|---:|---:|
| Plane .32 | .061413 / .061413 | 0 / 0 | 0 / 0; 0 / 0 |
| Tilted .32 | .153040 / .153040 | 31 / 33 | 0 / 8; 0 / 8 |
| Bite .32 | .170570 / .173745 | 34 / 36 | 0 / 0; 0 / 0 |
| Tilted .20 | .099999 / .099999 | 0 / 0 | 0 / 1; 0 / 12 |
| Bite .20 | .099551 / .099551 | 0 / 0 | 0 / 1; 0 / 1 |

Rim distances use actual Blender loop triangles (the older report's quad-BVH distances are not an exact matched numerical comparator). Rim vertices and edge midpoints. Displaced probes follow retained-side analytic cutter normals, require two ray-parity directions agreeing on inside the original hull, >=.005 mm distance from its boundary and positive cutter margin. On evaluated flesh, two ray directions must agree that a point is outside and nearest triangle distance must exceed .03 mm to count. Ambiguous/near-boundary probes reported separately, including numerous excluded hull points and small eligible bite sample counts (23 / 36); not continuous gap-volume or watertight joined proof. Sampled outer flesh away from cutter (>1.5 mm) has no outward nearest-normal excursions >.03 mm. Candidate introduces some genuine sampled interior-point gaps under the stated probe conditions. Exact rim proximity fails for the two coarse curved/tilted poses. The inherited analytic cutter margin remains imperfect. Do not infer physical seal from no boundary edges in separate tissue.

## Actual images and decision

Four new original 700x700 Workbench diagnostic renders, matched A/B tilted and bite at .32 mm. Same respective camera, lighting and material settings, verified per-frame receipts. Tilted changes .4792% of pixels >2/255, bite 4.7408%; difference detection, not a quality score. Bite's pale lip is locally thinner, but jagged rim persists. Tilted looks nearly unchanged. **Interface/visual gate FAIL**. Accept as evidence of reference-coordinate contract and a negative control for the combined recession change; do not replace the previous scene. The actual author's Fast skin face-deletion path has not been tested on our model in this experiment. Next compare that bounded alternative using the same signed cutter grid and flesh reference, with identical cutter, shape and resolution. Explicitly check retained exterior coordinates, gaps/overlap and cap provenance. No repeated arbitrary gain or threshold sweep, no forced global weld. Preserve source-aligned coordinate contract before attaching interior tissue modules.

## Reproduction

Use the pinned prior interface scene, original `build_split.py` and `qa_split.py` from `experiments/reference-split-surface-2026-11-24`, absolute paths and fresh output paths. No author assets required to rebuild our experiment. Original archive needed only to recheck source evidence.

```sh
B=/path/to/blender
L=/path/to/this/experiment
S=/path/to/previous/split/experiment
A=/path/to/interface.blend
D=/path/to/fresh/output
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_reference_flesh.py" -- "$A" "$S/build_split.py" "$D/reference-flesh.blend"
for spec in 'whole .32' 'plane .32' 'tilted .32' 'bite .32' 'tilted .20' 'bite .20'; do
  set -- $spec
  "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_reference_flesh.py" -- "$A" "$D/reference-flesh.blend" "$S/qa_split.py" "$1" "$2" "$D/qa-$1-$2.json"
done
for pose in tilted bite; do
  "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_reference_flesh.py" -- "$A" "$S/qa_split.py" "$pose" "$D/$pose-A.png"
  "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_reference_flesh.py" -- "$D/reference-flesh.blend" "$S/qa_split.py" "$pose" "$D/$pose-B.png"
done
python "$L/compare.py" "$D"
```

Binary serialization may depend on paths. Archive receipts reflect the actual run names; rerun the final validator on coarse poses to obtain the added wide-band statistics if needed. Private Drive stores binary and rendered evidence; GitHub only original code and compact reports. No reference footage or original node assets included.
