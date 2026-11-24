# Fast skin deletion — bounded reference-first negative control

24 November 2026. Continue draft PR50 from `0bf8c419b63269219ef27372c8fbe899fab2a693`. **Source-face preservation and unchanged flesh/seed checks PASS in six evaluated states; interface gate FAIL in all five cut states.** No main merge, no visual acceptance, no new material/tissue work. All modelling distances ARTIST. No Frucht source code, graph, preset or assets transferred.

## Reference and hypothesis

Reopened exact owner-private archive Frucht Free Kiwi 0.4.3 (SHA256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`), `schnitte.py:717–796`, especially 753–764 and 774–784. The default live deletion path samples the signed cutter SDF and deletes selected faces; no moving positions or creating exact intersections. The source permits separate raster resolution for skin and flesh (see `P` and calls at 755/1030), and also has alternate clip/snap paths. The previous actual Kiwi runtime audit confirms this distinction. The complete paid Strawberry scene is unavailable. This experiment uses the same cutter mesh, raster parameters and voxel driver for both paths to isolate the skin deletion rule, not the author's distinct numerical settings or a literal commercial recreation.

## Implementation

A = pinned owner scene `reference-flesh.blend` SHA256 `4cee7f472d5ebe8a9ee48b39f760ee87a5d16f3c1e2db0ee5aaffe4fcdcd0ff3` from the immediately preceding research. B = `fast-skin.blend`, SHA256 `c82d664a9c2e9873fd8415658e41c456569852dac23569c63246d770e383fd5e`. Blender 5.2.4 LTS cd5dc428cce1. Reuse our owned Graph helper from `reference-split-surface-2026-11-24/build_split.py` (Git blob `1fd07748a0bc668b81715d037e3ee5db8b6cad20`). Replace only the exact-clip skin modifier with an independently authored 16-node group. Sample cutter SDF (same actual cutter mesh, band width 3 and trilinear interpolation, same `flesh_voxel_mm` control; grid evaluations separate, not a shared persistent cached grid). Store diagnostic source face IDs and signed face-centre samples, delete faces with value < 0. Whole bypass. No new positional corrections. Existing tissue classification, recession, inverse rest, original stock and seed deletion unchanged. Saved whole. B remains a separate negative-control candidate.

## Independent QA

Six reopened A/B states: whole, plane, tilted/deformed, bite at .32 mm; tilted/deformed and bite at .20 mm. Exact seed and flesh coordinate/triangle hashes and tested named attributes agree in every state, including rest coordinates and pre-recess fields; whole skin matches exactly. All B skin vertex positions and their pit/rest attributes are exact members of the uncut source. All safe source vertices >.5 mm from cutter retained. B cut faces have exactly the original source indices and original vertex order. Independent in-memory routing of the full pre-delete stock yields exactly the retained face index set according to signed samples. In every cut, zero wrong labels in clearly signed analytic face-centre probes (|distance|>.05mm); maximum near-cutter difference <.011mm (sphere tessellation and raster approximation included). Each cut skin has one boundary component, no bad boundary valence, wire or over-two-face edges, inconsistent winding or degenerate triangles. This is deliberately open skin, not a watertight combined mesh. Retained seeds all have actual triangle overlap with the skin on each of the five cuts, but this is a contact check, not perfect seating/exposure.

| Pose / voxel mm | Rim max nearest cap mm A/B | B rim probes inside analytic cutter >.03mm | B rim probes >.10mm from cap |
|---|---:|---:|---:|
| Plane .32 | .061413 / .122373 | 532 | 21 |
| Tilted .32 | .153040 / .170312 | 481 | 91 |
| Bite .32 | .173745 / .214010 | 333 | 124 |
| Tilted .20 | .099999 / .180681 | 481 | 162 |
| Bite .20 | .099551 / .204813 | 317 | 134 |

Rim sampled at vertices and edge midpoints; nearest tagged cap actual Blender loop triangles. A and B have different rim sample sets, so these are maxima at their respective actual rims, not pointwise correspondence or measured gap width. Common A exact-clip rim probes also compared with B skin: 12/30/5/30/12 probes >.10mm in the above pose order. Candidate fails the declared diagnostic interface criterion (all rim probes within .10mm, none inside analytic cutter >.03mm, all common probes within .10mm, valid boundary valence). No continuous seal or self-intersection proof. No new full hull-aware gap-volume investigation: flesh is identical to the prior classification study and its limitations remain. Tilted skin and seed hashes identical between voxel resolutions; bite skin has six fewer retained faces at fine resolution; decreasing voxel size alone does not eliminate face-sized steps. No general claim about the unavailable commercial skin resolution, actual high-quality route or speed. Elapsed QA time includes both scenes and checks, not interactive evaluation benchmark.

## Visual evidence and decision

Two new actual 700² Workbench B renders (tilted, bite macro, .32mm), compared with SHA-verified prior reference-flesh B renders reused as A; matching camera, settings and source hashes checked. A not rerendered. Pixel differences >2/255: tilted .092%, bite .711%; >10/255: .015%, .334%. Difference detection, not quality. Bite close-up visibly has more staircase-like contour; existing irregular bright lip remains. No material comparison or photographic fidelity claim. **Do not promote the simple face-deletion candidate.** Keep the prior split exact-clip exterior for the Fast research control. This result does not prove that author's actual Fast has the same mismatch; the test uses our stock and matched grid settings. Do not repeat arbitrary rim shifts or threshold sweeps. Next distinguish reference's preview and Exact finalization architecture (source-body SDF branch, actual common-material boundary, then optional local smoothing before display separation). Identify the documented quality transition and independently test whether a shared connected boundary in a separate Exact output can support subsequent tissue modules without discarding the preserved Fast exterior. Do not assert full paid template behavior from free Kiwi. Previous integrated and reference-first control files unchanged; main unchanged.

## Reproduction

```
B=/path/to/blender
L=/path/to/this/experiment
S=/path/to/reference-split-surface-2026-11-24
A=/path/to/reference-flesh.blend
D=/path/to/fresh/output
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_fast_skin.py" -- "$A" "$S/build_split.py" "$D/fast-skin.blend"
for spec in 'whole .32' 'plane .32' 'tilted .32' 'bite .32' 'tilted .20' 'bite .20'; do
 set -- $spec
 "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_fast_skin.py" -- "$A" "$D/fast-skin.blend" "$S/qa_split.py" "$1" "$2" "$D/qa-$1-$2.json"
done
for pose in tilted bite; do
 "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_fast_skin.py" -- "$D/fast-skin.blend" "$S/qa_split.py" "$pose" "$D/$pose-B.png"
done
```

The renderer is the previous owned matched-view renderer, reused unchanged (Git blob `66dcf2e39e76283f50ca227d6ce7898384d11a62`). EGL warnings in logs, both actual PNGs written and inspected. Fresh output paths required; binary serialization may depend on paths. Original reference archive needed only to audit source. Private Drive stores scene and evidence, GitHub original source and compact reports only.
