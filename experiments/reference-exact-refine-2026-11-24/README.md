# Exact: cap-local adaptive refinement — 24 November 2026

Continuation of PR #50 from `eb0085ef635737edef9fd3d1985ad9e1c77115c2`. Original artistic implementation, not a reconstruction of the unavailable commercial Frucht node tree. Pinned source `exact-lumen.blend` SHA-256 `bbf897fd885725951e75e5ca4eda0301cbf38c0f1bd31a9f375f3d7ce58c72a8`; candidate `exact-refine.blend` SHA-256 `0868e656bc1d4c68c1a0f2b555bb5443f5f2527e34ca8bab0e55a1ae9d656e67`. Blender 5.2.4 LTS. The candidate was downloaded back from Drive and its complete bytes matched.

## Algorithm

Add two optional native geometry-node passes to the Exact body group, after skin/wall/cap classification and before existing pit sampling, outer edge-distance sampling, inverse-rest mapping and tissue-field evaluation. Selection: cap face; every vertex incident only to cap faces; current face area greater than `cap_refine_area_mm2` (default 0.03 mm², an experimental artistic setting). Each selected face is individually extruded with zero offset; its top is collapsed to its arithmetic vertex centre; merge-by-distance in Connected mode selects only the duplicated top vertices. The original face becomes a triangle fan with one new centre vertex. No existing edges are split; the collar incident to skin or cavity-wall faces is excluded. The second pass reevaluates face area and incidence. The existing rest-space vascular sampler and cell displacement then evaluate the new points. The original cavity and protrusion construction is unchanged. `cap_refine_level`: 0 (default, exact bypass), 1 or 2; `tissue_gain` remains off by default. Fast and whole display bypass are unchanged.

The first candidate used boolean-to-float domain conversion without explicitly storing intermediate float attributes. Independent QA correctly rejected it: 10,405 new points versus 9,785 eligible faces on the .32 plane, including collar faces. Although manifoldness was retained, the selection violated the intended criterion. The final candidate stores the face mask and pure-vertex mask explicitly as FLOAT named attributes on their native domains before evaluating selection. `rejected-plane-32.json` and the first builder are archived to preserve the negative result. An initial QA import-path failure was fixed separately.

## Actual evaluated geometry results

All six saved-scene states pass. Each cut evaluates both refinement levels, then level 2 with the existing tissue gain at one. Level zero equals the pinned Exact source (coordinates, connectivity, triangles, materials, sampled attributes). All existing vertices are retained at gain zero, every added vertex is a pure cap vertex, skin and cavity wall triangles and the cap/noncap edge sets are identical by coordinates. The expected count and independently calculated face centroids agree. No open, inconsistent, wire/over-two-face edges or degenerate render triangles. Connected-body and negative-cavity boundary counts are unchanged. All 831 retained seed contacts pass triangle BVH overlap, and skin and wall vertices remain fixed with relief. The field is independently sampled at 10,712 new-point observations: maximum absolute R/H/B error 7.69115e-5, max inverse-rest coordinate error 2.04359e-6 mm. Raw stock, anchor/vascular dependency keys, seed mesh, and Fast before/after checks pass. No exhaustive geometric or self-intersection proof.

| Pose | Voxel mm | Cap faces before -> level 2 | New vertices pass 1 + 2 | Total vertices before -> after | Gate |
|---|---:|---:|---:|---:|---|
| Whole (display bypass) | .20 | — | — | — | PASS |
| Plane | .20 | 26705 -> 103799 | 25698 + 0 | 106964 -> 132662 | PASS |
| Tilted, deformed | .20 | 40209 -> 93954 | 17915 + 0 | 123694 -> 141609 | PASS |
| Bite | .20 | 26430 -> 51375 | 8315 + 0 | 167798 -> 176113 | PASS |
| Plane | .32 | 10405 -> 39760 | 9785 + 0 | 41746 -> 51531 | PASS |
| Bite | .32 | 10318 -> 41022 | 9920 + 472 | 65422 -> 75814 | PASS |

The plane at .32 has median face area .1023999 -> .0256000 mm². In every tested cut no pure cap faces above the default area limit remain after level 2. The unchanged collar is explicitly excluded from that statement. A centroid fan does not shorten original edges, so the area criterion is not isotropic edge-length remeshing; it does not establish production-quality microcells. Nonplanar quads may acquire different interior triangulation. Two passes are a bounded option, not a guarantee for arbitrary thresholds or cutter poses. No calibrated materials, juice or visual parity claim; no speed benchmark.

`comparison.png` contains two newly rendered 700×700 Workbench frames with the same camera, SDF .32 mm and tissue_gain 1. On the right the finer tissue relief is visible, with the same outline and cavity. Grey clay remains deliberately diagnostic. The appearance is still not convincingly juicy fruit. The next research step can refine cellular appearance and add juice geometry on the independently evaluated, locally refined cut mesh; do not merge based only on technical gates.

## Reproduce

Use the pinned source scene from the previous lumen step and its exact-tissue `vascular-field.npz` (SHA-256 `0f6bbaa59a3a478c917a1c7bf69a41add5d9199f097c3ef8f0a2ebc984bb2c7e`). Place the unchanged `build_split.py` and `qa_split.py` from its evidence under `deps/`. The evidence archive includes both scripts. Fresh output paths required.

```sh
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_refine.py -- exact-lumen.blend exact-refine.blend
for spec in 'whole .20' 'plane .20' 'tilted .20' 'bite .20' 'plane .32' 'bite .32'; do
  set -- $spec
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_refine.py -- exact-lumen.blend exact-refine.blend vascular-field.npz "$1" "$2" "qa-$1-$2.json"
done
for level in 0 2; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_refine.py -- exact-refine.blend plane 1 "$level" .32 "plane-refine-$level.png"
done
```
