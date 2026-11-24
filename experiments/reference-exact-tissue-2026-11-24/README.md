# Exact: rebuilt neutral-stock vascular field and coupled cap relief — 24 November 2026

Draft PR50 continuation from `e95c2152defdf8f38cf039b07a9e9700bcf8936b`. **Six matched technical states PASS; visual acceptance pending.** No main merge, production materials, cavity, juice, cap refinement or Finalize. All uncalibrated dimensions and cell settings ARTIST. No author source, node trees, commercial geometry, numeric presets or assets copied.

## Source and implementation

Reopened the exact private Frucht Free Kiwi 0.4.3 ZIP `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`: `leitbuendel.py:19–144,301–336` establishes neutral evaluated seed targets, tapered carriers/terminals and spatial core/halo/ring field; `zellen.py:73–182` uses shared spatial coordinates and vascular atlas, separates cap faces and protects the open rim. Commercial Strawberry blend unavailable. Our implementation is independent and is NOT a claim to reproduce the author graph. In particular the author has adaptive cap-local subdivision; this experiment uses the existing common Exact mesh without refinement or separate cap geometry.

Pinned source scene `exact-phase.blend` SHA256 `2e31a68dba83e689b55b5599a7f2a13a34a9f3fb08dd09b4eff055c31c108224`; same verified Blender 5.2.4 LTS build cd5dc428cce1. Prior original ring algorithm (Git blob 14af1776a31c7afe393866e625391f17598e399d), owned sampler from SHA256 `a43df0a7d38404193af313ba5faca60a1ba00ad6db6de855d54135b050a202eb` bridge archive (Git blob 6d691d6bf1a95679b947d6eaa4bcd25406049c3a), split builder/validator blobs `1fd07748a0bc668b81715d037e3ee5db8b6cad20`, `dbe96d08499190d1b196091054fc4ab5a3030b3b`. Actual neutral-stock receipt `stock264.json` SHA256 `23beb6082f419148578ed556cc8dee0b83799b83f499df6453b161d9bb79bde6`. Raw skin, seed, anchor and seat buffers verified against the receipt; all 264 IDs and seat positions correspond. Recomputed actual neutral seed centre from each saved seat transform, compared against mesh centroid (max difference 0.024977 mm), then reused previous owned ring path parameters and inward target offset. No reuse of previous field pixels or previous anchor layout.

- 28 longitudinal carriers, 264 tapered terminals, exact attachment to carrier samples; no common axial trunk. 19,976 sampled path points, all inside original neutral pitted skin by nearest outward-normal probe, min signed sampled margin 0.579715 mm. Repeated deterministic graph construction exact. This is a discrete centreline check, not containment of entire Gaussian support, proof of histology, or proof for every deformed pose.
- Three 192^3 fields: narrow core R, broad halo H, nominal ring-relative B. Max Gaussian stamps using owned prior ring implementation, halo >= core, all finite. Both widths use 192^3 (not author's multiresolution halo), 34,072 stamps per field. B is relative to the nominal elliptical ring; no claim that it includes every angular modulation. Pack into Non-Color floating 3072×2304 image, sample via native two-slice interpolation extended from owned sampler. Single dependency key `d90800f97bc7e131d33436726013ec693f4b3f5e181c9adf95dd615a561b92ea` includes anchor digest, actual seed centre digest, stock key, coordinate map version, raster bounds/resolution and algorithm/settings. Key provenance only: no live rebuilding on arbitrary editing of stock mesh/count. 264-count experiment only.
- One original 59-node modifier and 50-node sampling group on Exact body only. Sample all channels at stored `sl_rest_position` in mm. Explicit face-domain cap flag converted to point float average; move only vertices whose incident faces are ALL cut faces. Rest/reference attributes remain pre-relief. Existing smooth-centre 3D noise-warped Voronoi, old owned settings converted to millimetres; retain .145-mm dome, halo suppression from 1 to .12, .12R+.045H ridge and smooth fade over pre-existing edge distance. No change to mesh connectivity, no new refinement. `tissue_gain` 0 (default) exposes field attrs without moving geometry; 1 applies coupled diagnostic relief. Existing Fast, seed guard, common forward/inverse map and zero/half-phase Exact unchanged. Saved whole/Fast. `exact-tissue.blend` SHA256 `95b40e781ee948f9496ba5277ac08be0bb305435de1b498031b51c669be1b5c2`. New field NPZ SHA256 `0f6bbaa59a3a478c917a1c7bf69a41add5d9199f097c3ef8f0a2ebc984bb2c7e`. Graph SHA256 `e739fcc9f1ff2871108757cebaf323c13c64516797a77cd68a6e640366bd9fcc`.

## Independent saved scene QA

| Pose / voxel mm | Body vertices | Shared rim vertices fixed | Seed contacts | Max relief mm | Gate |
|---|---:|---:|---:|---:|---|
| whole 0.20 | whole bypass | — | unchanged | 0.000000 | PASS |
| plane 0.20 | 105340 | 802 | 130/130 | 0.147982 | PASS |
| tilted 0.20 | 123638 | 1010 | 117/117 | 0.148066 | PASS |
| bite 0.20 | 161756 | 580 | 227/227 | 0.148008 | PASS |
| plane 0.32 | 41128 | 496 | 130/130 | 0.147938 | PASS |
| bite 0.32 | 63108 | 360 | 227/227 | 0.147936 | PASS |

Every pose independently reopened prior and candidate scenes, scripts disabled. Actual gain=0 Exact coords, triangles, polygon connectivity and all tested old attrs identical to old Exact; Fast geometry and tested attrs equal before and after, seed coordinates and attributes unchanged, source raw mesh/digest unchanged. Gain=1 independently reconstructed cap/skin adjacency from polygons, confirmed exact cap selection and zero skin or shared-rim displacement. Polygon connectivity retained; quad triangulation may change under displacement. All five cut meshes closed, no invalid/wire/over-two-face/inconsistent edges, zero triangles <1e-9 mm², positive volume. Total 831/831 retained seed/skin triangle contacts, not ideal seating. 3,248 shared boundary vertices fixed across five sampled cuts. Same stored volume used for deformed and neutral states. 20,480 independently sampled neutral locations compared on all three channels with NumPy trilinear; max absolute error 6.89137143e-05. Recomputed smootherstep suppression, edge fade, ridge, height and displacement equation from recorded fields; max component displacement equation error 1.91479921e-06 mm. No exhaustive self-intersection, arbitrary pose, shape-domain, cutter-excursion or biological validation. Raised cut relief deliberately departs from the ideal cutter surface; this is not a machining accuracy test. Initial validator import failure fixed only in Python search path; retained log. Whole bypass checks unchanged geometry, not an internal whole-body rendering. Original phase and Fast control scene hashes rechecked. The saved default remains relief disabled, not a replacement accepted scene.

## Images and decision

Two actual matched Workbench renders 700², direct longitudinal cut, .20 mm, same camera and light, gains 0 and 1. Image difference >2/255 26.225% (>10/255 7.274%); difference detection only. New relief reveals carrier/terminal network, but coarse, textile-like grain persists, no physical wet appearance, no full tissue material or central lumen. No visual fidelity acceptance. EGL warnings present despite successful PNG output. Only plane rendered; tilt and bite have numerical QA, not new renders. Next source-grounded work: examine cavity/attached tissue geometry and cap-local adaptive refinement separately, then juice and optical materials; no repeat arbitrary pigment sweeps or mesh-wide subdivision. Keep prior controls.

## Reproduce

With Blender 5.2.4, original phase scene and archived owned dependencies under `deps/`, fresh paths:

```sh
B=/path/to/blender
L=/path/to/experiment
A=/path/to/exact-phase.blend
D=/path/to/fresh/output
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_tissue.py" -- "$A" "$L/deps/stock264.json" "$D/exact-tissue.blend"
for spec in 'whole .20' 'plane .20' 'tilted .20' 'bite .20' 'plane .32' 'bite .32'; do
 set -- $spec
 $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_tissue.py" -- "$A" "$D/exact-tissue.blend" "$D/vascular-field.npz" "$1" "$2" "$D/qa-$1-$2.json"
done
for gain in 0 1; do
 $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_tissue.py" -- "$D/exact-tissue.blend" plane "$gain" "$D/plane-$gain.png"
done
```

Archive includes source, receipts, graph, logs, frames, pinned owned helper files and stock receipt; numerical NPZ and .blend stored separately on owner Drive. No author asset redistribution. Binary serialization may differ on rebuild. Verify actual geometry results, not file timestamp. QA times include multiple scene evaluations, not interactive speed.
