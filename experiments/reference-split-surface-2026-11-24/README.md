# Independent split skin/flesh prototype — 24 November 2026

Research continuation of Draft PR50 at `3219936eae3cd3c0eb0fa394b2bdbb4cdacf054c`. **Exterior preservation and separate closed flesh PASS at the sampled states; seam proximity gate FAIL for two coarse poses. NOT a proven watertight joined mesh or visual acceptance.** No production-material, cell, juice, vessel, cavity or crown changes. No commercial Frucht assets, original GPL code/nodes, numerical presets or reference media copied. All uncalibrated model values ARTIST.

## Reference and hypothesis

Read the previously verified owner-private Frucht Free 0.4.3 source archive (SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`), especially `schnitte.py:607–649,721–796,970–1024,1027–1128`; compare `experiments/reference-dependency-map-2026-11-24/README.md` and prior executed Kiwi runtime. The available shared source contains alternative exterior paths, including clean original-mesh clipping with a cap-removal tag and approximate cutter-field deletion/snap. Its independent flesh path uses a named SDF grid and recesses non-cut outer tissue under the skin. This is evidence for the principle, not access to the paid strawberry graph or proof that any particular alternative is its default. Our native prototype uses independently authored material-marker clipping, cutter-distance classification and a smooth recession field. It does not reproduce the exact reference node tree.

## Actual implementation and scope

Input: immutable `stock264.blend` SHA-256 `d430ac081f5383148e4f6a6a81f0dfc89fdfc5e8fb7538dd76cf97598398026a` from `experiments/reference-neutral-stock-2026-11-24`. Old integrated research control SHA-256 `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215` was rechecked and unchanged. Native Blender 5.2.4 LTS `cd5dc428cce1`, CPU, 4 threads, saved scenes opened with scripts disabled.

- Whole state keeps the original 157,250-vertex pitted skin. The native common forward shape map still runs first. For a cut, a native Manifold Mesh Boolean clips the original solid skin mesh, after which only the generated cutter-material faces are deleted. The remaining skin is intentionally open at the rim; it is not passed through SDF. No custom cap triangulator or perturbation of the cutter.
- Separate hidden flesh source copies the original neutral mesh and shares its forward shape map. The derived volume uses `Mesh to SDF Grid` and a named volume (`sl_flesh_volume`). The visible flesh independently reads it, subtracts the same routed cutter SDF and produces a closed mesh. No claim of persistent bake, actual cache hit, or verified re-evaluation avoidance. The outer flesh is smoothly recessed under skin away from the cutter. Cut faces are classified by distance to the actual cutter. The raw neutral stock, anchor digest, and pitted vertex buffers remain unchanged.
- One editable cutter router selects a large box (plane cut) or UV sphere. Both skin and flesh use its actual evaluated mesh. Seed culling uses all real seed vertices and stable anchor indices; any seed with a vertex inside the corresponding analytic plane/sphere (plus 0.04 mm margin) is removed in its entirety. This analytic guard is bounded to the configured box as a half-space and the uniformly scaled sphere, not arbitrary custom cutters, nonuniform sphere scaling or exhaustive collision handling. The plane box must continue to enclose the relevant half-space. The retained seed solids are not clipped into partial pieces.
- Saved `split.blend` SHA-256 `6c614f51d9879589d8c57efbf1cb48cbd3dffb7d96b273d5c14e6c2ecdd6f839`. Controller `SL Shape Controller | edit Custom Properties`: `split_mode` 0 whole/1 plane/2 sphere, `flesh_voxel_mm` default 0.32, `flesh_recess_mm` default 0.20, existing common shape settings. Cutters `SL Split | plane box` and `SL Split | sphere bite` are hidden editable source objects (unhide to manipulate). Saved state is whole. No new production materials; diagnostic clay only. Existing rest coordinates remain on source skin; inverse rest coordinates on remeshed flesh have NOT yet been implemented, so do not attach vascular/cell/juice fields yet.

## Observed independent QA

All 6 saved-scene states: whole/plane/tilted-and-deformed/bite at 0.32 mm, tilted-and-deformed/bite at 0.20 mm. All retained original skin vertices farther than 0.5 mm from the analytic cutter were found with **exact float coordinates** and identical pit-mask value. The complete evaluated skin and seed coordinates and pit-mask SHA agree across the two voxel sizes for both tested matched cut poses. Skin has a single intended boundary loop on each cut, no invalid boundary valence, wire/over-two-face edges, inconsistent two-face winding or degenerate triangles. Whole has no boundary. Flesh on every cut is closed, consistently oriented, positive signed volume, no degenerate triangles. Whole emits no visible flesh. Open-skin signed volume is not a closed-solid measurement and is not used as a pass gate. All retained seed IDs have the complete original vertex count. Vertex margins positive on every tested cut; sphere closest triangle distance from analytic sphere centre exceeds radius by 0.202751 mm in both bite tests. No exhaustive global self-intersection, arbitrary-cutter, all-shape, seed/skin exposure or seed-seed QA.

| Pose / voxel mm | Exact safe skin vertices | Flesh vertices | Retained seeds | Max rim→cap nearest distance mm | Total QA elapsed s | Peak process RSS KiB |
|---|---:|---:|---:|---:|---:|---:|
| Whole / .32 | 157250/157250 | 0 | 264 | n/a | 2.92 | 665356 |
| Plane / .32 | 71277/71277 | 41816 | 130 | .062457 | 4.00 | 986020 |
| Tilted / .32 | 56981/56981 | 48966 | 117 | .147851 | 4.47 | 1055368 |
| Bite / .32 | 144734/144734 | 63872 | 227 | .173745 | 3.65 | 813540 |
| Tilted / .20 | 56981/56981 | 125644 | 117 | .099887 | 7.40 | 1693580 |
| Bite / .20 | 144734/144734 | 163930 | 227 | .098070 | 5.18 | 875284 |

QA time includes original reference evaluation, mesh reads, topology/seed/rim/outer flesh probes; not a pure interactive update benchmark. RSS includes the complete Blender process. No speed comparison against author. For cut states, rim vertices and edge midpoints were compared against nearest triangles of faces tagged cut tissue (2592 plane, 2556 tilted, 1548 bite). At .32 mm tilted/bite have 32/33 samples over the diagnostic 0.10 mm threshold; at .20 both have zero. This is unsigned distance, not gap/overlap sign or a proof of continuous sealed seam. No cap protrusion/seam closure guarantee. Across all cuts the sampled outer flesh away from cutter (>1.5 mm) had no outward normal-projected deviations >0.03 mm (8000+ samples each). Whole/plane/tilted/bite diagnostic Workbench images 700² share camera and lighting. The untextured images show a bright/irregular fringe near the rim, especially on the bite; no visual acceptance. The two narrower fine-grid peak gaps do not establish a universal .20 mm solution. The source exterior can now remain unchanged when increasing only the flesh resolution. Earlier raw full-body SDF exterior pit-loss results are a different model, not a matched A/B of this new neutral stock.

Initial validator import and empty material-slot errors are archived. Fixed only QA import path and handling of empty material slots; no geometry changed. Final QA was rerun with additional coordinate/seed completeness receipts. The initial QA reports are kept in the private archive. All 6 states pass the stated geometry sub-gates; the seam criterion remains partial FAIL at .32. Next: characterize and register the skin/flesh interface (including signed gap/overlap and edge provenance) and transport the common inverse rest map to flesh; avoid unrelated material/vascular work until that contract is established. Preserve both current and previous control scenes. No main merge.

## Reproduction

```sh
B=/path/to/blender
L=/path/to/this/experiment
N=/path/to/stock264.blend
D=/path/to/new/output-directory
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_split.py" -- "$N" "$D/split.blend"
for pose in whole plane tilted bite; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_split.py" -- "$D/split.blend" "$pose" "$D/qa-$pose.json" .32
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_split.py" -- "$D/split.blend" "$pose" "$D/$pose.png" .32
done
for pose in tilted bite; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_split.py" -- "$D/split.blend" "$pose" "$D/qa-$pose-fine.json" .20
done
```

Use fresh paths. For exact process RSS use `/usr/bin/time -v`. Binary serialization may depend on file path; validate evaluated mesh results rather than assuming identical binary hashes on rebuild. Private Drive stores scene, diagnostic frames and archive; public GitHub stores only original source and compact evidence.
