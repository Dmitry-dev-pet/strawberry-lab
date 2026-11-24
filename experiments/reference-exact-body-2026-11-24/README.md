# Reference-first Exact common-body route — 24 November 2026

Continuation of draft PR50 from `d51239a77290a52c801df46d750a206ee57d1b4d`. Independent original implementation on the neutral-stock/split-surface branch. **Fast roundtrip and common material boundary established; zero-isovalue Exact planar tests PASS, zero-isovalue spherical bite topology FAIL. Not visual acceptance or a production Exact implementation.** No new material, vascular field, cells, cavity, juice, finalization or smoothing. No Frucht source, node trees, assets or presets copied. All model dimensions not independently measured remain ARTIST. Main and earlier scenes unchanged.

## Reference mechanism and actual implementation

Use prior verified `reference-exact-transition-2026-11-24/README.md`: the original free Kiwi runtime switches back from separately displayed Fast skin/flesh to its original body graph; source fragments for Strawberry `HAT_Z1` insert an SDF difference before original body's GridToMesh and filter a common material-labelled body (`schnitte.py:217–251,277–282`, `gliederung.py:299–390,540–551`). The complete commercial graph is unavailable. This experiment reproduces the **architecture principle**, not the author's exact geometry algorithm or runtime. Original reference is not executed again here.

Pinned `reference-flesh.blend` SHA256 `4cee7f472d5ebe8a9ee48b39f760ee87a5d16f3c1e2db0ee5aaffe4fcdcd0ff3`, owned helper `build_split.py` Git blob `1fd07748a0bc668b81715d037e3ee5db8b6cad20`, `qa_split.py` blob `dbe96d08499190d1b196091054fc4ab5a3030b3b`. Previously integrated control SHA256 `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215` rechecked. Actual Blender 5.2.4 LTS cd5dc428cce1, runtime archive SHA256 `2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86`, CPU, 4 requested threads.

- Native Exact object shares the neutral skin source mesh datablock and original common forward shape modifier. A 35-node group independently converts the deformed source into an SDF, subtracts the same actual routed cutter mesh and extracts **one** body. Face labels determined by dominance of operands of max(body SDF, -cutter SDF) at face-centre samples; both signed values are stored. The skin and cap materials already existed. No stitching, no arbitrary rim displacement. Transfer original pit mask (nearest source surface; cap interior is not skin provenance). Store distance to the uncut SDF reference. Reuse previously verified inverse rest-position and pre-cell reference position/normal group unchanged.
- `exact_mode` (0 Fast, 1 Exact) and `exact_voxel_mm` (default .20; bounded experimental UI) on existing controller. Exact only replaces display geometry on cuts. Whole always returns original uncut skin. Native routing suppresses the Fast skin and flesh meshes in Exact and vice versa. Existing seed guard and cutter transforms unchanged. Saved whole/Fast, scripts disabled on reopen. No persistent-bake or performance guarantee. Finalize not implemented.
- Initial `exact.blend` (SHA256 `102ed16fa3c0d6fc3669a61f71fb2880044a1effdefd716cf703396b4a123eed`) used Blender's inherited GridToMesh default threshold **+0.1 model units (mm)** for both Exact extraction and reference. This caused a roughly .1 mm systematic offset of exterior/cap. Verified actual defaults by opening the saved scene. Corrected builder explicitly sets both Exact thresholds to **0.0**, the signed distance zero surface. `exact-zero.blend` SHA256 `36f9ff4a5de1f1d222548d3c827a87df209624d55949643d9ff61449a1460cd6`. Both saved variants preserved. Fast deliberately untouched, including its inherited cut GridToMesh threshold +.1 and uncut reference threshold 0; this observation suggests a separately controlled future audit, not a claim that every previous pit/edge defect has the same cause. `build_exact_default.py` preserves initial builder.

## Observed independent QA

Each pose reopens actual control and candidate, scripts disabled, checks coordinate/triangle/attribute hashes of Fast before and after Exact, original stock coordinates, shared source and anchor digest, seed indices/counts and signed cutter guard. All 10 tested state receipts (five per candidate) retain Fast hashes and seed geometry exactly. Whole always bypasses Exact. Four nonempty cut states per candidate: actual common mesh incidence, rest inverse, pre-cell positions, signed operand/material correspondence, independently sampled clear cap/outer regions, and reference distances checked. Independent sample uses actual loop triangles. Worst inverse error across corrected tests 2.434e-6 mm; 16,384 reference distance samples match to reported precision in corrected cut states. No incorrect labels in sampled clear regions. Near-cutter signed samples agree with analytic plane/sphere to stated tolerance; sphere tessellation and discretization remain. All retained seed solids complete; all actual triangle BVH contacts with Exact skin present in every tested pose. A contact check does not prove ideal exposure or absence of seed penetration. Pit probes only on retained anchors >2 mm from cutter, using transformed source normals; signed depth relative to nominal anchor, not complete pit cross-section.

| Pose / voxel | Default +.1 body verts / shared edges | Zero body verts / shared edges | Zero median pit depth loss | Zero common boundary gate |
|---|---:|---:|---:|---|
| Plane .20 | 107066 / 806 | 104974 / 800 | .6011% | PASS |
| Tilted .20 | 125644 / 1006 | 123634 / 1010 | .8178% | PASS |
| Bite .20 | 163930 / 564 | 161780 / 574 | 1.3438% | FAIL |
| Plane .32 | 41816 / 504 | 40770 / 502 | 6.6978% | PASS |
| Whole .20 | original 157250 | original 157250 | n/a | bypass PASS |

Default candidate .20 plane, tilted, bite all single closed component with one shared material loop, no boundary/wire/over-two-face or inconsistent edges, zero triangles below 1e-9 mm²; contacts 130,117,227 of the retained seed sets. But default median pit-depth loss 30.204%,32.302%,31.313%; min analytic cutter margin about -.1 mm plane/tilted and -.110 mm bite. Corrected plane and tilted at .20 (and plane .32) preserve topology and contact. Corrected .20 bite has zero boundary/winding errors but **two connected components (161772 and 8 vertices), two triangles of area 3.638e-12 mm² at face 109365 near [6,-1,30] mm, two shared-material edge components**. Gate FAIL; no cleanup, shifted cutter, threshold workaround, or relaxed acceptance. Corrected sphere min analytic cutter margin -.010022 mm; cap median abs error .005932 mm, local mixed-label transition can be farther from ideal cutter (max .171 mm). Plane minimum margin approximately zero, but material boundary is not mathematically coincident with cutter in all transition cells. No exhaustive global self-intersection or general cutter/pose proof. Do not promote this to an accepted product. For plane .20 median depth original .333391 mm, default .232693, zero .331387; .32 zero median .311061. Demonstrated improvement comes from correct isovalue, not a new artistic offset.

First QA failed because evaluated mesh was accessed after dependency graph reroute. Fixed validator to capture arrays before reroute, not geometry. Initial zero-bite strict assertion failed; preserved log. Validator then reports component sizes, exact degenerate details and explicit false topology/common-boundary gate while continuing other diagnostics. It does not redefine a failure as PASS. Earlier receipts used the same original topology assertions; only the last three receipts include the new diagnostic fields. Full logs/evidence in archive. Timings include scene loading, multiple evaluations and QA; not pure interactive latency. Peak RSS in tested QA <= about 2.4 GiB. No new .16 mm sweep or claims of exact CAD clipping.

## Visual evidence and decision

Four fresh actual Blender Workbench diagnostic images 700², matched per-pose camera/light/resolution, same corrected saved scene, Fast .32 vs Exact .20. Tilted and bite macro. Image hash and settings checks, image difference >2/255: 1.2941% tilted, 12.2176% bite. Difference detection, not perceptual quality. Bright split-surface lip is reduced in common-body Exact, with remaining jagged material boundary. Bite is explicitly marked topology FAIL on comparison. These are clay diagnostic renders, not Cycles or Frucht parity. Last bite render timed out in batch; fresh isolated retry produced PNG/receipt. EGL warnings present despite successful image output. Preserve both candidate scenes and all negative evidence. Next narrowly diagnose zero-level degeneracy/stray component at sphere intersection and decide a geometry-valid treatment, without returning to arbitrary offsets; revisit Fast's inherited isovalue separately. After common-boundary gate passes, attach tissue modules. No main merge.

## Reproduction

Use exact prior `reference-flesh.blend` and existing split helper files, fresh output paths, absolute paths, scripts disabled. Both builders have identical shape/stock/route logic; only explicit isovalue settings differ. The final QA script records failures instead of terminating early for topology, so inspect `common_boundary_gate` and `seed_contact_gate`; process exit success is not overall acceptance.

```sh
B=/path/to/blender
L=/path/to/this/experiment
S=/path/to/experiments/reference-split-surface-2026-11-24
A=/path/to/reference-flesh.blend
D=/path/to/fresh/output
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_exact_default.py" -- "$A" "$S/build_split.py" "$D/exact.blend"
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_exact.py" -- "$A" "$S/build_split.py" "$D/exact-zero.blend"
for variant in exact exact-zero; do
 for spec in 'whole .20' 'plane .20' 'tilted .20' 'bite .20' 'plane .32'; do
  set -- $spec
  "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_exact.py" -- "$A" "$D/$variant.blend" "$S/qa_split.py" "$1" "$2" "$D/qa-$variant-$1-$2.json"
 done
done
for pose in tilted bite; do
 for quality in 0 1; do
  "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_exact.py" -- "$D/exact-zero.blend" "$S/qa_split.py" "$pose" "$quality" .20 "$D/$pose-$quality.png"
 done
done
```

Saved Blender binary serialization may depend on path. Both candidate .blend files separately on owner Drive; ZIP holds original source, compact receipts, diagnostic PNGs and logs; no third-party assets. Manifest pins both scenes and all evidence. Public repository only original source and compact evidence.
